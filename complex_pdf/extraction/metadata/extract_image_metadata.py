"""Image metadata extraction using LLM vision to analyze images and diagrams."""

import json
import logging
import re
from pathlib import Path

from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.core.utils import encode_image_to_data_uri, read_text_file
from complex_pdf.extraction.prompts.image_metadata import (
    GENERATE_IMAGE_METADATA_PROMPT,
)
from complex_pdf.extraction.schemas import ImageMetadataResponse

logger = logging.getLogger(__name__)


def enhance_content_elements_with_image_metadata(context_metadata: dict) -> dict:
    """
    Enhance figure entries in content_elements with detailed image metadata.

    Args:
        context_metadata: Context metadata dictionary

    Returns:
        Enhanced context metadata with updated content_elements
    """
    if (
        "image_metadata" not in context_metadata
        or not context_metadata["image_metadata"]
    ):
        return context_metadata

    if "content_elements" not in context_metadata:
        return context_metadata

    # Create a mapping of image_id to image_metadata
    image_metadata_map = {}
    for img_meta in context_metadata["image_metadata"]:
        image_id = img_meta.get("image_id", "")
        image_metadata_map[image_id] = img_meta

    # Enhance figure entries in content_elements
    for element in context_metadata["content_elements"]:
        if element.get("type") != "figure":
            continue

        element_id = element.get("element_id", "")

        # Try to match: figure-N-X or image-N-X with image-N-X
        # Extract page number and index from element_id
        match = re.match(r"(?:figure|image)-(\d+)-(\d+)", element_id)
        if not match:
            continue

        page_num, index = match.groups()
        # Try both figure-N-X and image-N-X formats
        possible_image_ids = [
            f"image-{page_num}-{index}",
            f"figure-{page_num}-{index}",
        ]

        matched_image_meta = None
        for possible_id in possible_image_ids:
            if possible_id in image_metadata_map:
                matched_image_meta = image_metadata_map[possible_id]
                break

        if not matched_image_meta:
            continue

        # Enhance the element with image metadata
        # Add image_type
        element["image_type"] = matched_image_meta.get("image_type", "")

        # Add natural_description
        element["natural_description"] = matched_image_meta.get(
            "natural_description", ""
        )

        # Enhance existing fields if image_metadata has better/more detailed versions
        if matched_image_meta.get("title"):
            element["title"] = matched_image_meta["title"]
        if matched_image_meta.get("summary"):
            element["summary"] = matched_image_meta["summary"]

        # Merge keywords (combine unique keywords)
        existing_keywords = set(element.get("keywords", []))
        new_keywords = set(matched_image_meta.get("keywords", []))
        element["keywords"] = list(existing_keywords.union(new_keywords))

        # Merge entities (combine unique entities)
        existing_entities = set(element.get("entities", []))
        new_entities = set(matched_image_meta.get("entities", []))
        element["entities"] = list(existing_entities.union(new_entities))

        # Add additional fields from image_metadata
        if matched_image_meta.get("dates"):
            element["dates"] = matched_image_meta["dates"]
        if matched_image_meta.get("locations"):
            element["locations"] = matched_image_meta["locations"]
        if matched_image_meta.get("model_name"):
            element["model_name"] = matched_image_meta["model_name"]
        if matched_image_meta.get("component_type"):
            element["component_type"] = matched_image_meta["component_type"]
        if matched_image_meta.get("model_applicability"):
            element["model_applicability"] = matched_image_meta["model_applicability"]
        if matched_image_meta.get("application_context"):
            element["application_context"] = matched_image_meta["application_context"]

        # Add related_tables if present
        if matched_image_meta.get("related_tables"):
            element["related_tables"] = matched_image_meta["related_tables"]

        logger.debug(
            f"Enhanced content element {element_id} with image metadata from {matched_image_meta.get('image_id')}"
        )

    return context_metadata


def generate_image_metadata(
    litellm_client: LitellmClient,
    image_path: Path,
    page_text_path: Path = None,
) -> dict:
    """
    Generate metadata for an image/diagram by visually analyzing it.

    Args:
        litellm_client: LLM client for vision analysis
        image_path: Path to the image PNG file
        page_text_path: Optional path to page text file for context

    Returns:
        Dictionary containing image metadata

    Raises:
        FileNotFoundError: If image_path doesn't exist
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Encode image to data URI
    image_data_uri = encode_image_to_data_uri(image_path)

    # Read page text for context if provided
    page_text = ""
    if page_text_path and page_text_path.exists():
        try:
            page_text = read_text_file(page_text_path)
        except Exception as e:
            logger.warning(f"Could not read page text from {page_text_path}: {e}")

    # Format prompt with page text
    prompt = GENERATE_IMAGE_METADATA_PROMPT.format(
        page_text=page_text if page_text else "No page text available."
    )

    # Send to LLM with vision
    response = litellm_client.chat(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_uri}},
                ],
            },
        ],
        response_format=ImageMetadataResponse,
        temperature=0.0,  # Use deterministic output
        call_type="image_metadata",
    )

    # Extract metadata from response
    metadata_resp_string = response.choices[0].message.content
    metadata_resp_json = json.loads(metadata_resp_string)
    return metadata_resp_json


def process_all_images(
    scratch_path: Path, litellm_client: LitellmClient, max_pages: int = None
) -> dict:
    """
    Process all images to generate their metadata.

    Args:
        scratch_path: Base path to processed PDF directory
        litellm_client: LLM client for vision analysis
        max_pages: Maximum number of pages to process (None = all pages)

    Returns:
        Dictionary with processing results:
        - status: "success" or "error"
        - images_processed: Number of images successfully processed
        - images_failed: Number of images that failed
        - total_images: Total number of images found
    """
    logger.info(f"Processing image metadata in {scratch_path}...")

    # Find all page directories
    page_dirs = []
    for item in scratch_path.iterdir():
        if item.is_dir() and item.name.startswith("page_"):
            page_dirs.append(item)

    # Sort by page number
    page_dirs.sort(key=lambda x: int(x.name.split("_")[1]))

    # Limit to max_pages if specified
    if max_pages is not None:
        page_dirs = page_dirs[:max_pages]
        logger.info(
            f"Found {len(page_dirs)} page directories (limited to first {max_pages} pages)"
        )
    else:
        logger.info(f"Found {len(page_dirs)} page directories")

    total_images = 0
    images_processed = 0
    images_failed = 0

    for page_dir in page_dirs:
        page_number = page_dir.name.split("_")[1]

        # Check if this page has figures
        context_file = page_dir / f"context_metadata_page_{page_number}.json"
        basic_file = page_dir / f"metadata_page_{page_number}.json"

        if not context_file.exists() or not basic_file.exists():
            logger.debug(f"Skipping page {page_number} - missing metadata files")
            continue

        # Read context metadata to check if has_figures is true
        try:
            with open(context_file, "r") as f:
                context_metadata = json.load(f)
        except Exception as e:
            logger.warning(
                f"Could not read context metadata for page {page_number}: {e}"
            )
            continue

        if not context_metadata.get("has_figures", False):
            continue

        logger.info(f"Processing images for page {page_number}...")

        # Get image files
        images_dir = page_dir / "images"
        if not images_dir.exists():
            logger.debug(f"  No images directory found for page {page_number}")
            continue

        image_files = list(images_dir.glob("image-*.png"))
        if not image_files:
            logger.debug(f"  No image PNG files found for page {page_number}")
            continue

        # Get page text for context
        text_dir = page_dir / "text"
        page_text_path = None
        if text_dir.exists():
            page_text_file = text_dir / f"page_{page_number}_text.txt"
            if page_text_file.exists():
                page_text_path = page_text_file

        # Process each image
        image_metadata_list = []
        for image_file in sorted(image_files):
            image_name = image_file.stem  # e.g., "image-25-1"
            total_images += 1

            try:
                logger.info(f"  Processing {image_name}...")

                # Generate image metadata
                image_metadata = generate_image_metadata(
                    litellm_client, image_file, page_text_path
                )

                # Add image identifier
                image_metadata["image_id"] = image_name
                image_metadata["image_file"] = str(image_file.name)

                image_metadata_list.append(image_metadata)
                logger.info(f"    ✓ Generated metadata for {image_name}")
                images_processed += 1

            except Exception as e:
                logger.error(f"    ✗ Error processing {image_name}: {e}", exc_info=True)
                images_failed += 1

        # Add image metadata to context metadata
        if image_metadata_list:
            context_metadata["image_metadata"] = image_metadata_list

            # Enhance content_elements with detailed image metadata
            context_metadata = enhance_content_elements_with_image_metadata(
                context_metadata
            )

            # Save enhanced context metadata
            with open(context_file, "w") as f:
                json.dump(context_metadata, f, indent=2)

            logger.info(
                f"  ✓ Added {len(image_metadata_list)} image(s) to context metadata and enhanced content_elements"
            )
        else:
            logger.info(f"  No image metadata generated for page {page_number}")

    logger.info(
        f"✅ Image metadata extraction complete! "
        f"Processed: {images_processed}, Failed: {images_failed}, Total: {total_images}"
    )

    return {
        "status": "success" if images_failed == 0 else "partial",
        "images_processed": images_processed,
        "images_failed": images_failed,
        "total_images": total_images,
    }


if __name__ == "__main__":
    # Example usage
    from complex_pdf.core.llm.litellm_client import LitellmClient

    scratch_path = Path("output/short_complex_manual")
    litellm_client = LitellmClient(model_name="openai/gpt-4o")

    results = process_all_images(scratch_path, litellm_client)
    print(f"Results: {results}")
