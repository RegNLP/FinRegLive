# Step 15 - Retrieval Diagnostics API Route
#
# Role:
#   Compare BM25, vector, and hybrid retrieval for the same question.
#
# Why this exists:
#   Before improving retrieval, we need to see what each retrieval method is
#   returning and where the methods agree or disagree.
#
# Input:
#   POST /retrieval/diagnostics with question and top_k.
#
# Output:
#   BM25, vector, hybrid results, plus overlap counts between methods.

from fastapi import APIRouter, HTTPException
from opensearchpy.exceptions import ConnectionError as OpenSearchConnectionError
from opensearchpy.exceptions import NotFoundError, TransportError
from pydantic import BaseModel, Field, field_validator

from backend.retrieval.bm25 import retrieve_bm25
from backend.retrieval.hybrid import retrieve_hybrid
from backend.retrieval.models import RetrievalResult
from backend.retrieval.vector import retrieve_vector

router = APIRouter(tags=["retrieval"])


class RetrievalDiagnosticsRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        cleaned_value = value.strip()
        if len(cleaned_value) < 3:
            raise ValueError("Question must contain at least 3 non-space characters.")
        return cleaned_value


class RetrievalOverlap(BaseModel):
    bm25_vector: int
    bm25_hybrid: int
    vector_hybrid: int
    all_methods: int


class RetrievalDiagnosticsResponse(BaseModel):
    question: str
    top_k: int
    bm25: list[RetrievalResult]
    vector: list[RetrievalResult]
    hybrid: list[RetrievalResult]
    overlap: RetrievalOverlap


def chunk_ids(results: list[RetrievalResult]) -> set[str]:
    return {result.chunk_id for result in results}


@router.post("/retrieval/diagnostics", response_model=RetrievalDiagnosticsResponse)
def retrieval_diagnostics(
    request: RetrievalDiagnosticsRequest,
) -> RetrievalDiagnosticsResponse:
    try:
        bm25_results = retrieve_bm25(request.question, top_k=request.top_k)
        vector_results = retrieve_vector(request.question, top_k=request.top_k)
        hybrid_results = retrieve_hybrid(request.question, top_k=request.top_k)
    except (OpenSearchConnectionError, NotFoundError, TransportError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Search service is unavailable or the chunk index is not ready.",
        ) from exc

    bm25_ids = chunk_ids(bm25_results)
    vector_ids = chunk_ids(vector_results)
    hybrid_ids = chunk_ids(hybrid_results)

    return RetrievalDiagnosticsResponse(
        question=request.question,
        top_k=request.top_k,
        bm25=bm25_results,
        vector=vector_results,
        hybrid=hybrid_results,
        overlap=RetrievalOverlap(
            bm25_vector=len(bm25_ids & vector_ids),
            bm25_hybrid=len(bm25_ids & hybrid_ids),
            vector_hybrid=len(vector_ids & hybrid_ids),
            all_methods=len(bm25_ids & vector_ids & hybrid_ids),
        ),
    )
