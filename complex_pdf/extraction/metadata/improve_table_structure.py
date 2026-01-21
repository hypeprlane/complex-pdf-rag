"""Table structure improvement using LLM vision to correct HTML structure."""

import logging
from pathlib import Path

from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.core.utils import encode_image_to_data_uri
from complex_pdf.extraction.prompts.improve_table_structure import (
    IMPROVE_TABLE_STRUCTURE_PROMPT,
)

logger = logging.getLogger(__name__)


def improve_table_structure(
    litellm_client: LitellmClient, html_content: str, table_image_path: Path
) -> str:
    """
    Improve table HTML structure by visually analyzing the table image.

    Args:
        litellm_client: LLM client for vision analysis
        html_content: Current HTML table content
        table_image_path: Path to the table image PNG file

    Returns:
        Corrected HTML table string

    Raises:
        FileNotFoundError: If table_image_path doesn't exist
    """
    if not table_image_path.exists():
        raise FileNotFoundError(f"Table image not found: {table_image_path}")

    # Encode image to data URI
    image_data_uri = encode_image_to_data_uri(table_image_path)

    # Format prompt with HTML content
    prompt = IMPROVE_TABLE_STRUCTURE_PROMPT.format(html_content=html_content)

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
        temperature=0.0,  # Use deterministic output for structure correction
        call_type="improve_table_structure",
    )

    # Extract corrected HTML from response
    corrected_html = response.choices[0].message.content.strip()

    # Clean up any markdown code blocks if present
    if corrected_html.startswith("```html"):
        corrected_html = corrected_html[7:]
    elif corrected_html.startswith("```"):
        corrected_html = corrected_html[3:]

    if corrected_html.endswith("```"):
        corrected_html = corrected_html[:-3]

    corrected_html = corrected_html.strip()

    return corrected_html


def process_all_tables_structure(
    scratch_path: Path, litellm_client: LitellmClient, max_pages: int = None
) -> dict:
    """
    Process all tables to improve their HTML structure.

    Args:
        scratch_path: Base path to processed PDF directory
        litellm_client: LLM client for vision analysis

    Returns:
        Dictionary with processing results:
        - status: "success" or "error"
        - tables_processed: Number of tables successfully improved
        - tables_failed: Number of tables that failed
        - total_tables: Total number of tables found
    """
    logger.info(f"Processing table structures in {scratch_path}...")

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

    total_tables = 0
    tables_processed = 0
    tables_failed = 0

    for page_dir in page_dirs:
        page_number = page_dir.name.split("_")[1]

        # Get table files
        tables_dir = page_dir / "tables"
        if not tables_dir.exists():
            continue

        table_files = list(tables_dir.glob("table-*.html"))
        if not table_files:
            continue

        # Process each table
        for table_file in sorted(table_files):
            table_name = table_file.stem  # e.g., "table-69-1"
            total_tables += 1

            try:
                logger.info(f"  Processing {table_name}...")

                # Read HTML content
                with open(table_file, "r", encoding="utf-8") as f:
                    html_content = f.read()

                # Get corresponding PNG file
                png_file = table_file.with_suffix(".png")
                if not png_file.exists():
                    logger.warning(f"    Warning: PNG file not found for {table_name}")
                    tables_failed += 1
                    continue

                # Improve table structure
                corrected_html = improve_table_structure(
                    litellm_client, html_content, png_file
                )

                # Replace original HTML file with corrected version
                with open(table_file, "w", encoding="utf-8") as f:
                    f.write(corrected_html)

                logger.info(f"    ✓ Improved structure for {table_name}")
                tables_processed += 1

            except Exception as e:
                logger.error(f"    ✗ Error processing {table_name}: {e}", exc_info=True)
                tables_failed += 1

    logger.info(
        f"✅ Table structure improvement complete! "
        f"Processed: {tables_processed}, Failed: {tables_failed}, Total: {total_tables}"
    )

    return {
        "status": "success" if tables_failed == 0 else "partial",
        "tables_processed": tables_processed,
        "tables_failed": tables_failed,
        "total_tables": total_tables,
    }


if __name__ == "__main__":
    # Example usage
    from complex_pdf.core.llm.litellm_client import LitellmClient

    scratch_path = Path("output/short_complex_manual")
    litellm_client = LitellmClient(model_name="openai/gpt-4o")

    results = process_all_tables_structure(scratch_path, litellm_client)
    print(f"Results: {results}")
