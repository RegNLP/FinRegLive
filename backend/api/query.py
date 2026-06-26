# Step 09A - Query API Route
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
#   Grounded answer JSON with sources and limitations.

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.generation.answer import answer_question, answer_question_with_llm
from backend.generation.models import GroundedAnswer

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=10)
    use_llm: bool = False


@router.post("/query", response_model=GroundedAnswer)
def query(request: QueryRequest) -> GroundedAnswer:
    if request.use_llm:
        return answer_question_with_llm(request.question, top_k=request.top_k)

    return answer_question(request.question, top_k=request.top_k)
