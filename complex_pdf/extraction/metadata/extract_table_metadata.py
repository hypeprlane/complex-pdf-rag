import json
from pathlib import Path

from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.core.utils import encode_image_to_data_uri
from complex_pdf.extraction.prompts.table_metadata import GENERATE_TABLE_METADATA_PROMPT
from complex_pdf.extraction.schemas import TableMetadataResponse


def generate_table_metadata(
    litellm_client: LitellmClient, html_content: str, pdf_page: str
) -> str:
    image_data_uri = encode_image_to_data_uri(pdf_page)

    resp = litellm_client.chat(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": GENERATE_TABLE_METADATA_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_data_uri}},
                    {
                        "type": "text",
                        "text": f"<html><body>{html_content}</body></html>",
                    },
                ],
            },
        ],
        response_format=TableMetadataResponse,
        temperature=0.0,
    )
    metadata_resp_string = resp.choices[0].message.content
    metadata_resp_json = json.loads(metadata_resp_string)
    return metadata_resp_json


def process_all_tables(scratch_path: Path = None, max_pages: int = None):
    """Process all tables in pages where has_tables is true."""
    if scratch_path is None:
        scratch_path = Path("scratch/service_manual_long")

    litellm_client = LitellmClient(model_name="openai/gpt-4o")

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
        print(
            f"Found {len(page_dirs)} page directories (limited to first {max_pages} pages)"
        )
    else:
        print(f"Found {len(page_dirs)} page directories")

    for page_dir in page_dirs:
        page_number = page_dir.name.split("_")[1]

        # Check if this page has tables
        context_file = page_dir / f"context_metadata_page_{page_number}.json"
        basic_file = page_dir / f"metadata_page_{page_number}.json"

        if not context_file.exists() or not basic_file.exists():
            print(f"Skipping page {page_number} - missing metadata files")
            continue

        # Read context metadata to check if has_tables is true
        with open(context_file, "r") as f:
            context_metadata = json.load(f)

        if not context_metadata.get("has_tables", False):
            continue

        print(f"Processing tables for page {page_number}...")

        # Get table files
        tables_dir = page_dir / "tables"
        if not tables_dir.exists():
            print(f"  No tables directory found for page {page_number}")
            continue

        table_files = list(tables_dir.glob("table-*.html"))
        if not table_files:
            print(f"  No table HTML files found for page {page_number}")
            continue

        # Process each table
        table_metadata_list = []
        for table_file in sorted(table_files):
            table_name = table_file.stem  # e.g., "table-69-1"
            print(f"  Processing {table_name}...")

            try:
                # Read HTML content
                with open(table_file, "r") as f:
                    html_content = f.read()

                # Get corresponding PNG file
                png_file = table_file.with_suffix(".png")
                if not png_file.exists():
                    print(f"    Warning: PNG file not found for {table_name}")
                    continue

                # Generate table metadata
                table_metadata = generate_table_metadata(
                    litellm_client, html_content, png_file
                )

                # Add table identifier and HTML content
                table_metadata["table_id"] = table_name
                table_metadata["table_file"] = str(table_file.name)
                table_metadata["table_image"] = str(png_file.name)
                table_metadata["table_html"] = html_content  # Include full HTML

                table_metadata_list.append(table_metadata)
                print(f"    ✓ Generated metadata for {table_name}")

            except Exception as e:
                print(f"    ✗ Error processing {table_name}: {e}")

        # Add table metadata to context metadata
        if table_metadata_list:
            context_metadata["table_metadata"] = table_metadata_list

            # Save enhanced context metadata
            with open(context_file, "w") as f:
                json.dump(context_metadata, f, indent=2)

            print(f"  ✓ Added {len(table_metadata_list)} table(s) to context metadata")
        else:
            print(f"  No table metadata generated for page {page_number}")


if __name__ == "__main__":
    # Process all tables
    process_all_tables()
