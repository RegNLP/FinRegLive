# Step 18A - Query Classifier Tests
#
# Role:
#   Verify the rule-based query classifier and priority order.
#
# Why this exists:
#   Routing changes retrieval depth, reranking, model cost, and verification.
#   The first classifier must be predictable and explainable before it is wired
#   into the live query path.
#
# Input:
#   Representative user questions.
#
# Output:
#   Passing pytest checks for query class, route hint, and matched rules.

from backend.routing.classifier import QueryClass, RouteHint, classify_query


CLASSIFIER_EXAMPLES = (
    ("What is an Authorised Person?", QueryClass.DEFINITION_LOOKUP, RouteHint.SIMPLE),
    ("Define Recognised Body.", QueryClass.DEFINITION_LOOKUP, RouteHint.SIMPLE),
    ("What does Client Money mean?", QueryClass.DEFINITION_LOOKUP, RouteHint.SIMPLE),
    (
        "What notification requirements apply to Authorised Persons?",
        QueryClass.OBLIGATION_QUESTION,
        RouteHint.MEDIUM,
    ),
    (
        "What obligations apply to a firm under this rule?",
        QueryClass.OBLIGATION_QUESTION,
        RouteHint.MEDIUM,
    ),
    (
        "Compare the notification duties under GEN and FSMR.",
        QueryClass.COMPARISON_QUESTION,
        RouteHint.MEDIUM,
    ),
    (
        "How do these two reporting obligations differ?",
        QueryClass.COMPARISON_QUESTION,
        RouteHint.MEDIUM,
    ),
    (
        "Which obligations apply across multiple documents?",
        QueryClass.MULTI_HOP_CROSS_REFERENCE,
        RouteHint.COMPLEX,
    ),
    (
        "What does Section X require when read together with Section Y?",
        QueryClass.MULTI_HOP_CROSS_REFERENCE,
        RouteHint.COMPLEX,
    ),
    (
        "Does the firm need approval if its controller changes?",
        QueryClass.COMPLIANCE_DECISION,
        RouteHint.COMPLEX,
    ),
    (
        "Can the firm rely on an exemption in this situation?",
        QueryClass.COMPLIANCE_DECISION,
        RouteHint.COMPLEX,
    ),
    ("What is the weather in Dubai?", QueryClass.OUT_OF_DOMAIN, RouteHint.ABSTAIN),
    (
        "What are the symptoms of vitamin D deficiency?",
        QueryClass.OUT_OF_DOMAIN,
        RouteHint.ABSTAIN,
    ),
    (
        "Explain the main point of this document.",
        QueryClass.GENERAL_QUESTION,
        RouteHint.MEDIUM,
    ),
    ("How does this rule work?", QueryClass.GENERAL_QUESTION, RouteHint.MEDIUM),
)


def test_curated_classifier_examples() -> None:
    for question, expected_class, expected_route in CLASSIFIER_EXAMPLES:
        result = classify_query(question)

        assert result.query_class == expected_class, question
        assert result.route_hint == expected_route, question


def test_classifies_definition_lookup() -> None:
    result = classify_query("What is an Authorised Person?")

    assert result.query_class == QueryClass.DEFINITION_LOOKUP
    assert result.route_hint == RouteHint.SIMPLE
    assert result.confidence >= 0.8
    assert result.matched_rules


def test_classifies_obligation_question() -> None:
    result = classify_query("What notification requirements apply to authorised persons?")

    assert result.query_class == QueryClass.OBLIGATION_QUESTION
    assert result.route_hint == RouteHint.MEDIUM
    assert "keyword:requirements" in result.matched_rules


def test_classifies_comparison_question() -> None:
    result = classify_query("Compare SEC and FCA updates.")

    assert result.query_class == QueryClass.COMPARISON_QUESTION
    assert result.route_hint == RouteHint.MEDIUM


def test_classifies_multi_hop_cross_reference_question() -> None:
    result = classify_query(
        "Across the retrieved documents, what themes appear most often?"
    )

    assert result.query_class == QueryClass.MULTI_HOP_CROSS_REFERENCE
    assert result.route_hint == RouteHint.COMPLEX


def test_classifies_compliance_decision_question() -> None:
    result = classify_query(
        "Does the firm need approval if its controller structure changes?"
    )

    assert result.query_class == QueryClass.COMPLIANCE_DECISION
    assert result.route_hint == RouteHint.COMPLEX


def test_classifies_out_of_domain_question() -> None:
    result = classify_query("What is the best skincare routine for blackheads?")

    assert result.query_class == QueryClass.OUT_OF_DOMAIN
    assert result.route_hint == RouteHint.ABSTAIN


def test_priority_keeps_high_risk_question_out_of_definition_route() -> None:
    result = classify_query("Is this compliant if the firm fails to notify the FCA?")

    assert result.query_class == QueryClass.COMPLIANCE_DECISION
    assert result.route_hint == RouteHint.COMPLEX


def test_priority_detects_comparison_before_obligation() -> None:
    result = classify_query("Compare the reporting obligations for firms X and Y.")

    assert result.query_class == QueryClass.COMPARISON_QUESTION
    assert result.route_hint == RouteHint.MEDIUM


def test_priority_detects_multi_hop_before_obligation() -> None:
    result = classify_query(
        "Across multiple documents, what reporting obligations appear most often?"
    )

    assert result.query_class == QueryClass.MULTI_HOP_CROSS_REFERENCE
    assert result.route_hint == RouteHint.COMPLEX


def test_broad_risk_terms_do_not_alone_create_compliance_decision() -> None:
    result = classify_query("What is the approval threshold?")

    assert result.query_class == QueryClass.GENERAL_QUESTION
    assert result.route_hint == RouteHint.MEDIUM


def test_fallback_uses_low_confidence_general_question() -> None:
    result = classify_query("Tell me about GEN.")

    assert result.query_class == QueryClass.GENERAL_QUESTION
    assert result.route_hint == RouteHint.MEDIUM
    assert result.confidence == 0.35
    assert result.matched_rules == ("fallback:no_specific_rule_matched",)


def test_matched_rules_are_tuple_for_frozen_classification() -> None:
    result = classify_query("Define Recognised Body.")

    assert isinstance(result.matched_rules, tuple)
