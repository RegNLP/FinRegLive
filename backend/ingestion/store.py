# Step 04b - Store Ingested Documents
#
# Role:
#   Save ingested documents into the local database.
#
# Why this exists:
#   Fetching source content is not enough. The system needs to persist new
#   documents and skip duplicates before later steps can chunk and search them.
#
# Input:
#   A list of IngestedDocument objects from RSS or HTML ingestion.
#
# Output:
#   A summary showing how many documents were stored and skipped.

from pydantic import BaseModel

from backend.database.crud import create_document, get_document_by_hash, update_document_text
from backend.database.db import init_db
from backend.ingestion.deduplication import content_hash
from backend.ingestion.models import IngestedDocument


class StoreIngestionResult(BaseModel):
    stored: int
    duplicates: int


def store_ingested_documents(documents: list[IngestedDocument]) -> StoreIngestionResult:
    init_db()

    stored = 0
    duplicates = 0

    for document in documents:
        document_hash = content_hash(document.text)

        existing_document = get_document_by_hash(document_hash)
        if existing_document:
            if not existing_document.text:
                update_document_text(existing_document.id, document.text)
            duplicates += 1
            continue

        create_document(
            title=document.title,
            source_name=document.source_name,
            source_url=document.source_url,
            text=document.text,
            content_hash=document_hash,
            publication_date=document.publication_date,
        )
        stored += 1

    return StoreIngestionResult(stored=stored, duplicates=duplicates)
