# Step 18D - Route-Aware Answer Pipeline Tests
#
# Role:
#   Verify the first route-aware answer orchestrator.
#
# Why this exists:
#   The pipeline should use classifier and route policy decisions before it is
#   connected to the live `/query` API.
#
# Input:
#   Mocked retrieval results and representative questions.
#
# Output:
#   Passing pytest checks for routing, retrieval depth, reranking, diagnostics,
#   and abstention behavior.

from unittest.mock import patch

from backend.pipeline.route_aware_answer import (
    answer_question_route_aware,
    route_aware_answer_to_dict,
)
from backend.retrieval.models import RetrievalResult
from backend.routing.policy import RouteName


def make_result(
    chunk_id: str,
    document_id: int,
    rank: int,
    score: float,
    title: str,
    text: str,
) -> RetrievalResult:
    return RetrievalResult(
        rank=rank,
        score=score,
        retrieval_method="hybrid",
        chunk_id=chunk_id,
        document_id=document_id,
        chunk_index=0,
        title=title,
        source_name="FCA",
        source_url="https://example.com",
        chunk_text=text,
    )


def test_simple_route_uses_top_k_without_reranking() -> None:
    evidence = [
        make_result(
            "1",
            10,
            1,
            1.0,
            "Authorised Person definition",
            "An Authorised Person is a firm with financial services permission.",
        )
    ]

    with (
        patch(
            "backend.pipeline.route_aware_answer.retrieve_hybrid",
            return_value=evidence,
        ) as retrieve_hybrid,
        patch("backend.pipeline.route_aware_answer.rerank_lexical") as rerank_lexical,
    ):
        result = answer_question_route_aware("What is an Authorised Person?")

    retrieve_hybrid.assert_called_once_with("What is an Authorised Person?", top_k=3)
    rerank_lexical.assert_not_called()
    assert result.route_policy.route_name == RouteName.SIMPLE
    assert result.answer.sources[0].chunk_id == "1"


def test_medium_route_retrieves_candidates_and_reranks_to_top_k() -> None:
    candidates = [
        make_result(
            str(index),
            index,
            index,
            1.0 / index,
            "Notification requirements",
            "The firm must notify the regulator about notification requirements.",
        )
        for index in range(1, 21)
    ]
    reranked = candidates[:8]

    with (
        patch(
            "backend.pipeline.route_aware_answer.retrieve_hybrid",
            return_value=candidates,
        ) as retrieve_hybrid,
        patch(
            "backend.pipeline.route_aware_answer.rerank_lexical",
            return_value=reranked,
        ) as rerank_lexical,
    ):
        result = answer_question_route_aware(
            "What notification requirements apply to Authorised Persons?"
        )

    retrieve_hybrid.assert_called_once_with(
        "What notification requirements apply to Authorised Persons?",
        top_k=20,
    )
    rerank_lexical.assert_called_once()
    assert result.route_policy.route_name == RouteName.MEDIUM
    assert len(result.evidence) == 8


def test_out_of_domain_route_abstains_without_retrieval() -> None:
    with patch("backend.pipeline.route_aware_answer.retrieve_hybrid") as retrieve_hybrid:
        result = answer_question_route_aware("What is the weather in Dubai?")

    retrieve_hybrid.assert_not_called()
    assert result.route_policy.route_name == RouteName.ABSTAIN
    assert result.answer.answer == "The retrieved evidence is insufficient to answer this question."
    assert result.evidence == []


def test_complex_route_abstains_when_evidence_is_not_strong() -> None:
    weak_evidence = [
        make_result(
            "1",
            10,
            1,
            0.5,
            "Generic update",
            "This update mentions a regulator but has little relevant detail.",
        )
    ]

    with patch(
        "backend.pipeline.route_aware_answer.retrieve_hybrid",
        return_value=weak_evidence,
    ):
        result = answer_question_route_aware(
            "Does the firm need approval if its controller changes?"
        )

    assert result.route_policy.route_name == RouteName.COMPLEX
    assert result.answer.answer == "The retrieved evidence is insufficient to answer this question."
    assert "Evidence diagnostics" in result.answer.limitations[0]


def test_complex_route_answers_when_evidence_is_strong() -> None:
    strong_evidence = [
        make_result(
            "1",
            10,
            1,
            0.9,
            "Controller change approval",
            "The firm must notify the regulator and may need approval when its controller changes.",
        ),
        make_result(
            "2",
            11,
            2,
            0.8,
            "Approval conditions",
            "Approval is required under these conditions before the firm proceeds.",
        ),
        make_result(
            "3",
            12,
            3,
            0.7,
            "Regulator notification",
            "The firm should notify the regulator before a controller change.",
        ),
    ]

    with (
        patch(
            "backend.pipeline.route_aware_answer.retrieve_hybrid",
            return_value=strong_evidence,
        ),
        patch(
            "backend.pipeline.route_aware_answer.rerank_lexical",
            return_value=strong_evidence,
        ),
    ):
        result = answer_question_route_aware(
            "Does the firm need approval if its controller changes?"
        )

    assert result.route_policy.route_name == RouteName.COMPLEX
    assert result.answer.sources
    assert result.answer.answer.startswith("Based on the retrieved evidence")


def test_route_aware_answer_serializes_metadata() -> None:
    evidence = [
        make_result(
            "1",
            10,
            1,
            1.0,
            "Authorised Person definition",
            "An Authorised Person is a firm with financial services permission.",
        )
    ]

    with patch(
        "backend.pipeline.route_aware_answer.retrieve_hybrid",
        return_value=evidence,
    ):
        result = answer_question_route_aware("What is an Authorised Person?")

    payload = route_aware_answer_to_dict(result)

    assert payload["classification"]["query_class"] == "definition_lookup"
    assert payload["route_policy"]["route_name"] == "simple"
    assert payload["evidence_diagnostics"]["evidence_strength"] == "strong"
    assert payload["evidence_chunk_ids"] == ["1"]
