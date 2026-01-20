import json

from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.indexing.prompts.query_decomposition import (
    USER_QUESTION_DECOMPOSITION_PROMPT,
)
from complex_pdf.indexing.schemas import QueryDecompositionResponse


def user_query_decomposition(litellm_client: LitellmClient, user_question: str) -> str:
    resp = litellm_client.chat(
        messages=[
            {
                "role": "system",
                "content": "You are a technical assistant that decomposes a user's question into a list of sub-questions.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": USER_QUESTION_DECOMPOSITION_PROMPT.format(
                            user_question=user_question
                        ),
                    },
                ],
            },
        ],
        response_format=QueryDecompositionResponse,
        call_type="query_decomposition",
    )
    return json.loads(resp.choices[0].message.content)


if __name__ == "__main__":
    from complex_pdf.core.llm.litellm_client import LitellmClient

    litellm_client = LitellmClient(model_name="openai/gpt-4o")
    user_question = "What sequence of checks should be performed if the engine starts but none of the hydraulic functions work?"
    questions = user_query_decomposition(litellm_client, user_question)
