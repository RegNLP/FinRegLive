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

from dotenv import load_dotenv
from openai import OpenAI

from backend.config import get_settings
from backend.generation.prompts import SYSTEM_INSTRUCTIONS, build_generation_prompt
from backend.retrieval.models import RetrievalResult


def generate_openai_answer(question: str, evidence: list[RetrievalResult]) -> str:
    load_dotenv()

    settings = get_settings()
    client = OpenAI()
    prompt = build_generation_prompt(question, evidence)

    response = client.responses.create(
        model=settings.llm.model,
        instructions=SYSTEM_INSTRUCTIONS,
        input=prompt,
        temperature=0,
        max_output_tokens=700,
    )

    return response.output_text.strip()
