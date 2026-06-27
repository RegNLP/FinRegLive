# Step 18C - Evidence Diagnostics
#
# Role:
#   Measure retrieved evidence quality before generation.
#
# Why this exists:
#   The system should know whether evidence is concentrated, weak, risky, or
#   strong enough for the selected route. These diagnostics make route-aware
#   generation and abstention decisions explainable.
#
# Input:
#   User question, retrieved RetrievalResult objects, and RoutePolicy.
#
# Output:
#   EvidenceDiagnostics with score, spread, risk, and strength signals.

from dataclasses import dataclass
from enum import Enum

from backend.reranking.lexical import tokenize
from backend.retrieval.models import RetrievalResult
from backend.routing.policy import RouteName, RoutePolicy


class EvidenceStrength(str, Enum):
    NONE = "none"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


RISK_MARKER_TERMS = {
    "approval",
    "approve",
    "compliant",
    "deadline",
    "exemption",
    "fined",
    "notify",
    "penalty",
    "permission",
    "required",
    "threshold",
}
CROSS_REFERENCE_TERMS = {
    "across",
    "both",
    "cross-reference",
    "documents",
    "multiple",
    "read together",
    "section",
    "sections",
    "sources",
}


@dataclass(frozen=True)
class EvidenceDiagnostics:
    route_name: RouteName
    retrieved_count: int
    top_score: float
    score_margin: float
    source_document_count: int
    duplicate_document_count: int
    source_name_count: int
    strong_passage_count: int
    max_token_overlap: float
    avg_token_overlap: float
    has_cross_reference_signal: bool
    risk_markers: tuple[str, ...]
    evidence_strength: EvidenceStrength
    reasons: tuple[str, ...]


def token_overlap_ratio(question_tokens: set[str], evidence: RetrievalResult) -> float:
    if not question_tokens:
        return 0.0

    evidence_tokens = set(tokenize(f"{evidence.title} {evidence.chunk_text}"))
    return len(question_tokens & evidence_tokens) / len(question_tokens)


def score_margin(results: list[RetrievalResult]) -> float:
    if len(results) < 2:
        return results[0].score if results else 0.0
    return results[0].score - results[1].score


def find_risk_markers(question: str, evidence: list[RetrievalResult]) -> tuple[str, ...]:
    text = " ".join(
        [
            question,
            *[item.title for item in evidence],
            *[item.chunk_text for item in evidence[:5]],
        ]
    ).lower()
    tokens = set(tokenize(text))
    return tuple(sorted(tokens & RISK_MARKER_TERMS))


def has_cross_reference_signal(question: str, evidence: list[RetrievalResult]) -> bool:
    text = " ".join(
        [
            question,
            *[item.title for item in evidence],
            *[item.chunk_text for item in evidence[:5]],
        ]
    ).lower()
    tokens = set(tokenize(text))
    return bool(tokens & CROSS_REFERENCE_TERMS) or "read together" in text


def count_strong_passages(overlap_ratios: list[float], route_policy: RoutePolicy) -> int:
    if route_policy.route_name == RouteName.SIMPLE:
        threshold = 0.25
    elif route_policy.route_name == RouteName.MEDIUM:
        threshold = 0.20
    else:
        threshold = 0.16

    return sum(ratio >= threshold for ratio in overlap_ratios)


def classify_strength(
    route_policy: RoutePolicy,
    retrieved_count: int,
    strong_passage_count: int,
    source_document_count: int,
    max_token_overlap: float,
) -> tuple[EvidenceStrength, tuple[str, ...]]:
    reasons: list[str] = []

    if retrieved_count == 0:
        return EvidenceStrength.NONE, ("No evidence was retrieved.",)

    if max_token_overlap < 0.12:
        reasons.append("Maximum question/evidence token overlap is low.")

    if strong_passage_count == 0:
        reasons.append("No strong passages were detected.")

    if route_policy.route_name == RouteName.SIMPLE:
        if strong_passage_count >= 1 and max_token_overlap >= 0.25:
            return EvidenceStrength.STRONG, ("Simple route has at least one strong passage.",)
        if strong_passage_count >= 1:
            return EvidenceStrength.MODERATE, ("Simple route has usable evidence.",)

    if route_policy.route_name == RouteName.MEDIUM:
        if strong_passage_count >= 2 and source_document_count >= 1:
            return EvidenceStrength.STRONG, ("Medium route has multiple strong passages.",)
        if strong_passage_count >= 1:
            return EvidenceStrength.MODERATE, ("Medium route has at least one strong passage.",)

    if route_policy.route_name == RouteName.COMPLEX:
        if strong_passage_count >= 3 and source_document_count >= 2:
            return EvidenceStrength.STRONG, (
                "Complex route has multiple strong passages across documents.",
            )
        if strong_passage_count >= 2:
            return EvidenceStrength.MODERATE, (
                "Complex route has multiple strong passages but limited document spread.",
            )

    if not reasons:
        reasons.append("Evidence did not meet strength thresholds for the selected route.")

    return EvidenceStrength.WEAK, tuple(reasons)


def diagnose_evidence(
    question: str,
    evidence: list[RetrievalResult],
    route_policy: RoutePolicy,
) -> EvidenceDiagnostics:
    question_tokens = set(tokenize(question))
    overlap_ratios = [
        token_overlap_ratio(question_tokens, item)
        for item in evidence
    ]
    document_ids = [item.document_id for item in evidence]
    unique_document_ids = set(document_ids)
    source_names = {item.source_name for item in evidence}
    strong_passages = count_strong_passages(overlap_ratios, route_policy)
    max_overlap = max(overlap_ratios, default=0.0)
    avg_overlap = (
        sum(overlap_ratios) / len(overlap_ratios)
        if overlap_ratios
        else 0.0
    )
    strength, reasons = classify_strength(
        route_policy=route_policy,
        retrieved_count=len(evidence),
        strong_passage_count=strong_passages,
        source_document_count=len(unique_document_ids),
        max_token_overlap=max_overlap,
    )

    return EvidenceDiagnostics(
        route_name=route_policy.route_name,
        retrieved_count=len(evidence),
        top_score=evidence[0].score if evidence else 0.0,
        score_margin=score_margin(evidence),
        source_document_count=len(unique_document_ids),
        duplicate_document_count=len(document_ids) - len(unique_document_ids),
        source_name_count=len(source_names),
        strong_passage_count=strong_passages,
        max_token_overlap=max_overlap,
        avg_token_overlap=avg_overlap,
        has_cross_reference_signal=has_cross_reference_signal(question, evidence),
        risk_markers=find_risk_markers(question, evidence),
        evidence_strength=strength,
        reasons=reasons,
    )


def evidence_diagnostics_to_dict(
    diagnostics: EvidenceDiagnostics,
) -> dict[str, object]:
    return {
        "route_name": diagnostics.route_name.value,
        "retrieved_count": diagnostics.retrieved_count,
        "top_score": diagnostics.top_score,
        "score_margin": diagnostics.score_margin,
        "source_document_count": diagnostics.source_document_count,
        "duplicate_document_count": diagnostics.duplicate_document_count,
        "source_name_count": diagnostics.source_name_count,
        "strong_passage_count": diagnostics.strong_passage_count,
        "max_token_overlap": diagnostics.max_token_overlap,
        "avg_token_overlap": diagnostics.avg_token_overlap,
        "has_cross_reference_signal": diagnostics.has_cross_reference_signal,
        "risk_markers": diagnostics.risk_markers,
        "evidence_strength": diagnostics.evidence_strength.value,
        "reasons": diagnostics.reasons,
    }
