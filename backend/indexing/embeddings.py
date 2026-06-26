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

import hashlib
import math
from functools import lru_cache

from backend.config import get_settings


@lru_cache
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    settings = get_settings()
    return SentenceTransformer(settings.embeddings.model_name)


def embed_texts_with_hash(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    dimension = settings.embeddings.dimension
    vectors = []

    for text in texts:
        vector = [0.0] * dimension
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], byteorder="big") % dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]

        vectors.append(vector)

    return vectors


def embed_texts(texts: list[str]) -> list[list[float]]:
    settings = get_settings()

    if settings.embeddings.provider == "hash":
        return embed_texts_with_hash(texts)

    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return embeddings.astype("float32").tolist()


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
