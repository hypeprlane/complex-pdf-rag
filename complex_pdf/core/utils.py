import base64
import json
from pathlib import Path


def encode_image_to_data_uri(image_path: Path) -> str:
    """
    Read a PNG (or other) image from disk and return a data URI string.
    Raises FileNotFoundError if the file does not exist.
    """
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{base64_image}"


def read_json_file(json_path: Path) -> str:
    """
    Read a JSON file from disk and return the contents as a string.
    Raises FileNotFoundError if the file does not exist.
    """
    with open(json_path, "r") as f:
        return json.dumps(json.dumps(json.load(f)))


def read_text_file(text_path: Path) -> str:
    """
    Read a text file from disk and return the contents as a string.
    Raises FileNotFoundError if the file does not exist.
    """
    with open(text_path, "r") as f:
        return f.read()


def enhance_context_metadata(
    context_metadata_path: Path, basic_metadata_path: Path
) -> dict:
    """
    Enhance context metadata with information from basic metadata file.

    Args:
        context_metadata_path: Path to the context metadata JSON file
        basic_metadata_path: Path to the basic metadata JSON file

    Returns:
        Enhanced context metadata dictionary with additional boolean flags

    Raises:
        FileNotFoundError: If either file doesn't exist
        json.JSONDecodeError: If either file contains invalid JSON
    """
    # Read both metadata files
    with open(context_metadata_path, "r") as f:
        context_metadata = json.load(f)

    with open(basic_metadata_path, "r") as f:
        basic_metadata = json.load(f)

    # Extract content information from basic metadata
    tables = basic_metadata.get("tables", [])
    figures = basic_metadata.get("figures", [])
    text_blocks = basic_metadata.get("text_blocks", [])

    # Add boolean flags to context metadata
    enhanced_metadata = context_metadata.copy()
    enhanced_metadata.update(
        {
            "has_tables": len(tables) > 0,
            "has_figures": len(figures) > 0,
            "has_text_blocks": len(text_blocks) > 0,
            "table_count": len(tables),
            "figure_count": len(figures),
            "text_block_count": len(text_blocks),
            "content_summary": {
                "tables": tables,
                "figures": figures,
                "text_blocks": text_blocks,
            },
        }
    )

    return enhanced_metadata


def enhance_context_metadata_file(
    context_metadata_path: Path,
    basic_metadata_path: Path,
    output_path: Path = None,
) -> Path:
    """
    Enhance a context metadata file and save the result.

    Args:
        context_metadata_path: Path to the context metadata JSON file
        basic_metadata_path: Path to the basic metadata JSON file
        output_path: Path to save the enhanced metadata (optional,
            defaults to overwriting input)

    Returns:
        Path to the saved enhanced metadata file
    """
    enhanced_metadata = enhance_context_metadata(
        context_metadata_path, basic_metadata_path
    )

    if output_path is None:
        output_path = context_metadata_path

    with open(output_path, "w") as f:
        json.dump(enhanced_metadata, f, indent=2)

    return output_path
