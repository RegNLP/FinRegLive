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

from backend.generation.confidence import EvidenceAssessment, assess_evidence
from backend.generation.llm_client import generate_openai_answer
from backend.generation.models import AnswerSource, GroundedAnswer
from backend.reranking.lexical import rerank_lexical
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


def build_sources(evidence: list[RetrievalResult]) -> list[AnswerSource]:
    return [
        AnswerSource(
            chunk_id=item.chunk_id,
            title=item.title,
            source_name=item.source_name,
            source_url=item.source_url,
        )
        for item in evidence
    ]


def build_abstention_answer(
    question: str,
    evidence: list[RetrievalResult],
    assessment: EvidenceAssessment,
) -> GroundedAnswer:
    return GroundedAnswer(
        question=question,
        answer="The retrieved evidence is insufficient to answer this question.",
        sources=build_sources(evidence),
        limitations=[
            assessment.reason,
            f"Maximum question/evidence overlap: {assessment.max_overlap_ratio:.2f}.",
            "This answer is generated only from retrieved evidence.",
            "This is not legal, financial, or investment advice.",
        ],
    )


def retrieve_answer_evidence(
    question: str,
    top_k: int = 5,
    use_reranking: bool = False,
) -> list[RetrievalResult]:
    if not use_reranking:
        return retrieve_hybrid(question, top_k=top_k)

    candidate_k = min(max(top_k * 4, top_k), 50)
    candidates = retrieve_hybrid(question, top_k=candidate_k)
    return rerank_lexical(question, candidates, top_k=top_k)


def answer_question(
    question: str,
    top_k: int = 5,
    use_reranking: bool = False,
) -> GroundedAnswer:
    evidence = retrieve_answer_evidence(
        question,
        top_k=top_k,
        use_reranking=use_reranking,
    )
    assessment = assess_evidence(question, evidence)
    if not assessment.can_answer:
        return build_abstention_answer(question, evidence, assessment)

    return build_local_answer(question, evidence)


def answer_question_with_llm(
    question: str,
    top_k: int = 5,
    use_reranking: bool = False,
) -> GroundedAnswer:
    evidence = retrieve_answer_evidence(
        question,
        top_k=top_k,
        use_reranking=use_reranking,
    )

    assessment = assess_evidence(question, evidence)
    if not assessment.can_answer:
        return build_abstention_answer(question, evidence, assessment)

    answer_text = generate_openai_answer(question, evidence)
    fallback_answer = build_local_answer(question, evidence)

    return GroundedAnswer(
        question=question,
        answer=answer_text,
        sources=fallback_answer.sources,
        limitations=[
            "This answer is generated only from retrieved evidence.",
            "This is not legal, financial, or investment advice.",
        ],
    )


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
    parser.add_argument("--use-llm", action="store_true")
    parser.add_argument("--use-reranking", action="store_true")
    args = parser.parse_args()

    if args.use_llm:
        print_answer(
            answer_question_with_llm(
                args.question,
                top_k=args.top_k,
                use_reranking=args.use_reranking,
            )
        )
    else:
        print_answer(
            answer_question(
                args.question,
                top_k=args.top_k,
                use_reranking=args.use_reranking,
            )
        )


if __name__ == "__main__":
    main()
