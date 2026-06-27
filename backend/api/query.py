# Step 09A/09B - Query API Route and Query Logging
#
# Role:
#   Expose the RAG question-answering flow as a FastAPI endpoint.
#
# Why this exists:
#   Terminal scripts are useful for development, but applications need API
#   endpoints. This route lets a client send a question and receive a structured
#   grounded answer.
#
# Input:
#   POST /query with question.
#
# Output:
#   Grounded answer JSON with route metadata, query_id, sources, and limitations.

from time import perf_counter
from typing import Any

from fastapi import APIRouter, HTTPException
from opensearchpy.exceptions import ConnectionError as OpenSearchConnectionError
from opensearchpy.exceptions import NotFoundError, TransportError
from pydantic import BaseModel, Field, field_validator

from backend.database.crud import create_query_log
from backend.database.db import init_db
from backend.generation.models import AnswerSource
from backend.pipeline.route_aware_answer import (
    answer_question_route_aware,
    route_aware_answer_to_dict,
)

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        cleaned_value = value.strip()
        if len(cleaned_value) < 3:
            raise ValueError("Question must contain at least 3 non-space characters.")
        return cleaned_value


class QueryResponse(BaseModel):
    query_id: int | None = None
    question: str
    answer: str
    sources: list[AnswerSource]
    limitations: list[str]
    classification: dict[str, Any]
    route_policy: dict[str, Any]
    evidence_diagnostics: dict[str, Any]
    evidence_chunk_ids: list[str]


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    init_db()

    started_at = perf_counter()
    try:
        route_aware_result = answer_question_route_aware(request.question)
    except (OpenSearchConnectionError, NotFoundError, TransportError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Search service is unavailable or the chunk index is not ready.",
        ) from exc

    latency_ms = int((perf_counter() - started_at) * 1000)
    answer = route_aware_result.answer
    query_log = create_query_log(
        query_text=request.question,
        retrieval_method=route_aware_result.route_policy.route_name.value,
        answer_mode=route_aware_result.route_policy.generation_mode.value,
        top_k=route_aware_result.route_policy.top_k,
        retrieved_chunk_ids=[source.chunk_id for source in answer.sources],
        source_count=len(answer.sources),
        latency_ms=latency_ms,
    )

    payload = route_aware_answer_to_dict(route_aware_result)
    payload["answer"]["query_id"] = query_log.id

    return QueryResponse(
        **payload["answer"],
        classification=payload["classification"],
        route_policy=payload["route_policy"],
        evidence_diagnostics=payload["evidence_diagnostics"],
        evidence_chunk_ids=payload["evidence_chunk_ids"],
    )
