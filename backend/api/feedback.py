# Step 09C - Feedback API Route
#
# Role:
#   Store user feedback for a saved query.
#
# Why this exists:
#   A RAG system needs feedback to learn which answers were useful, correct,
#   and supported by evidence. Feedback must connect to a query_id so we know
#   which question, answer mode, and retrieved chunks the user evaluated.
#
# Input:
#   POST /feedback with query_id, useful_label, correctness_label,
#   evidence_label, and optional note.
#
# Output:
#   Stored feedback metadata with a feedback ID.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.database.crud import create_feedback, get_query_log
from backend.database.db import init_db

router = APIRouter(tags=["feedback"])


class FeedbackRequest(BaseModel):
    query_id: int = Field(gt=0)
    useful_label: str = Field(min_length=1)
    correctness_label: str = Field(min_length=1)
    evidence_label: str = Field(min_length=1)
    note: str | None = None


class FeedbackResponse(BaseModel):
    feedback_id: int
    query_id: int
    status: str


@router.post("/feedback", response_model=FeedbackResponse)
def feedback(request: FeedbackRequest) -> FeedbackResponse:
    init_db()

    if get_query_log(request.query_id) is None:
        raise HTTPException(status_code=404, detail="query_id was not found")

    saved_feedback = create_feedback(
        query_id=request.query_id,
        useful_label=request.useful_label,
        correctness_label=request.correctness_label,
        evidence_label=request.evidence_label,
        note=request.note,
    )

    return FeedbackResponse(
        feedback_id=saved_feedback.id,
        query_id=saved_feedback.query_id,
        status="stored",
    )
