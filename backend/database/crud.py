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

from sqlmodel import Session, select

from backend.database.db import engine
from backend.database.models import Chunk, Document


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
