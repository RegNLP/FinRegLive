# Step 06C - OpenSearch Index Schema
#
# Role:
#   Define the OpenSearch index mapping for searchable chunk records.
#
# Why this exists:
#   OpenSearch needs to know how each field should be indexed. Text fields are
#   used for BM25 search, keyword/date fields are used for filtering, and the
#   embedding field will support vector search.
#
# Input:
#   Search and embedding settings from configs/local.yaml.
#
# Output:
#   A Python dictionary containing OpenSearch index settings and mappings.

from backend.config import get_settings


def chunk_index_schema() -> dict:
    settings = get_settings()

    return {
        "settings": {
            "index": {
                "knn": True,
            }
        },
        "mappings": {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "document_id": {"type": "integer"},
                "chunk_index": {"type": "integer"},
                "chunk_text": {"type": "text"},
                "title": {"type": "text"},
                "source_name": {"type": "keyword"},
                "source_url": {"type": "keyword"},
                "publication_date": {"type": "date", "ignore_malformed": True},
                "created_at": {"type": "date"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": settings.embeddings.dimension,
                },
            }
        },
    }
