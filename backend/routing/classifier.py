# Step 18A - Rule-Based Query Classifier
#
# Role:
#   Classify a user question before route policy is selected.
#
# Why this exists:
#   Simple definitions, obligation questions, comparisons, high-risk compliance
#   questions, and out-of-domain questions should not all use the same RAG path.
#   A deterministic classifier gives us a cheap, explainable first routing layer.
#
# Input:
#   A user question string.
#
# Output:
#   QueryClassification with query class, confidence, matched rules, and route hint.

import argparse
import json
from dataclasses import dataclass
from enum import Enum


class QueryClass(str, Enum):
    DEFINITION_LOOKUP = "definition_lookup"
    OBLIGATION_QUESTION = "obligation_question"
    COMPARISON_QUESTION = "comparison_question"
    MULTI_HOP_CROSS_REFERENCE = "multi_hop_cross_reference"
    COMPLIANCE_DECISION = "compliance_decision"
    OUT_OF_DOMAIN = "out_of_domain"
    GENERAL_QUESTION = "general_question"


class RouteHint(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class QueryClassification:
    query_class: QueryClass
    confidence: float
    matched_rules: tuple[str, ...]
    route_hint: RouteHint


@dataclass(frozen=True)
class RuleGroup:
    query_class: QueryClass
    route_hint: RouteHint
    confidence: float
    phrases: tuple[str, ...]
    keywords: tuple[str, ...]


OUT_OF_DOMAIN_RULES = RuleGroup(
    query_class=QueryClass.OUT_OF_DOMAIN,
    route_hint=RouteHint.ABSTAIN,
    confidence=0.95,
    phrases=(
        "blackheads",
        "docker and kubernetes",
        "fifa world cup",
        "kubernetes",
        "lentil soup",
        "recipe",
        "skincare",
        "turkish lentil",
        "vitamin d",
        "weather in",
    ),
    keywords=(
        "blackheads",
        "cooking",
        "docker",
        "fifa",
        "kubernetes",
        "recipe",
        "skincare",
        "soup",
        "symptoms",
        "vitamin",
        "weather",
    ),
)

COMPLIANCE_DECISION_RULES = RuleGroup(
    query_class=QueryClass.COMPLIANCE_DECISION,
    route_hint=RouteHint.COMPLEX,
    confidence=0.90,
    phrases=(
        "approval required",
        "can the firm",
        "can the firm rely",
        "can the firm proceed",
        "confidential",
        "definitive legal opinion",
        "does the firm need",
        "fully compliant",
        "is approval required",
        "is this compliant",
        "legal opinion",
        "make a reasonable guess",
        "most likely",
        "need approval",
        "need to notify",
        "next month",
        "rely on an exemption",
        "required under these conditions",
        "sources are unrelated",
        "under these conditions",
        "without notifying",
    ),
    keywords=(),
)

COMPARISON_RULES = RuleGroup(
    query_class=QueryClass.COMPARISON_QUESTION,
    route_hint=RouteHint.MEDIUM,
    confidence=0.88,
    phrases=(
        "compare",
        "contrast",
        "difference between",
        "different ones",
        "do these two",
        "how do they differ",
        "how do these two",
        "similar regulatory topics",
        "similar or different",
        "versus",
    ),
    keywords=(
        "compare",
        "contrast",
        "difference",
        "differences",
        "differ",
        "versus",
        "vs",
    ),
)

OBLIGATION_RULES = RuleGroup(
    query_class=QueryClass.OBLIGATION_QUESTION,
    route_hint=RouteHint.MEDIUM,
    confidence=0.86,
    phrases=(
        "duties apply",
        "must comply",
        "must report",
        "need to notify",
        "notification requirements",
        "obligations apply",
        "reporting duties",
        "reporting obligations",
        "required to notify",
        "what obligations",
        "what requirements",
    ),
    keywords=(
        "duties",
        "duty",
        "must",
        "notification",
        "notify",
        "obligation",
        "obligations",
        "reporting",
        "requirement",
        "requirements",
    ),
)

MULTI_HOP_RULES = RuleGroup(
    query_class=QueryClass.MULTI_HOP_CROSS_REFERENCE,
    route_hint=RouteHint.COMPLEX,
    confidence=0.84,
    phrases=(
        "across sources",
        "across the retrieved documents",
        "available sources suggest",
        "cross reference",
        "cross-reference",
        "from multiple documents",
        "most active",
        "read together",
        "recent trend",
        "section x and y",
        "themes appear",
    ),
    keywords=(
        "across",
        "documents",
        "multi",
        "multiple",
        "sections",
        "section",
        "sources",
        "themes",
        "trend",
    ),
)

DEFINITION_RULES = RuleGroup(
    query_class=QueryClass.DEFINITION_LOOKUP,
    route_hint=RouteHint.SIMPLE,
    confidence=0.82,
    phrases=(
        "define",
        "meaning of",
        "what does",
        "what is a",
        "what is an",
        "what is the meaning",
    ),
    keywords=(
        "define",
        "definition",
        "meaning",
    ),
)

RULE_PRIORITY = (
    OUT_OF_DOMAIN_RULES,
    COMPLIANCE_DECISION_RULES,
    MULTI_HOP_RULES,
    COMPARISON_RULES,
    OBLIGATION_RULES,
    DEFINITION_RULES,
)


def normalize_question(question: str) -> str:
    return " ".join(question.lower().strip().split())


def tokenize_for_rules(question: str) -> set[str]:
    normalized = normalize_question(question)
    return {
        token.strip(".,;:!?()[]{}\"'")
        for token in normalized.split()
        if token.strip(".,;:!?()[]{}\"'")
    }


def matched_rule_names(question: str, rule_group: RuleGroup) -> list[str]:
    normalized = normalize_question(question)
    padded_normalized = f" {normalized} "
    tokens = tokenize_for_rules(question)
    matches: list[str] = []

    for phrase in rule_group.phrases:
        if f" {phrase} " in padded_normalized:
            matches.append(f"phrase:{phrase}")

    for keyword in rule_group.keywords:
        if keyword in tokens:
            matches.append(f"keyword:{keyword}")

    return matches


def classify_query(question: str) -> QueryClassification:
    for rule_group in RULE_PRIORITY:
        matches = matched_rule_names(question, rule_group)
        if matches:
            return QueryClassification(
                query_class=rule_group.query_class,
                confidence=rule_group.confidence,
                matched_rules=tuple(matches),
                route_hint=rule_group.route_hint,
            )

    return QueryClassification(
        query_class=QueryClass.GENERAL_QUESTION,
        confidence=0.35,
        matched_rules=("fallback:no_specific_rule_matched",),
        route_hint=RouteHint.MEDIUM,
    )


def classification_to_dict(classification: QueryClassification) -> dict[str, object]:
    return {
        "query_class": classification.query_class.value,
        "confidence": classification.confidence,
        "matched_rules": classification.matched_rules,
        "route_hint": classification.route_hint.value,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify a user question.")
    parser.add_argument("question")
    args = parser.parse_args()

    classification = classify_query(args.question)
    print(json.dumps(classification_to_dict(classification), indent=2))


if __name__ == "__main__":
    main()
