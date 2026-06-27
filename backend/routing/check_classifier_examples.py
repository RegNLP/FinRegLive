# Step 18A - Query Classifier Example Check
#
# Role:
#   Run curated classifier examples from the terminal.
#
# Why this exists:
#   The rule-based classifier should be easy to inspect without starting the
#   API or reading pytest internals. This script checks representative examples
#   and exits with a non-zero status if any expected class or route changes.
#
# Input:
#   Built-in example questions.
#
# Output:
#   A terminal table showing expected and actual classifier results.

from dataclasses import dataclass

from backend.routing.classifier import QueryClass, RouteHint, classify_query


@dataclass(frozen=True)
class ClassifierExample:
    question: str
    expected_class: QueryClass
    expected_route: RouteHint


EXAMPLES = (
    ClassifierExample(
        "What is an Authorised Person?",
        QueryClass.DEFINITION_LOOKUP,
        RouteHint.SIMPLE,
    ),
    ClassifierExample(
        "Define Recognised Body.",
        QueryClass.DEFINITION_LOOKUP,
        RouteHint.SIMPLE,
    ),
    ClassifierExample(
        "What does Client Money mean?",
        QueryClass.DEFINITION_LOOKUP,
        RouteHint.SIMPLE,
    ),
    ClassifierExample(
        "What notification requirements apply to Authorised Persons?",
        QueryClass.OBLIGATION_QUESTION,
        RouteHint.MEDIUM,
    ),
    ClassifierExample(
        "When must a firm notify the Regulator?",
        QueryClass.OBLIGATION_QUESTION,
        RouteHint.MEDIUM,
    ),
    ClassifierExample(
        "Compare the notification duties under GEN and FSMR.",
        QueryClass.COMPARISON_QUESTION,
        RouteHint.MEDIUM,
    ),
    ClassifierExample(
        "How do these two reporting obligations differ?",
        QueryClass.COMPARISON_QUESTION,
        RouteHint.MEDIUM,
    ),
    ClassifierExample(
        "Which obligations apply across multiple documents?",
        QueryClass.MULTI_HOP_CROSS_REFERENCE,
        RouteHint.COMPLEX,
    ),
    ClassifierExample(
        "What does Section X require when read together with Section Y?",
        QueryClass.MULTI_HOP_CROSS_REFERENCE,
        RouteHint.COMPLEX,
    ),
    ClassifierExample(
        "Does the firm need approval if its controller changes?",
        QueryClass.COMPLIANCE_DECISION,
        RouteHint.COMPLEX,
    ),
    ClassifierExample(
        "Can the firm rely on an exemption in this situation?",
        QueryClass.COMPLIANCE_DECISION,
        RouteHint.COMPLEX,
    ),
    ClassifierExample(
        "What is the weather in Dubai?",
        QueryClass.OUT_OF_DOMAIN,
        RouteHint.ABSTAIN,
    ),
    ClassifierExample(
        "How do I fix a Docker container?",
        QueryClass.OUT_OF_DOMAIN,
        RouteHint.ABSTAIN,
    ),
    ClassifierExample(
        "Explain the main point of this document.",
        QueryClass.GENERAL_QUESTION,
        RouteHint.MEDIUM,
    ),
    ClassifierExample(
        "How does this rule work?",
        QueryClass.GENERAL_QUESTION,
        RouteHint.MEDIUM,
    ),
    ClassifierExample(
        "What is the approval requirement?",
        QueryClass.OBLIGATION_QUESTION,
        RouteHint.MEDIUM,
    ),
    ClassifierExample(
        "What is the deadline for notification?",
        QueryClass.OBLIGATION_QUESTION,
        RouteHint.MEDIUM,
    ),
    ClassifierExample(
        "What is the difference between the notification requirement and the approval requirement?",
        QueryClass.COMPARISON_QUESTION,
        RouteHint.MEDIUM,
    ),
)


def main() -> None:
    failures = 0
    for example in EXAMPLES:
        result = classify_query(example.question)
        passed = (
            result.query_class == example.expected_class
            and result.route_hint == example.expected_route
        )
        status = "OK" if passed else "FAIL"
        if not passed:
            failures += 1

        print(
            f"{status} | expected={example.expected_class.value}/{example.expected_route.value} "
            f"actual={result.query_class.value}/{result.route_hint.value} | {example.question}"
        )
        print(f"     matched_rules={', '.join(result.matched_rules)}")

    if failures:
        raise SystemExit(f"{failures} classifier example(s) failed.")


if __name__ == "__main__":
    main()
