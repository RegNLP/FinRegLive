# Step 08 - Generation Models
#
# Role:
#   Define structured answer output for source-grounded generation.
#
# Why this exists:
#   The backend should return predictable answer, source, and limitation fields
#   whether the answer is produced by a local fallback or an LLM.
#
# Input:
#   User question and retrieved evidence chunks.
#
# Output:
#   GroundedAnswer objects.

from pydantic import BaseModel


class AnswerSource(BaseModel):
    chunk_id: str
    title: str
    source_name: str
    source_url: str


class GroundedAnswer(BaseModel):
    question: str
    answer: str
    sources: list[AnswerSource]
    limitations: list[str]
