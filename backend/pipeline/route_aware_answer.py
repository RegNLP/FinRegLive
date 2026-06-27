# Step 18D - Route-Aware Answer Pipeline
#
# Role:
#   Orchestrate classification, route policy, retrieval, reranking, evidence
#   diagnostics, and local answer generation.
#
# Why this exists:
#   Earlier steps built the pieces separately. This module connects them so
#   different question types can use different retrieval depth, reranking, and
#   abstention behavior.
#
# Input:
#   A user question.
#
# Output:
#   RouteAwareAnswer containing the answer plus routing and diagnostics metadata.

import argparse
import json
from dataclasses import dataclass

from backend.evidence.diagnostics import (
    EvidenceDiagnostics,
    EvidenceStrength,
    diagnose_evidence,
    evidence_diagnostics_to_dict,
)
from backend.generation.answer import build_abstention_answer, build_local_answer
from backend.generation.confidence import EvidenceAssessment, assess_evidence
from backend.generation.models import GroundedAnswer
from backend.reranking.lexical import rerank_lexical
from backend.retrieval.hybrid import retrieve_hybrid
from backend.retrieval.models import RetrievalResult
from backend.routing.classifier import QueryClassification, classify_query
from backend.routing.policy import (
    RouteName,
    RoutePolicy,
    get_route_for_classification,
    route_policy_to_dict,
)


@dataclass(frozen=True)
class RouteAwareAnswer:
    answer: GroundedAnswer
    classification: QueryClassification
    route_policy: RoutePolicy
    evidence_diagnostics: EvidenceDiagnostics
    evidence: list[RetrievalResult]


def retrieve_evidence_for_policy(
    question: str,
    route_policy: RoutePolicy,
) -> list[RetrievalResult]:
    if route_policy.route_name == RouteName.ABSTAIN:
        return []

    candidate_count = (
        route_policy.candidate_k
        if route_policy.use_reranking
        else route_policy.top_k
    )
    candidates = retrieve_hybrid(question, top_k=candidate_count)

    if route_policy.use_reranking:
        return rerank_lexical(question, candidates, top_k=route_policy.top_k)

    return candidates[: route_policy.top_k]


def should_abstain_from_diagnostics(
    diagnostics: EvidenceDiagnostics,
    route_policy: RoutePolicy,
) -> bool:
    if route_policy.route_name == RouteName.ABSTAIN:
        return True

    if diagnostics.evidence_strength in {EvidenceStrength.NONE, EvidenceStrength.WEAK}:
        return True

    if (
        route_policy.route_name == RouteName.COMPLEX
        and diagnostics.evidence_strength != EvidenceStrength.STRONG
    ):
        return True

    return False


def build_route_abstention_assessment(
    route_policy: RoutePolicy,
    diagnostics: EvidenceDiagnostics,
) -> EvidenceAssessment:
    if route_policy.route_name == RouteName.ABSTAIN:
        reason = "The question is routed to abstain and will not be answered from the corpus."
    else:
        reason = (
            "Evidence diagnostics did not meet the strength threshold for "
            f"the {route_policy.route_name.value} route."
        )

    return EvidenceAssessment(
        can_answer=False,
        reason=reason,
        max_overlap_ratio=diagnostics.max_token_overlap,
        domain_term_count=0,
    )


def answer_question_route_aware(question: str) -> RouteAwareAnswer:
    classification = classify_query(question)
    route_policy = get_route_for_classification(classification)
    evidence = retrieve_evidence_for_policy(question, route_policy)
    diagnostics = diagnose_evidence(question, evidence, route_policy)

    if should_abstain_from_diagnostics(diagnostics, route_policy):
        answer = build_abstention_answer(
            question,
            evidence,
            build_route_abstention_assessment(route_policy, diagnostics),
        )
        return RouteAwareAnswer(
            answer=answer,
            classification=classification,
            route_policy=route_policy,
            evidence_diagnostics=diagnostics,
            evidence=evidence,
        )

    assessment = assess_evidence(question, evidence)
    if not assessment.can_answer:
        answer = build_abstention_answer(question, evidence, assessment)
    else:
        answer = build_local_answer(question, evidence)

    return RouteAwareAnswer(
        answer=answer,
        classification=classification,
        route_policy=route_policy,
        evidence_diagnostics=diagnostics,
        evidence=evidence,
    )


def route_aware_answer_to_dict(result: RouteAwareAnswer) -> dict[str, object]:
    return {
        "answer": result.answer.model_dump(),
        "classification": {
            "query_class": result.classification.query_class.value,
            "confidence": result.classification.confidence,
            "matched_rules": result.classification.matched_rules,
            "route_hint": result.classification.route_hint.value,
        },
        "route_policy": route_policy_to_dict(result.route_policy),
        "evidence_diagnostics": evidence_diagnostics_to_dict(
            result.evidence_diagnostics
        ),
        "evidence_chunk_ids": [item.chunk_id for item in result.evidence],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run route-aware local answering.")
    parser.add_argument("question")
    args = parser.parse_args()

    result = answer_question_route_aware(args.question)
    print(json.dumps(route_aware_answer_to_dict(result), indent=2))


if __name__ == "__main__":
    main()
