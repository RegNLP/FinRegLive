# Step 08 - Generation Prompts
#
# Role:
#   Store prompt rules for source-grounded answer generation.
#
# Why this exists:
#   The LLM must not answer from memory. These instructions make the expected
#   behavior explicit: answer only from retrieved evidence, cite sources, and
#   admit when evidence is insufficient.
#
# Input:
#   Retrieved evidence chunks and a user question.
#
# Output:
#   Prompt text that can be sent to an LLM.

from backend.retrieval.models import RetrievalResult


SYSTEM_INSTRUCTIONS = """You are a financial and regulatory RAG assistant.
Answer the user's question using only the provided evidence.
If the evidence is insufficient, say that the provided evidence is insufficient.
Do not invent facts, dates, citations, or source details.
Do not provide legal, financial, or investment advice.
Always cite evidence using chunk IDs.
"""


def format_evidence(evidence: list[RetrievalResult]) -> str:
    parts: list[str] = []

    for item in evidence:
        parts.append(
            "\n".join(
                [
                    f"CHUNK_ID: {item.chunk_id}",
                    f"TITLE: {item.title}",
                    f"SOURCE: {item.source_name}",
                    f"URL: {item.source_url}",
                    "TEXT:",
                    item.chunk_text,
                ]
            )
        )

    return "\n\n---\n\n".join(parts)


def build_generation_prompt(question: str, evidence: list[RetrievalResult]) -> str:
    return f"""Question:
{question}

Evidence:
{format_evidence(evidence)}

Answer format:
Answer:
<answer grounded only in the evidence>

Sources:
<chunk IDs used>

Limitations:
<any missing or insufficient evidence>
"""
