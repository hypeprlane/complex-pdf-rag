import json

from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.indexing.prompts.map_question_section import (
    MAP_QUESTION_SECTION_PROMPT,
)
from complex_pdf.indexing.schemas import QuestionMappingResponse


def map_question_chapter(litellm_client: LitellmClient, user_question: str) -> str:
    resp = litellm_client.chat(
        messages=[
            {
                "role": "system",
                "content": "You are a technical assistant that maps a user's question to the most relevant section and chapter in a service manual.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": MAP_QUESTION_SECTION_PROMPT.format(
                            user_question=user_question
                        ),
                    },
                ],
            },
        ],
        response_format=QuestionMappingResponse,
    )
    return json.loads(resp.choices[0].message.content)


if __name__ == "__main__":
    from colpali_rag.llm.litellm_client import LitellmClient

    litellm_client = LitellmClient(model_name="openai/gpt-4o")
    user_question = "What sequence of checks should be performed if the engine starts but none of the hydraulic functions work?"
    print(map_question_chapter(litellm_client, user_question))
