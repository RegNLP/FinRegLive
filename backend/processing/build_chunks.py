# Step 05 - Build Database Chunks
#
# Role:
#   Create Chunk rows from stored Document rows.
#
# Why this exists:
#   Ingested documents must be split into retrievable pieces before search
#   indexing. This file connects stored document text to the chunk table.
#
# Input:
#   Stored documents with text in SQLite.
#
# Output:
#   A summary showing how many documents were processed and chunks created.

from pydantic import BaseModel

from backend.config import get_settings
from backend.database.crud import create_chunk, get_chunks_for_document, list_documents_with_text
from backend.database.db import init_db
from backend.processing.chunker import chunk_text


class BuildChunksResult(BaseModel):
    documents_processed: int
    documents_skipped: int
    chunks_created: int


def build_chunks_for_stored_documents() -> BuildChunksResult:
    init_db()
    settings = get_settings()

    documents_processed = 0
    documents_skipped = 0
    chunks_created = 0

    for document in list_documents_with_text():
        existing_chunks = get_chunks_for_document(document.id)
        if existing_chunks:
            documents_skipped += 1
            continue

        chunks = chunk_text(
            text=document.text,
            chunk_size_words=settings.processing.chunk_size_words,
            chunk_overlap_words=settings.processing.chunk_overlap_words,
        )

        for index, chunk in enumerate(chunks):
            create_chunk(document_id=document.id, chunk_index=index, text=chunk)
            chunks_created += 1

        documents_processed += 1

    return BuildChunksResult(
        documents_processed=documents_processed,
        documents_skipped=documents_skipped,
        chunks_created=chunks_created,
    )
