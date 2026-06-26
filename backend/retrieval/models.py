# Step 07 - Retrieval Models
#
# Role:
#   Define the structured evidence object returned by retrieval functions.
#
# Why this exists:
#   Later steps need consistent evidence fields for citations, prompts, and
#   diagnostics regardless of whether evidence came from BM25, vector, or hybrid
#   retrieval.
#
# Input:
#   OpenSearch hit dictionaries.
#
# Output:
#   RetrievalResult objects.

from pydantic import BaseModel


class RetrievalResult(BaseModel):
    rank: int
    score: float
    retrieval_method: str
    chunk_id: str
    document_id: int
    chunk_index: int
    title: str
    source_name: str
    source_url: str
    chunk_text: str
    publication_date: str | None = None
