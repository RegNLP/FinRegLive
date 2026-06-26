# Step 08 - Source-Grounded Answer Generation
#
# Role:
#   Generate an answer from retrieved evidence.
#
# Why this exists:
#   Retrieval finds evidence, but users need an answer. This module creates a
#   grounded response while preserving sources and limitations.
#
# Input:
#   A user question and retrieved evidence chunks.
#
# Output:
#   A GroundedAnswer object.

import argparse

from backend.generation.models import AnswerSource, GroundedAnswer
from backend.retrieval.hybrid import retrieve_hybrid
from backend.retrieval.models import RetrievalResult


def build_local_answer(question: str, evidence: list[RetrievalResult]) -> GroundedAnswer:
    if not evidence:
        return GroundedAnswer(
            question=question,
            answer="The retrieved evidence is insufficient to answer this question.",
            sources=[],
            limitations=["No evidence chunks were retrieved."],
        )

    evidence_lines = []
    for item in evidence[:3]:
        evidence_lines.append(f"- {item.chunk_text} [{item.chunk_id}]")

    answer = (
        "Based on the retrieved evidence, the most relevant information is:\n"
        + "\n".join(evidence_lines)
    )

    sources = [
        AnswerSource(
            chunk_id=item.chunk_id,
            title=item.title,
            source_name=item.source_name,
            source_url=item.source_url,
        )
        for item in evidence
    ]

    return GroundedAnswer(
        question=question,
        answer=answer,
        sources=sources,
        limitations=[
            "This answer is generated only from retrieved evidence.",
            "This is not legal, financial, or investment advice.",
        ],
    )


def answer_question(question: str, top_k: int = 5) -> GroundedAnswer:
    evidence = retrieve_hybrid(question, top_k=top_k)
    return build_local_answer(question, evidence)


def print_answer(answer: GroundedAnswer) -> None:
    print("\nQuestion:\n")
    print(answer.question)

    print("\nAnswer:\n")
    print(answer.answer)

    print("\nSources:\n")
    for source in answer.sources:
        print(f"- {source.chunk_id} | {source.source_name} | {source.title}")
        print(f"  {source.source_url}")

    print("\nLimitations:\n")
    for limitation in answer.limitations:
        print(f"- {limitation}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a source-grounded answer.")
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    print_answer(answer_question(args.question, top_k=args.top_k))


if __name__ == "__main__":
    main()
