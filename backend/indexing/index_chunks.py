# Step 06E - Index Chunks Into OpenSearch
#
# Role:
#   Send stored SQLite chunks to OpenSearch with metadata and embeddings.
#
# Why this exists:
#   SQLite stores application metadata, but OpenSearch provides ranked text and
#   vector retrieval. This step turns database chunks into searchable evidence.
#
# Input:
#   Chunk and Document rows from SQLite.
#
# Output:
#   Indexed OpenSearch documents in the finreg_chunks index.

from pydantic import BaseModel

from backend.config import get_settings
from backend.database.crud import get_document, list_chunks
from backend.database.db import init_db
from backend.indexing.embeddings import embed_texts
from backend.indexing.manage_index import create_index
from backend.search.client import get_search_client


class IndexChunksResult(BaseModel):
    chunks_seen: int
    chunks_indexed: int
    chunks_skipped: int


def build_index_document(chunk, document, embedding: list[float]) -> dict:
    return {
        "chunk_id": str(chunk.id),
        "document_id": document.id,
        "chunk_index": chunk.chunk_index,
        "chunk_text": chunk.text,
        "title": document.title,
        "source_name": document.source_name,
        "source_url": document.source_url,
        "publication_date": document.publication_date,
        "created_at": chunk.created_at.isoformat(),
        "embedding": embedding,
    }


def index_chunks(recreate_index: bool = False) -> IndexChunksResult:
    init_db()
    create_index(recreate=recreate_index)

    settings = get_settings()
    client = get_search_client()
    chunks = list_chunks()

    if not chunks:
        return IndexChunksResult(chunks_seen=0, chunks_indexed=0, chunks_skipped=0)

    texts = [chunk.text for chunk in chunks]
    embeddings = embed_texts(texts)

    chunks_indexed = 0
    chunks_skipped = 0

    for chunk, embedding in zip(chunks, embeddings):
        document = get_document(chunk.document_id)
        if document is None:
            chunks_skipped += 1
            continue

        client.index(
            index=settings.search.index_name,
            id=str(chunk.id),
            body=build_index_document(chunk, document, embedding),
            refresh=True,
        )
        chunks_indexed += 1

    return IndexChunksResult(
        chunks_seen=len(chunks),
        chunks_indexed=chunks_indexed,
        chunks_skipped=chunks_skipped,
    )


def main() -> None:
    result = index_chunks()
    print("chunks_seen:", result.chunks_seen)
    print("chunks_indexed:", result.chunks_indexed)
    print("chunks_skipped:", result.chunks_skipped)


if __name__ == "__main__":
    main()
