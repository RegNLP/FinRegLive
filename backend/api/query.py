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
#   POST /query with question, top_k, and use_llm.
#
# Output:
#   Grounded answer JSON with query_id, sources, and limitations.

from time import perf_counter

from fastapi import APIRouter, HTTPException
from opensearchpy.exceptions import ConnectionError as OpenSearchConnectionError
from opensearchpy.exceptions import NotFoundError, TransportError
from pydantic import BaseModel, Field, field_validator

from backend.database.crud import create_query_log
from backend.database.db import init_db
from backend.generation.answer import answer_question, answer_question_with_llm
from backend.generation.llm_client import LLMGenerationError, MissingOpenAIAPIKeyError
from backend.generation.models import GroundedAnswer

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=10)
    use_llm: bool = False

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        cleaned_value = value.strip()
        if len(cleaned_value) < 3:
            raise ValueError("Question must contain at least 3 non-space characters.")
        return cleaned_value


@router.post("/query", response_model=GroundedAnswer)
def query(request: QueryRequest) -> GroundedAnswer:
    init_db()

    started_at = perf_counter()
    answer_mode = "openai" if request.use_llm else "local"

    try:
        if request.use_llm:
            answer = answer_question_with_llm(request.question, top_k=request.top_k)
        else:
            answer = answer_question(request.question, top_k=request.top_k)
    except (OpenSearchConnectionError, NotFoundError, TransportError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Search service is unavailable or the chunk index is not ready.",
        ) from exc
    except MissingOpenAIAPIKeyError as exc:
        raise HTTPException(
            status_code=503,
            detail="OpenAI answer generation is not configured. Check OPENAI_API_KEY.",
        ) from exc
    except LLMGenerationError as exc:
        raise HTTPException(
            status_code=503,
            detail="OpenAI answer generation failed. Try local mode or retry later.",
        ) from exc

    latency_ms = int((perf_counter() - started_at) * 1000)
    query_log = create_query_log(
        query_text=request.question,
        retrieval_method="hybrid",
        answer_mode=answer_mode,
        top_k=request.top_k,
        retrieved_chunk_ids=[source.chunk_id for source in answer.sources],
        source_count=len(answer.sources),
        latency_ms=latency_ms,
    )

    return answer.model_copy(update={"query_id": query_log.id})
