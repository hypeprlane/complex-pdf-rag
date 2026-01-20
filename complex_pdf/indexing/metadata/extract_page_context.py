from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.core.utils import (
    encode_image_to_data_uri,
    read_json_file,
    read_text_file,
)
from complex_pdf.indexing.metadata.extract_page_metadata_with_context import (
    extract_metadata_from_page_with_response,
)


@dataclass
class PageData:
    """Data structure for a single page's information"""

    page_number: int
    image_path: Path
    image_data_uri: str
    metadata_path: Path
    metadata_content: str
    text_path: Path
    text_content: str


@dataclass
class PageContext:
    """Data structure containing n-1, n, and n+1 page information"""

    previous_page: Optional[PageData]
    current_page: PageData
    next_page: Optional[PageData]


def get_page_context(page_number: int, pdf_base_path: Path) -> PageContext:
    """
    Get the context for a specific page including n-1, n, and n+1 pages.

    Args:
        page_number: The target page number
        pdf_base_path: Base path to the processed PDF directory (e.g., scratch/service_manual_long/)

    Returns:
        PageContext containing data for previous, current, and next pages

    Raises:
        FileNotFoundError: If the current page doesn't exist
        ValueError: If page_number is less than 1
    """
    if page_number < 1:
        raise ValueError("Page number must be at least 1")

    # Current page paths
    current_page_dir = pdf_base_path / f"page_{page_number}"
    current_image_path = current_page_dir / f"page_{page_number}_full.png"
    current_metadata_path = current_page_dir / f"metadata_page_{page_number}.json"
    current_text_path = current_page_dir / "text" / f"page_{page_number}_text.txt"

    # Verify current page exists
    if not current_page_dir.exists():
        raise FileNotFoundError(
            f"Page {page_number} directory not found at {current_page_dir}"
        )

    # Load current page data
    current_page = PageData(
        page_number=page_number,
        image_path=current_image_path,
        image_data_uri=encode_image_to_data_uri(current_image_path),
        metadata_path=current_metadata_path,
        metadata_content=str(read_json_file(current_metadata_path))
        if current_metadata_path.exists()
        else "{}",
        text_path=current_text_path,
        text_content=str(read_text_file(current_text_path))
        if current_text_path.exists()
        else "",
    )

    # Previous page (n-1)
    previous_page = None
    if page_number > 1:
        prev_page_dir = pdf_base_path / f"page_{page_number - 1}"
        if prev_page_dir.exists():
            prev_image_path = prev_page_dir / f"page_{page_number - 1}_full.png"
            prev_metadata_path = prev_page_dir / f"metadata_page_{page_number - 1}.json"
            prev_text_path = prev_page_dir / "text" / f"page_{page_number - 1}_text.txt"

            previous_page = PageData(
                page_number=page_number - 1,
                image_path=prev_image_path,
                image_data_uri=encode_image_to_data_uri(prev_image_path),
                metadata_path=prev_metadata_path,
                metadata_content=str(read_json_file(prev_metadata_path))
                if prev_metadata_path.exists()
                else "{}",
                text_path=prev_text_path,
                text_content=str(read_text_file(prev_text_path))
                if prev_text_path.exists()
                else "",
            )

    # Next page (n+1)
    next_page = None
    next_page_dir = pdf_base_path / f"page_{page_number + 1}"
    if next_page_dir.exists():
        next_image_path = next_page_dir / f"page_{page_number + 1}_full.png"
        next_metadata_path = next_page_dir / f"metadata_page_{page_number + 1}.json"
        next_text_path = next_page_dir / "text" / f"page_{page_number + 1}_text.txt"

        next_page = PageData(
            page_number=page_number + 1,
            image_path=next_image_path,
            image_data_uri=encode_image_to_data_uri(next_image_path),
            metadata_path=next_metadata_path,
            metadata_content=str(read_json_file(next_metadata_path))
            if next_metadata_path.exists()
            else "{}",
            text_path=next_text_path,
            text_content=str(read_text_file(next_text_path))
            if next_text_path.exists()
            else "",
        )

    return PageContext(
        previous_page=previous_page, current_page=current_page, next_page=next_page
    )


def extract_metadata_with_context(
    litellm_client: LitellmClient,
    page_number: int,
    pdf_base_path: Path,
) -> str:
    """
    Extract metadata for a specific page using its context (n-1, n, n+1).

    This is a convenience function that combines get_page_context() with
    extract_metadata_from_page() to provide a simpler interface.

    Args:
        litellm_client: LitellmClient instance
        page_number: The target page number
        pdf_base_path: Base path to the processed PDF directory

    Returns:
        Extracted metadata as a string

    Raises:
        FileNotFoundError: If the current page doesn't exist
        ValueError: If page_number is less than 1
    """
    context = get_page_context(page_number, pdf_base_path)

    # Handle missing context pages gracefully
    if not context.previous_page or not context.next_page:
        # Create a simplified context with empty data for missing pages
        if not context.previous_page:
            # Create dummy previous page data
            prev_page_dir = pdf_base_path / f"page_{page_number - 1}"
            context.previous_page = PageData(
                page_number=page_number - 1,
                image_path=prev_page_dir / f"page_{page_number - 1}_full.png",
                image_data_uri="",
                metadata_path=prev_page_dir / f"metadata_page_{page_number - 1}.json",
                metadata_content="{}",
                text_path=prev_page_dir / "text" / f"page_{page_number - 1}_text.txt",
                text_content="",
            )

        if not context.next_page:
            # Create dummy next page data
            next_page_dir = pdf_base_path / f"page_{page_number + 1}"
            context.next_page = PageData(
                page_number=page_number + 1,
                image_path=next_page_dir / f"page_{page_number + 1}_full.png",
                image_data_uri="",
                metadata_path=next_page_dir / f"metadata_page_{page_number + 1}.json",
                metadata_content="{}",
                text_path=next_page_dir / "text" / f"page_{page_number + 1}_text.txt",
                text_content="",
            )

    return extract_metadata_from_page_with_response(
        litellm_client=litellm_client,
        image_path_n=str(context.current_page.image_path),
        image_path_n_1=str(context.previous_page.image_path),
        image_path_n_plus_1=str(context.next_page.image_path),
        metadata_page_n_1_path=str(context.previous_page.metadata_path),
        metadata_page_n_path=str(context.current_page.metadata_path),
        metadata_page_n_plus_1_path=str(context.next_page.metadata_path),
        page_n_1_text_path=str(context.previous_page.text_path),
        page_n_text_path=str(context.current_page.text_path),
        page_n_plus_1_text_path=str(context.next_page.text_path),
    )


def save_context_metadata(
    page_number: int,
    pdf_base_path: Path,
    metadata_content: str,
) -> Path:
    """
    Save context metadata to the proper location in the page directory structure.

    Args:
        page_number: The target page number
        pdf_base_path: Base path to the processed PDF directory
        metadata_content: The metadata content to save

    Returns:
        Path to the saved context metadata file

    Raises:
        FileNotFoundError: If the page directory doesn't exist
    """
    page_dir = pdf_base_path / f"page_{page_number}"
    if not page_dir.exists():
        raise FileNotFoundError(f"Page directory not found: {page_dir}")

    # Clean the JSON string
    clean_json_str = (
        metadata_content.strip().removeprefix("```json").removesuffix("```").strip()
    )

    # Parse to validate JSON
    parsed_data = json.loads(clean_json_str)

    # Save to context metadata file
    context_metadata_path = page_dir / f"context_metadata_page_{page_number}.json"
    with open(context_metadata_path, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=2)

    return context_metadata_path


def extract_and_save_context_metadata(
    litellm_client: LitellmClient,
    page_number: int,
    pdf_base_path: Path,
) -> Path:
    """
    Extract metadata with context and save it to the proper location.

    This is a convenience function that combines extract_metadata_with_context()
    with save_context_metadata() to provide a complete workflow.

    Args:
        litellm_client: LitellmClient instance
        page_number: The target page number
        pdf_base_path: Base path to the processed PDF directory

    Returns:
        Path to the saved context metadata file

    Raises:
        FileNotFoundError: If the current page doesn't exist
        ValueError: If page_number is less than 1 or if context pages are missing
    """
    response = extract_metadata_with_context(litellm_client, page_number, pdf_base_path)
    metadata_content = response.choices[0].message.content

    return save_context_metadata(page_number, pdf_base_path, metadata_content)


if __name__ == "__main__":
    import json

    import fitz

    # Example usage
    pdf_path = Path(
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/data/service_manual_long.pdf"
    )

    pdf_base_path = Path(
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long"
    )

    with fitz.open(pdf_path) as pdf_doc:
        total_pages = pdf_doc.page_count

    litellm_client = LitellmClient(model_name="openai/gpt-4o")

    for page_number in range(275, 565):
        # Extract and save context metadata for page
        context_metadata_path = extract_and_save_context_metadata(
            litellm_client, page_number, pdf_base_path
        )
        print(f"✅ Context metadata saved to: {context_metadata_path}")

    # Get cost information using LiteLLM's completion_cost function
    # Note: We need to get the response again for cost calculation
    # response = extract_metadata_with_context(litellm_client, 148, pdf_base_path)
    # cost = completion_cost(completion_response=response)
    # print(f"💰 API Call Cost: ${cost:.6f}")

    # # Get token usage information
    # if hasattr(response, "usage"):
    #     usage = response.usage
    #     print("📊 Token Usage:")
    #     print(f"   Prompt tokens: {getattr(usage, 'prompt_tokens', 'N/A')}")
    #     print(f"   Completion tokens: {getattr(usage, 'completion_tokens', 'N/A')}")
    #     print(f"   Total tokens: {getattr(usage, 'total_tokens', 'N/A')}")

    # # Alternative: Get cost from response._hidden_params if available
    # if (
    #     hasattr(response, "_hidden_params")
    #     and "response_cost" in response._hidden_params
    # ):
    #     hidden_cost = response._hidden_params["response_cost"]
    #     print(f"💰 Hidden Cost: ${hidden_cost:.6f}")
