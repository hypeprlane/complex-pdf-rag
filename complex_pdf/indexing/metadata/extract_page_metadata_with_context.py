from pathlib import Path

from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.core.utils import (
    encode_image_to_data_uri,
    read_json_file,
    read_text_file,
)
from complex_pdf.indexing.prompts.context_metadata import METADATA_PROMPT


def extract_metadata_from_page(
    litellm_client: LitellmClient,
    image_path_n: str,
    image_path_n_1: str,
    image_path_n_plus_1: str,
    metadata_page_n_1_path: str,
    metadata_page_n_path: str,
    metadata_page_n_plus_1_path: str,
    page_n_1_text_path: str,
    page_n_text_path: str,
    page_n_plus_1_text_path: str,
) -> str:
    """
    Answer a specific question by reading a technical manual page

    Args:
        litellm_client: LitellmClient instance
        image_path: Path to the image file
        question: Specific question to answer

    Returns:
        Answer extracted from the image
    """
    image_data_uri = encode_image_to_data_uri(Path(image_path_n))
    image_data_uri_n_1 = encode_image_to_data_uri(Path(image_path_n_1))
    image_data_uri_n_plus_1 = encode_image_to_data_uri(Path(image_path_n_plus_1))

    metadata_page_n_1 = str(read_json_file(Path(metadata_page_n_1_path)))
    metadata_page_n = str(read_json_file(Path(metadata_page_n_path)))
    metadata_page_n_plus_1 = str(read_json_file(Path(metadata_page_n_plus_1_path)))

    page_n_1_text = str(read_text_file(Path(page_n_1_text_path)))
    page_n_text = str(read_text_file(Path(page_n_text_path)))
    page_n_plus_1_text = str(read_text_file(Path(page_n_plus_1_text_path)))

    # Build content array with only non-empty images
    content = [
        {
            "type": "text",
            "text": METADATA_PROMPT.replace("{metadata_page_n_1}", metadata_page_n_1)
            .replace("{metadata_page_n}", metadata_page_n)
            .replace("{metadata_page_n_plus_1}", metadata_page_n_plus_1)
            .replace("{page_n_1_text}", page_n_1_text)
            .replace("{page_n_text}", page_n_text)
            .replace("{page_n_plus_1_text}", page_n_plus_1_text),
        }
    ]

    # Add images only if they exist
    if image_data_uri:
        content.append({"type": "image_url", "image_url": {"url": image_data_uri}})
    if image_data_uri_n_1:
        content.append({"type": "image_url", "image_url": {"url": image_data_uri_n_1}})
    if image_data_uri_n_plus_1:
        content.append(
            {"type": "image_url", "image_url": {"url": image_data_uri_n_plus_1}}
        )

    resp = litellm_client.chat(
        messages=[
            {
                "role": "user",
                "content": content,
            },
        ],
        response_format=None,
        temperature=0.0,
        max_tokens=10000,
    )

    return resp.choices[0].message.content


def extract_metadata_from_page_with_response(
    litellm_client: LitellmClient,
    image_path_n: str,
    image_path_n_1: str,
    image_path_n_plus_1: str,
    metadata_page_n_1_path: str,
    metadata_page_n_path: str,
    metadata_page_n_plus_1_path: str,
    page_n_1_text_path: str,
    page_n_text_path: str,
    page_n_plus_1_text_path: str,
):
    """
    Extract metadata for a specific page using its context (n-1, n, n+1).
    Returns the full LiteLLM response object for cost tracking.

    Args:
        litellm_client: LitellmClient instance
        image_path_n: Path to current page image
        image_path_n_1: Path to previous page image
        image_path_n_plus_1: Path to next page image
        metadata_page_n_1_path: Path to previous page metadata
        metadata_page_n_path: Path to current page metadata
        metadata_page_n_plus_1_path: Path to next page metadata
        page_n_1_text_path: Path to previous page text
        page_n_text_path: Path to current page text
        page_n_plus_1_text_path: Path to next page text

    Returns:
        Full LiteLLM response object containing both content and usage information
    """
    # Handle missing images gracefully
    try:
        image_data_uri = encode_image_to_data_uri(Path(image_path_n))
    except FileNotFoundError:
        image_data_uri = ""

    try:
        image_data_uri_n_1 = encode_image_to_data_uri(Path(image_path_n_1))
    except FileNotFoundError:
        image_data_uri_n_1 = ""

    try:
        image_data_uri_n_plus_1 = encode_image_to_data_uri(Path(image_path_n_plus_1))
    except FileNotFoundError:
        image_data_uri_n_plus_1 = ""

    # Handle missing metadata files gracefully
    try:
        metadata_page_n_1 = str(read_json_file(Path(metadata_page_n_1_path)))
    except FileNotFoundError:
        metadata_page_n_1 = "{}"

    try:
        metadata_page_n = str(read_json_file(Path(metadata_page_n_path)))
    except FileNotFoundError:
        metadata_page_n = "{}"

    try:
        metadata_page_n_plus_1 = str(read_json_file(Path(metadata_page_n_plus_1_path)))
    except FileNotFoundError:
        metadata_page_n_plus_1 = "{}"

    # Handle missing text files gracefully
    try:
        page_n_1_text = str(read_text_file(Path(page_n_1_text_path)))
    except FileNotFoundError:
        page_n_1_text = ""

    try:
        page_n_text = str(read_text_file(Path(page_n_text_path)))
    except FileNotFoundError:
        page_n_text = ""

    try:
        page_n_plus_1_text = str(read_text_file(Path(page_n_plus_1_text_path)))
    except FileNotFoundError:
        page_n_plus_1_text = ""

    resp = litellm_client.chat(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": METADATA_PROMPT.replace(
                            "{metadata_page_n_1}", metadata_page_n_1
                        )
                        .replace("{metadata_page_n}", metadata_page_n)
                        .replace("{metadata_page_n_plus_1}", metadata_page_n_plus_1)
                        .replace("{page_n_1_text}", page_n_1_text)
                        .replace("{page_n_text}", page_n_text)
                        .replace("{page_n_plus_1_text}", page_n_plus_1_text),
                    },
                    {"type": "image_url", "image_url": {"url": image_data_uri}},
                    {"type": "image_url", "image_url": {"url": image_data_uri_n_1}},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_uri_n_plus_1},
                    },
                ],
            },
        ],
        response_format=None,
        temperature=0.0,
        max_tokens=10000,
    )

    return resp


if __name__ == "__main__":
    litellm_client = LitellmClient(model_name="openai/gpt-4o")
    import json

    metadata = extract_metadata_from_page(
        litellm_client,
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_27/page_27_full.png",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_28/page_28_full.png",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_29/page_29_full.png",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_27/metadata_page_27.json",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_28/metadata_page_28.json",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_29/metadata_page_29.json",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_27/text/page_27_text.txt",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_28/text/page_28_text.txt",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_29/text/page_29_text.txt",
    )

    print(metadata)

    clean_json_str = (
        metadata.strip().removeprefix("```json").removesuffix("```").strip()
    )
    parsed_data = json.loads(clean_json_str)

    # Step 3: Save to JSON file properly
    with open("page_28_metadata.json", "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=2)
