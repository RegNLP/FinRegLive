# Step 14 - Corpus Analytics API Route
#
# Role:
#   Summarize corpus size, source coverage, and text length statistics.
#
# Why this exists:
#   A RAG system needs observability. Total document counts are useful, but we
#   also need to know which sources dominate the corpus and how large documents
#   and chunks are.
#
# Input:
#   GET /analytics/corpus.
#
# Output:
#   Corpus-level and source-level analytics for documents and chunks.

from collections import defaultdict
import json
from statistics import mean

from fastapi import APIRouter
from pydantic import BaseModel

from backend.database.crud import list_chunks, list_documents, list_ingestion_runs
from backend.database.db import init_db

router = APIRouter(tags=["analytics"])


class LengthStats(BaseModel):
    min_chars: int
    max_chars: int
    avg_chars: float
    min_words: int
    max_words: int
    avg_words: float


class SourceCorpusAnalytics(BaseModel):
    source_name: str
    document_count: int
    chunk_count: int
    avg_document_words: float
    avg_chunk_words: float
    latest_document_created_at: str | None


class IngestionRunAnalytics(BaseModel):
    id: int
    source_key: str
    days: int
    limit: int
    status: str
    fetched_documents: int
    stored: int
    duplicates: int
    chunks_created: int
    chunks_indexed: int
    source_failures: list[str]
    duration_ms: int | None
    started_at: str
    finished_at: str | None


class CorpusAnalyticsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    document_length_stats: LengthStats
    chunk_length_stats: LengthStats
    sources: list[SourceCorpusAnalytics]
    recent_ingestion_runs: list[IngestionRunAnalytics]


def build_length_stats(texts: list[str]) -> LengthStats:
    char_lengths = [len(text) for text in texts]
    word_lengths = [len(text.split()) for text in texts]

    if not texts:
        return LengthStats(
            min_chars=0,
            max_chars=0,
            avg_chars=0,
            min_words=0,
            max_words=0,
            avg_words=0,
        )

    return LengthStats(
        min_chars=min(char_lengths),
        max_chars=max(char_lengths),
        avg_chars=round(mean(char_lengths), 2),
        min_words=min(word_lengths),
        max_words=max(word_lengths),
        avg_words=round(mean(word_lengths), 2),
    )


@router.get("/analytics/corpus", response_model=CorpusAnalyticsResponse)
def corpus_analytics() -> CorpusAnalyticsResponse:
    init_db()
    documents = list_documents()
    chunks = list_chunks()

    documents_by_id = {document.id: document for document in documents}
    source_documents = defaultdict(list)
    source_chunks = defaultdict(list)

    for document in documents:
        source_documents[document.source_name].append(document)

    for chunk in chunks:
        document = documents_by_id.get(chunk.document_id)
        if document is not None:
            source_chunks[document.source_name].append(chunk)

    source_rows = []
    for source_name, source_document_rows in source_documents.items():
        source_chunk_rows = source_chunks[source_name]
        document_word_lengths = [len((document.text or "").split()) for document in source_document_rows]
        chunk_word_lengths = [len((chunk.text or "").split()) for chunk in source_chunk_rows]
        latest_created_at = max(document.created_at for document in source_document_rows)

        source_rows.append(
            SourceCorpusAnalytics(
                source_name=source_name,
                document_count=len(source_document_rows),
                chunk_count=len(source_chunk_rows),
                avg_document_words=round(mean(document_word_lengths), 2)
                if document_word_lengths
                else 0,
                avg_chunk_words=round(mean(chunk_word_lengths), 2) if chunk_word_lengths else 0,
                latest_document_created_at=latest_created_at.isoformat(),
            )
        )

    source_rows.sort(key=lambda row: row.document_count, reverse=True)
    ingestion_runs = []

    for run in list_ingestion_runs(limit=10):
        try:
            source_failures = json.loads(run.source_failures)
        except json.JSONDecodeError:
            source_failures = []

        ingestion_runs.append(
            IngestionRunAnalytics(
                id=run.id,
                source_key=run.source_key,
                days=run.days,
                limit=run.limit,
                status=run.status,
                fetched_documents=run.fetched_documents,
                stored=run.stored,
                duplicates=run.duplicates,
                chunks_created=run.chunks_created,
                chunks_indexed=run.chunks_indexed,
                source_failures=source_failures,
                duration_ms=run.duration_ms,
                started_at=run.started_at.isoformat(),
                finished_at=run.finished_at.isoformat() if run.finished_at else None,
            )
        )

    return CorpusAnalyticsResponse(
        total_documents=len(documents),
        total_chunks=len(chunks),
        document_length_stats=build_length_stats([document.text or "" for document in documents]),
        chunk_length_stats=build_length_stats([chunk.text or "" for chunk in chunks]),
        sources=source_rows,
        recent_ingestion_runs=ingestion_runs,
    )
