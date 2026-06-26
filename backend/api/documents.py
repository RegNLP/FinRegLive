# Step 11C - Documents API Routes
#
# Role:
#   Expose stored documents and recent updates through read-only API endpoints.
#
# Why this exists:
#   The frontend and future clients need a way to browse ingested regulatory
#   updates, inspect a specific document, and see the chunks used for retrieval.
#
# Input:
#   GET /documents, GET /documents/{document_id}, and GET /recent-updates.
#
# Output:
#   Structured document metadata, document detail, and recent update JSON.

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.database.crud import get_chunks_for_document, get_document, list_documents
from backend.database.db import init_db
from backend.database.models import Chunk, Document

router = APIRouter(tags=["documents"])


class DocumentSummary(BaseModel):
    id: int
    title: str
    source_name: str
    source_url: str
    publication_date: str | None
    created_at: datetime
    text_length: int
    chunk_count: int


class ChunkResponse(BaseModel):
    id: int
    chunk_index: int
    text: str
    created_at: datetime


class DocumentDetail(DocumentSummary):
    text: str
    chunks: list[ChunkResponse]


def _document_summary(document: Document, chunks: list[Chunk]) -> DocumentSummary:
    return DocumentSummary(
        id=document.id,
        title=document.title,
        source_name=document.source_name,
        source_url=document.source_url,
        publication_date=document.publication_date,
        created_at=document.created_at,
        text_length=len(document.text),
        chunk_count=len(chunks),
    )


def _chunk_response(chunk: Chunk) -> ChunkResponse:
    return ChunkResponse(
        id=chunk.id,
        chunk_index=chunk.chunk_index,
        text=chunk.text,
        created_at=chunk.created_at,
    )


@router.get("/documents", response_model=list[DocumentSummary])
def documents(limit: int = Query(default=20, ge=1, le=100)) -> list[DocumentSummary]:
    init_db()

    summaries = []
    for document in list_documents()[:limit]:
        chunks = get_chunks_for_document(document.id)
        summaries.append(_document_summary(document, chunks))

    return summaries


@router.get("/documents/{document_id}", response_model=DocumentDetail)
def document_detail(document_id: int) -> DocumentDetail:
    init_db()

    document = get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document_id was not found")

    chunks = get_chunks_for_document(document.id)
    summary = _document_summary(document, chunks)

    return DocumentDetail(
        **summary.model_dump(),
        text=document.text,
        chunks=[_chunk_response(chunk) for chunk in chunks],
    )


@router.get("/recent-updates", response_model=list[DocumentSummary])
def recent_updates(limit: int = Query(default=10, ge=1, le=50)) -> list[DocumentSummary]:
    init_db()

    summaries = []
    for document in list_documents()[:limit]:
        chunks = get_chunks_for_document(document.id)
        summaries.append(_document_summary(document, chunks))

    return summaries
