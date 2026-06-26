# Step 06D - Embeddings
#
# Role:
#   Convert chunk text into numeric vectors for semantic search.
#
# Why this exists:
#   Vector search needs embeddings. An embedding represents text meaning as a
#   list of numbers, so OpenSearch can find chunks that are semantically close
#   to a user query.
#
# Input:
#   Chunk text strings and embedding settings from configs/local.yaml.
#
# Output:
#   A list of floating-point embedding vectors.

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from backend.config import get_settings


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    settings = get_settings()
    return SentenceTransformer(settings.embeddings.model_name)


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return embeddings.astype("float32").tolist()


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
