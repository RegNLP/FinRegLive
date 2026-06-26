# Step 04 - Ingestion Deduplication
#
# Role:
#   Create stable hashes for document text.
#
# Why this exists:
#   Public sources may repeat or update the same content. Hashing normalized
#   text lets the system detect duplicate documents before storing them.
#
# Input:
#   Raw or cleaned document text.
#
# Output:
#   A SHA-256 content hash string.

import hashlib


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def content_hash(text: str) -> str:
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
