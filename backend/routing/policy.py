# Step 18B - Route Policy
#
# Role:
#   Map query classes to route settings and cost controls.
#
# Why this exists:
#   Query classification says what kind of question was asked. Route policy
#   turns that class into concrete execution settings such as top-k, reranking,
#   generation mode, verification level, judge usage, and retry budget.
#
# Input:
#   QueryClass or QueryClassification.
#
# Output:
#   RoutePolicy describing how the RAG pipeline should handle the question.

from dataclasses import dataclass
from enum import Enum

from backend.routing.classifier import QueryClass, QueryClassification


class RouteName(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    ABSTAIN = "abstain"


class GenerationMode(str, Enum):
    LOCAL = "local"
    MEDIUM_MODEL = "medium_model"
    STRONG_MODEL = "strong_model"
    NONE = "none"


class VerificationLevel(str, Enum):
    NONE = "none"
    CITATION = "citation"
    CITATION_AND_ANSWERABILITY = "citation_and_answerability"
    STRICT_WITH_JUDGE = "strict_with_judge"


@dataclass(frozen=True)
class RoutePolicy:
    route_name: RouteName
    top_k: int
    candidate_k: int
    use_reranking: bool
    generation_mode: GenerationMode
    verification_level: VerificationLevel
    requires_judge: bool
    max_retry: int
    reason: str


ROUTE_POLICIES: dict[RouteName, RoutePolicy] = {
    RouteName.SIMPLE: RoutePolicy(
        route_name=RouteName.SIMPLE,
        top_k=3,
        candidate_k=3,
        use_reranking=False,
        generation_mode=GenerationMode.LOCAL,
        verification_level=VerificationLevel.CITATION,
        requires_judge=False,
        max_retry=1,
        reason="Simple lookup route uses small context and low-cost generation.",
    ),
    RouteName.MEDIUM: RoutePolicy(
        route_name=RouteName.MEDIUM,
        top_k=8,
        candidate_k=20,
        use_reranking=True,
        generation_mode=GenerationMode.MEDIUM_MODEL,
        verification_level=VerificationLevel.CITATION_AND_ANSWERABILITY,
        requires_judge=False,
        max_retry=1,
        reason="Medium route uses reranking and more evidence for obligations, comparisons, and general questions.",
    ),
    RouteName.COMPLEX: RoutePolicy(
        route_name=RouteName.COMPLEX,
        top_k=12,
        candidate_k=30,
        use_reranking=True,
        generation_mode=GenerationMode.STRONG_MODEL,
        verification_level=VerificationLevel.STRICT_WITH_JUDGE,
        requires_judge=True,
        max_retry=1,
        reason="Complex route uses larger context, reranking, and judge verification for high-risk or multi-hop questions.",
    ),
    RouteName.ABSTAIN: RoutePolicy(
        route_name=RouteName.ABSTAIN,
        top_k=0,
        candidate_k=0,
        use_reranking=False,
        generation_mode=GenerationMode.NONE,
        verification_level=VerificationLevel.NONE,
        requires_judge=False,
        max_retry=0,
        reason="Abstain route avoids generation for out-of-domain questions.",
    ),
}


QUERY_CLASS_TO_ROUTE: dict[QueryClass, RouteName] = {
    QueryClass.DEFINITION_LOOKUP: RouteName.SIMPLE,
    QueryClass.OBLIGATION_QUESTION: RouteName.MEDIUM,
    QueryClass.COMPARISON_QUESTION: RouteName.MEDIUM,
    QueryClass.GENERAL_QUESTION: RouteName.MEDIUM,
    QueryClass.MULTI_HOP_CROSS_REFERENCE: RouteName.COMPLEX,
    QueryClass.COMPLIANCE_DECISION: RouteName.COMPLEX,
    QueryClass.OUT_OF_DOMAIN: RouteName.ABSTAIN,
}


def get_route_for_query_class(query_class: QueryClass) -> RoutePolicy:
    route_name = QUERY_CLASS_TO_ROUTE[query_class]
    return ROUTE_POLICIES[route_name]


def get_route_for_classification(
    classification: QueryClassification,
) -> RoutePolicy:
    return get_route_for_query_class(classification.query_class)


def route_policy_to_dict(policy: RoutePolicy) -> dict[str, object]:
    return {
        "route_name": policy.route_name.value,
        "top_k": policy.top_k,
        "candidate_k": policy.candidate_k,
        "use_reranking": policy.use_reranking,
        "generation_mode": policy.generation_mode.value,
        "verification_level": policy.verification_level.value,
        "requires_judge": policy.requires_judge,
        "max_retry": policy.max_retry,
        "reason": policy.reason,
    }
