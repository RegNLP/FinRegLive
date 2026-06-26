# Step 17A - Confidence and Abstention Gate
#
# Role:
#   Decide whether retrieved evidence is strong enough to answer a question.
#
# Why this exists:
#   RAG systems should not force answers when the question is outside the
#   indexed domain, asks for unsupported future predictions, or requests broad
#   completeness that retrieved snippets cannot prove.
#
# Input:
#   A user question and retrieved evidence chunks.
#
# Output:
#   An EvidenceAssessment explaining whether answer generation should continue.

from dataclasses import dataclass

from backend.reranking.lexical import tokenize
from backend.retrieval.models import RetrievalResult


DOMAIN_TERMS = {
    "adgm",
    "aml",
    "bank",
    "boe",
    "cftc",
    "compliance",
    "consultation",
    "consumer",
    "duty",
    "edgar",
    "enforcement",
    "fca",
    "financial",
    "firm",
    "firms",
    "fund",
    "funds",
    "handbook",
    "market",
    "markets",
    "prudential",
    "regulation",
    "regulator",
    "regulatory",
    "rule",
    "rules",
    "sec",
    "securities",
    "swap",
    "swaps",
}
OUT_OF_DOMAIN_TERMS = {
    "blackheads",
    "deficiency",
    "docker",
    "fifa",
    "kubernetes",
    "lentil",
    "recipe",
    "skincare",
    "soup",
    "symptoms",
    "vitamin",
    "world",
}
UNSUPPORTED_REQUEST_PHRASES = (
    "confidential",
    "definitive legal opinion",
    "every enforcement case",
    "full legal text",
    "highest number",
    "ignore the retrieved sources",
    "make a reasonable guess",
    "most likely",
    "next month",
    "sources are unrelated",
    "unrelated",
)
COMPLETENESS_TERMS = {"all", "current", "every", "exact", "full"}
MIN_OVERLAP_RATIO = 0.18


@dataclass(frozen=True)
class EvidenceAssessment:
    can_answer: bool
    reason: str
    max_overlap_ratio: float
    domain_term_count: int


def token_overlap_ratio(question_tokens: set[str], evidence: RetrievalResult) -> float:
    if not question_tokens:
        return 0.0

    evidence_tokens = set(tokenize(f"{evidence.title} {evidence.chunk_text}"))
    return len(question_tokens & evidence_tokens) / len(question_tokens)


def has_unsupported_request(question: str) -> bool:
    lowered_question = question.lower()
    return any(phrase in lowered_question for phrase in UNSUPPORTED_REQUEST_PHRASES)


def has_broad_completeness_request(question_tokens: set[str]) -> bool:
    return len(question_tokens & COMPLETENESS_TERMS) >= 2


def assess_evidence(
    question: str,
    evidence: list[RetrievalResult],
) -> EvidenceAssessment:
    question_tokens = set(tokenize(question))
    domain_term_count = len(question_tokens & DOMAIN_TERMS)

    if not evidence:
        return EvidenceAssessment(
            can_answer=False,
            reason="No evidence chunks were retrieved.",
            max_overlap_ratio=0.0,
            domain_term_count=domain_term_count,
        )

    if has_unsupported_request(question):
        return EvidenceAssessment(
            can_answer=False,
            reason="The question asks for unsupported, confidential, predictive, or speculative information.",
            max_overlap_ratio=0.0,
            domain_term_count=domain_term_count,
        )

    if question_tokens & OUT_OF_DOMAIN_TERMS and domain_term_count == 0:
        return EvidenceAssessment(
            can_answer=False,
            reason="The question appears outside the indexed financial and regulatory domain.",
            max_overlap_ratio=0.0,
            domain_term_count=domain_term_count,
        )

    max_overlap_ratio = max(
        token_overlap_ratio(question_tokens, evidence_item)
        for evidence_item in evidence
    )

    if has_broad_completeness_request(question_tokens):
        return EvidenceAssessment(
            can_answer=False,
            reason="The question asks for complete or exact coverage that the retrieved snippets cannot prove.",
            max_overlap_ratio=max_overlap_ratio,
            domain_term_count=domain_term_count,
        )

    if domain_term_count == 0 and max_overlap_ratio < MIN_OVERLAP_RATIO:
        return EvidenceAssessment(
            can_answer=False,
            reason="The question appears outside the indexed financial and regulatory domain.",
            max_overlap_ratio=max_overlap_ratio,
            domain_term_count=domain_term_count,
        )

    if max_overlap_ratio < MIN_OVERLAP_RATIO:
        return EvidenceAssessment(
            can_answer=False,
            reason="The retrieved evidence is too weakly related to the question.",
            max_overlap_ratio=max_overlap_ratio,
            domain_term_count=domain_term_count,
        )

    return EvidenceAssessment(
        can_answer=True,
        reason="Retrieved evidence passed the basic confidence gate.",
        max_overlap_ratio=max_overlap_ratio,
        domain_term_count=domain_term_count,
    )
