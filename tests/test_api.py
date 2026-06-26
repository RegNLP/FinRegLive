# Step 11B - API Tests
#
# Role:
#   Verify important FastAPI routes, validation rules, and service error
#   handling.
#
# Why this exists:
#   The API is the contract used by the Streamlit frontend and future clients.
#   These tests protect request validation and friendly error responses without
#   requiring real OpenSearch or OpenAI calls.
#
# Input:
#   TestClient HTTP requests with mocked route dependencies.
#
# Output:
#   Passing pytest checks for status codes and response shapes.

from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from opensearchpy.exceptions import ConnectionError as OpenSearchConnectionError

from backend.generation.llm_client import MissingOpenAIAPIKeyError
from backend.generation.models import AnswerSource, GroundedAnswer
from backend.main import app


client = TestClient(app)


def sample_answer() -> GroundedAnswer:
    return GroundedAnswer(
        question="What did regulators publish?",
        answer="They published a request for public comment.",
        sources=[
            AnswerSource(
                chunk_id="1",
                title="SEC and CFTC update",
                source_name="SEC",
                source_url="https://example.com/sec-cftc",
            )
        ],
        limitations=["This answer is generated only from retrieved evidence."],
    )


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_query_rejects_blank_question() -> None:
    response = client.post(
        "/query",
        json={"question": "   ", "top_k": 2, "use_llm": False},
    )

    assert response.status_code == 422


def test_query_returns_answer_and_query_id() -> None:
    with (
        patch("backend.api.query.init_db"),
        patch("backend.api.query.answer_question", return_value=sample_answer()),
        patch("backend.api.query.create_query_log", return_value=SimpleNamespace(id=42)),
    ):
        response = client.post(
            "/query",
            json={"question": "What did regulators publish?", "top_k": 2, "use_llm": False},
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["query_id"] == 42
    assert payload["sources"][0]["chunk_id"] == "1"


def test_query_returns_503_when_search_is_unavailable() -> None:
    with (
        patch("backend.api.query.init_db"),
        patch(
            "backend.api.query.answer_question",
            side_effect=OpenSearchConnectionError("N/A", "unavailable", Exception("down")),
        ),
    ):
        response = client.post(
            "/query",
            json={"question": "What changed?", "top_k": 2, "use_llm": False},
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Search service is unavailable or the chunk index is not ready."
    }


def test_query_returns_503_when_openai_key_is_missing() -> None:
    with (
        patch("backend.api.query.init_db"),
        patch(
            "backend.api.query.answer_question_with_llm",
            side_effect=MissingOpenAIAPIKeyError("missing"),
        ),
    ):
        response = client.post(
            "/query",
            json={"question": "What changed?", "top_k": 2, "use_llm": True},
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "OpenAI answer generation is not configured. Check OPENAI_API_KEY."
    }


def test_feedback_rejects_unknown_label() -> None:
    response = client.post(
        "/feedback",
        json={
            "query_id": 1,
            "useful_label": "bad_value",
            "correctness_label": "correct",
            "evidence_label": "supported",
        },
    )

    assert response.status_code == 422


def test_feedback_stores_for_existing_query() -> None:
    with (
        patch("backend.api.feedback.init_db"),
        patch("backend.api.feedback.get_query_log", return_value=SimpleNamespace(id=7)),
        patch(
            "backend.api.feedback.create_feedback",
            return_value=SimpleNamespace(id=99, query_id=7),
        ),
    ):
        response = client.post(
            "/feedback",
            json={
                "query_id": 7,
                "useful_label": "useful",
                "correctness_label": "correct",
                "evidence_label": "supported",
            },
        )

    assert response.status_code == 200
    assert response.json() == {"feedback_id": 99, "query_id": 7, "status": "stored"}
