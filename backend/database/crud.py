# Step 03 - Database CRUD Helpers
#
# Role:
#   Provide small functions for creating and reading database records.
#
# Why this exists:
#   API routes and pipeline code should not write raw SQL each time they need
#   to store or fetch data. This file centralizes common database operations.
#
# Input:
#   Python values such as document title, source URL, and content hash.
#
# Output:
#   Stored SQLModel objects returned from the SQLite database.

import json

from sqlmodel import Session, func, select

from backend.database.db import engine
from backend.database.models import Chunk, Document, Feedback, IngestionRun, QueryLog, utc_now


def get_document_by_hash(content_hash: str) -> Document | None:
    with Session(engine) as session:
        statement = select(Document).where(Document.content_hash == content_hash)
        return session.exec(statement).first()


def create_document(
    title: str,
    source_name: str,
    source_url: str,
    text: str,
    content_hash: str,
    publication_date: str | None = None,
) -> Document:
    document = Document(
        title=title,
        source_name=source_name,
        source_url=source_url,
        text=text,
        content_hash=content_hash,
        publication_date=publication_date,
    )

    with Session(engine) as session:
        session.add(document)
        session.commit()
        session.refresh(document)
        return document


def get_document(document_id: int) -> Document | None:
    with Session(engine) as session:
        return session.get(Document, document_id)


def update_document_text(document_id: int, text: str) -> Document | None:
    with Session(engine) as session:
        document = session.get(Document, document_id)
        if document is None:
            return None

        document.text = text
        session.add(document)
        session.commit()
        session.refresh(document)
        return document


def list_documents() -> list[Document]:
    with Session(engine) as session:
        statement = select(Document).order_by(Document.created_at.desc())
        return list(session.exec(statement))


def list_documents_with_text() -> list[Document]:
    with Session(engine) as session:
        statement = select(Document).where(Document.text != "").order_by(Document.created_at.desc())
        return list(session.exec(statement))


def get_chunks_for_document(document_id: int) -> list[Chunk]:
    with Session(engine) as session:
        statement = select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index)
        return list(session.exec(statement))


def list_chunks() -> list[Chunk]:
    with Session(engine) as session:
        statement = select(Chunk).order_by(Chunk.document_id, Chunk.chunk_index)
        return list(session.exec(statement))


def create_chunk(document_id: int, chunk_index: int, text: str) -> Chunk:
    chunk = Chunk(document_id=document_id, chunk_index=chunk_index, text=text)

    with Session(engine) as session:
        session.add(chunk)
        session.commit()
        session.refresh(chunk)
        return chunk


def create_query_log(
    query_text: str,
    retrieval_method: str,
    answer_mode: str,
    top_k: int,
    retrieved_chunk_ids: list[str],
    source_count: int,
    latency_ms: int | None = None,
) -> QueryLog:
    query_log = QueryLog(
        query_text=query_text,
        retrieval_method=retrieval_method,
        answer_mode=answer_mode,
        top_k=top_k,
        retrieved_chunk_ids=json.dumps(retrieved_chunk_ids),
        source_count=source_count,
        latency_ms=latency_ms,
    )

    with Session(engine) as session:
        session.add(query_log)
        session.commit()
        session.refresh(query_log)
        return query_log


def list_query_logs() -> list[QueryLog]:
    with Session(engine) as session:
        statement = select(QueryLog).order_by(QueryLog.created_at.desc())
        return list(session.exec(statement))


def get_query_log(query_id: int) -> QueryLog | None:
    with Session(engine) as session:
        return session.get(QueryLog, query_id)


def create_feedback(
    query_id: int,
    useful_label: str,
    correctness_label: str,
    evidence_label: str,
    note: str | None = None,
) -> Feedback:
    feedback = Feedback(
        query_id=query_id,
        useful_label=useful_label,
        correctness_label=correctness_label,
        evidence_label=evidence_label,
        note=note,
    )

    with Session(engine) as session:
        session.add(feedback)
        session.commit()
        session.refresh(feedback)
        return feedback


def list_feedback() -> list[Feedback]:
    with Session(engine) as session:
        statement = select(Feedback).order_by(Feedback.created_at.desc())
        return list(session.exec(statement))


def create_ingestion_run(
    source_key: str,
    days: int,
    limit: int,
    status: str = "running",
) -> IngestionRun:
    ingestion_run = IngestionRun(
        source_key=source_key,
        days=days,
        limit=limit,
        status=status,
    )

    with Session(engine) as session:
        session.add(ingestion_run)
        session.commit()
        session.refresh(ingestion_run)
        return ingestion_run


def complete_ingestion_run(
    ingestion_run_id: int,
    status: str,
    fetched_documents: int,
    stored: int,
    duplicates: int,
    documents_processed: int,
    chunks_created: int,
    chunks_indexed: int,
    source_failures: list[str],
    duration_ms: int,
) -> IngestionRun | None:
    with Session(engine) as session:
        ingestion_run = session.get(IngestionRun, ingestion_run_id)
        if ingestion_run is None:
            return None

        ingestion_run.status = status
        ingestion_run.fetched_documents = fetched_documents
        ingestion_run.stored = stored
        ingestion_run.duplicates = duplicates
        ingestion_run.documents_processed = documents_processed
        ingestion_run.chunks_created = chunks_created
        ingestion_run.chunks_indexed = chunks_indexed
        ingestion_run.source_failures = json.dumps(source_failures)
        ingestion_run.duration_ms = duration_ms
        ingestion_run.finished_at = utc_now()

        session.add(ingestion_run)
        session.commit()
        session.refresh(ingestion_run)
        return ingestion_run


def list_ingestion_runs(limit: int = 10) -> list[IngestionRun]:
    with Session(engine) as session:
        statement = select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(limit)
        return list(session.exec(statement))


def count_documents() -> int:
    with Session(engine) as session:
        return session.exec(select(func.count()).select_from(Document)).one()


def count_chunks() -> int:
    with Session(engine) as session:
        return session.exec(select(func.count()).select_from(Chunk)).one()


def count_query_logs() -> int:
    with Session(engine) as session:
        return session.exec(select(func.count()).select_from(QueryLog)).one()


def count_feedback() -> int:
    with Session(engine) as session:
        return session.exec(select(func.count()).select_from(Feedback)).one()
