# Step 08b - OpenAI LLM Client
#
# Role:
#   Generate source-grounded answers with the OpenAI API.
#
# Why this exists:
#   The local fallback proves the RAG flow, but an LLM can produce a clearer
#   natural-language answer from retrieved evidence. This client keeps the LLM
#   call isolated from retrieval and database code.
#
# Input:
#   User question, retrieved evidence, prompt instructions, and OPENAI_API_KEY.
#
# Output:
#   LLM-generated answer text.

import os

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

from backend.config import get_settings
from backend.generation.prompts import SYSTEM_INSTRUCTIONS, build_generation_prompt
from backend.retrieval.models import RetrievalResult


class MissingOpenAIAPIKeyError(RuntimeError):
    pass


class LLMGenerationError(RuntimeError):
    pass


def generate_openai_answer(question: str, evidence: list[RetrievalResult]) -> str:
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise MissingOpenAIAPIKeyError("OPENAI_API_KEY is not configured.")

    settings = get_settings()
    client = OpenAI()
    prompt = build_generation_prompt(question, evidence)

    try:
        response = client.responses.create(
            model=settings.llm.model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=prompt,
            temperature=0,
            max_output_tokens=700,
        )
    except OpenAIError as exc:
        raise LLMGenerationError("OpenAI answer generation failed.") from exc

    return response.output_text.strip()
