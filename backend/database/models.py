# Step 03 - Database Models
#
# Role:
#   Define the database tables used by the local application.
#
# Why this exists:
#   The RAG system must remember ingested documents, document chunks, user
#   queries, and feedback. These models describe the shape of that stored data.
#
# Input:
#   Python values passed when creating Document, Chunk, QueryLog, or Feedback
#   records.
#
# Output:
#   SQLModel table definitions that can be created in SQLite.

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Document(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    source_name: str
    source_url: str
    text: str = ""
    content_hash: str = Field(index=True, unique=True)
    publication_date: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class Chunk(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    document_id: int = Field(index=True)
    chunk_index: int
    text: str
    created_at: datetime = Field(default_factory=utc_now)


class QueryLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    query_text: str
    retrieval_method: str
    answer_mode: str = "local"
    top_k: int = 5
    retrieved_chunk_ids: str = "[]"
    source_count: int = 0
    latency_ms: int | None = None
    created_at: datetime = Field(default_factory=utc_now)


class Feedback(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    query_id: int
    useful_label: str
    correctness_label: str
    evidence_label: str
    note: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class IngestionRun(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    source_key: str
    days: int
    limit: int
    status: str
    fetched_documents: int = 0
    stored: int = 0
    duplicates: int = 0
    documents_processed: int = 0
    chunks_created: int = 0
    chunks_indexed: int = 0
    source_failures: str = "[]"
    duration_ms: int | None = None
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
