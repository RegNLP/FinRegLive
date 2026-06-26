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

from backend.database.models import Chunk, Document
from backend.generation.llm_client import MissingOpenAIAPIKeyError
from backend.generation.models import AnswerSource, GroundedAnswer
from backend.main import app
from backend.retrieval.models import RetrievalResult


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


def test_query_can_use_reranking() -> None:
    with (
        patch("backend.api.query.init_db"),
        patch("backend.api.query.answer_question", return_value=sample_answer()) as answer_question,
        patch("backend.api.query.create_query_log", return_value=SimpleNamespace(id=42)) as create_query_log,
    ):
        response = client.post(
            "/query",
            json={
                "question": "What did regulators publish?",
                "top_k": 2,
                "use_llm": False,
                "use_reranking": True,
            },
        )

    assert response.status_code == 200
    answer_question.assert_called_once_with(
        "What did regulators publish?",
        top_k=2,
        use_reranking=True,
    )
    assert create_query_log.call_args.kwargs["retrieval_method"] == "hybrid_reranked"


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


def sample_document() -> Document:
    return Document(
        id=7,
        title="Sample SEC Update",
        source_name="SEC",
        source_url="https://example.com/sec",
        text="Sample regulatory update text.",
        content_hash="sample-hash",
        publication_date="2026-06-25",
    )


def sample_chunk() -> Chunk:
    return Chunk(
        id=11,
        document_id=7,
        chunk_index=0,
        text="Sample regulatory update text.",
    )


def sample_retrieval_result(chunk_id: str, method: str) -> RetrievalResult:
    return RetrievalResult(
        rank=1,
        score=1.0,
        retrieval_method=method,
        chunk_id=chunk_id,
        document_id=7,
        chunk_index=0,
        title="Sample SEC Update",
        source_name="SEC",
        source_url="https://example.com/sec",
        chunk_text="Sample regulatory update text.",
    )


def test_documents_lists_document_summaries() -> None:
    with (
        patch("backend.api.documents.init_db"),
        patch("backend.api.documents.list_documents", return_value=[sample_document()]),
        patch("backend.api.documents.get_chunks_for_document", return_value=[sample_chunk()]),
    ):
        response = client.get("/documents")

    payload = response.json()
    assert response.status_code == 200
    assert payload[0]["id"] == 7
    assert payload[0]["chunk_count"] == 1
    assert payload[0]["text_length"] == len("Sample regulatory update text.")


def test_document_detail_returns_text_and_chunks() -> None:
    with (
        patch("backend.api.documents.init_db"),
        patch("backend.api.documents.get_document", return_value=sample_document()),
        patch("backend.api.documents.get_chunks_for_document", return_value=[sample_chunk()]),
    ):
        response = client.get("/documents/7")

    payload = response.json()
    assert response.status_code == 200
    assert payload["id"] == 7
    assert payload["text"] == "Sample regulatory update text."
    assert payload["chunks"][0]["id"] == 11


def test_document_detail_returns_404_for_missing_document() -> None:
    with (
        patch("backend.api.documents.init_db"),
        patch("backend.api.documents.get_document", return_value=None),
    ):
        response = client.get("/documents/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "document_id was not found"}


def test_recent_updates_lists_document_summaries() -> None:
    with (
        patch("backend.api.documents.init_db"),
        patch("backend.api.documents.list_documents", return_value=[sample_document()]),
        patch("backend.api.documents.get_chunks_for_document", return_value=[sample_chunk()]),
    ):
        response = client.get("/recent-updates")

    payload = response.json()
    assert response.status_code == 200
    assert payload[0]["title"] == "Sample SEC Update"


def test_recent_ingestion_endpoint_returns_summary() -> None:
    with patch("backend.api.ingestion.ingest_recent_sources") as ingest_recent_sources:
        ingest_recent_sources.return_value = {
            "days": 7,
            "source_keys": ["sec_press"],
            "fetched_documents": 2,
            "recent_documents": 2,
            "stored": 1,
            "duplicates": 1,
            "documents_processed": 1,
            "chunks_created": 3,
            "chunks_indexed": 10,
            "html_snapshots": 0,
            "source_failures": [],
        }

        response = client.post(
            "/ingest/recent",
            json={"days": 7, "source": "sec_press", "limit": 2, "recreate_index": True},
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["stored"] == 1
    assert payload["chunks_indexed"] == 10


def test_recent_ingestion_endpoint_rejects_unknown_source() -> None:
    response = client.post(
        "/ingest/recent",
        json={"days": 7, "source": "unknown", "limit": 2, "recreate_index": True},
    )

    assert response.status_code == 422


def test_corpus_analytics_returns_source_and_length_stats() -> None:
    document = sample_document()
    chunk = sample_chunk()

    with (
        patch("backend.api.analytics.init_db"),
        patch("backend.api.analytics.list_documents", return_value=[document]),
        patch("backend.api.analytics.list_chunks", return_value=[chunk]),
        patch("backend.api.analytics.list_ingestion_runs", return_value=[]),
    ):
        response = client.get("/analytics/corpus")

    payload = response.json()
    assert response.status_code == 200
    assert payload["total_documents"] == 1
    assert payload["total_chunks"] == 1
    assert payload["document_length_stats"]["min_words"] == 4
    assert payload["sources"][0]["source_name"] == "SEC"
    assert payload["sources"][0]["document_count"] == 1
    assert payload["sources"][0]["chunk_count"] == 1
    assert payload["recent_ingestion_runs"] == []


def test_retrieval_diagnostics_returns_method_results_and_overlap() -> None:
    with (
        patch(
            "backend.api.retrieval_diagnostics.retrieve_bm25",
            return_value=[sample_retrieval_result("1", "bm25")],
        ),
        patch(
            "backend.api.retrieval_diagnostics.retrieve_vector",
            return_value=[sample_retrieval_result("1", "vector")],
        ),
        patch(
            "backend.api.retrieval_diagnostics.retrieve_hybrid",
            return_value=[sample_retrieval_result("1", "hybrid")],
        ),
    ):
        response = client.post(
            "/retrieval/diagnostics",
            json={"question": "What changed?", "top_k": 3},
        )

    payload = response.json()
    assert response.status_code == 200
    assert payload["bm25"][0]["chunk_id"] == "1"
    assert payload["vector"][0]["chunk_id"] == "1"
    assert payload["hybrid"][0]["chunk_id"] == "1"
    assert payload["overlap"]["all_methods"] == 1


def test_retrieval_diagnostics_rejects_blank_question() -> None:
    response = client.post(
        "/retrieval/diagnostics",
        json={"question": "  ", "top_k": 3},
    )

    assert response.status_code == 422
