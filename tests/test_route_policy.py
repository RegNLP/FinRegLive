# Step 18B - Route Policy Tests
#
# Role:
#   Verify query class to route policy mapping.
#
# Why this exists:
#   Route policy controls retrieval depth, reranking, model cost, verification,
#   judge calls, and retry budget. These settings should be explicit and
#   protected before being wired into the live query pipeline.
#
# Input:
#   QueryClass values and QueryClassification objects.
#
# Output:
#   Passing pytest checks for route names and route settings.

from backend.routing.classifier import QueryClass, QueryClassification, RouteHint
from backend.routing.policy import (
    GenerationMode,
    RouteName,
    VerificationLevel,
    get_route_for_classification,
    get_route_for_query_class,
    route_policy_to_dict,
)


def test_definition_lookup_uses_simple_route() -> None:
    policy = get_route_for_query_class(QueryClass.DEFINITION_LOOKUP)

    assert policy.route_name == RouteName.SIMPLE
    assert policy.top_k == 3
    assert policy.use_reranking is False
    assert policy.requires_judge is False
    assert policy.verification_level == VerificationLevel.CITATION


def test_obligation_comparison_and_general_use_medium_route() -> None:
    for query_class in (
        QueryClass.OBLIGATION_QUESTION,
        QueryClass.COMPARISON_QUESTION,
        QueryClass.GENERAL_QUESTION,
    ):
        policy = get_route_for_query_class(query_class)

        assert policy.route_name == RouteName.MEDIUM
        assert policy.top_k == 8
        assert policy.candidate_k == 20
        assert policy.use_reranking is True
        assert policy.requires_judge is False
        assert policy.verification_level == VerificationLevel.CITATION_AND_ANSWERABILITY


def test_multi_hop_and_compliance_use_complex_route() -> None:
    for query_class in (
        QueryClass.MULTI_HOP_CROSS_REFERENCE,
        QueryClass.COMPLIANCE_DECISION,
    ):
        policy = get_route_for_query_class(query_class)

        assert policy.route_name == RouteName.COMPLEX
        assert policy.top_k == 12
        assert policy.candidate_k == 30
        assert policy.use_reranking is True
        assert policy.requires_judge is True
        assert policy.generation_mode == GenerationMode.STRONG_MODEL
        assert policy.verification_level == VerificationLevel.STRICT_WITH_JUDGE


def test_out_of_domain_uses_abstain_route() -> None:
    policy = get_route_for_query_class(QueryClass.OUT_OF_DOMAIN)

    assert policy.route_name == RouteName.ABSTAIN
    assert policy.top_k == 0
    assert policy.candidate_k == 0
    assert policy.use_reranking is False
    assert policy.generation_mode == GenerationMode.NONE
    assert policy.max_retry == 0


def test_route_policy_can_be_selected_from_classification() -> None:
    classification = QueryClassification(
        query_class=QueryClass.COMPLIANCE_DECISION,
        confidence=0.9,
        matched_rules=("phrase:is this compliant",),
        route_hint=RouteHint.COMPLEX,
    )

    policy = get_route_for_classification(classification)

    assert policy.route_name == RouteName.COMPLEX


def test_route_policy_serializes_for_diagnostics() -> None:
    policy = get_route_for_query_class(QueryClass.DEFINITION_LOOKUP)

    payload = route_policy_to_dict(policy)

    assert payload["route_name"] == "simple"
    assert payload["top_k"] == 3
    assert payload["verification_level"] == "citation"
