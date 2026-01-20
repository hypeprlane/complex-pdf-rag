from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.extraction.prompts.flatten_table import FLATTEN_TABLE_PROMPT


def flatten_table(litellm_client: LitellmClient, html_content: str) -> str:
    resp = litellm_client.chat(
        messages=[
            {
                "role": "system",
                "content": "You are a technical assistant that transforms technical tables into compact but complete summaries. Your goal is to produce a single paragraph that retains all essential information from the table, so nothing is lost during this flattening process. Your outputs will be embedded into a vector index for retrieval.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": FLATTEN_TABLE_PROMPT.format(table_html=html_content),
                    },
                    {
                        "type": "text",
                        "text": f"<html><body>{html_content}</body></html>",
                    },
                ],
            },
        ],
        response_format=None,
    )
    return resp.choices[0].message.content
