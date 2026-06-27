# Step 18B - Route Question CLI
#
# Role:
#   Show query classification and selected route policy for one question.
#
# Why this exists:
#   Route policy is easier to learn and debug when we can inspect the full
#   classifier-to-route decision from the terminal.
#
# Input:
#   A user question string.
#
# Output:
#   JSON with classification details and selected route policy.

import argparse
import json

from backend.routing.classifier import classification_to_dict, classify_query
from backend.routing.policy import get_route_for_classification, route_policy_to_dict


def route_question(question: str) -> dict[str, object]:
    classification = classify_query(question)
    policy = get_route_for_classification(classification)

    return {
        "question": question,
        "classification": classification_to_dict(classification),
        "route_policy": route_policy_to_dict(policy),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify and route a question.")
    parser.add_argument("question")
    args = parser.parse_args()

    print(json.dumps(route_question(args.question), indent=2))


if __name__ == "__main__":
    main()
