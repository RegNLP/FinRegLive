# Step 05 - Text Chunking
#
# Role:
#   Split long document text into smaller overlapping chunks.
#
# Why this exists:
#   Search and LLM context windows work better with focused text passages than
#   with entire long documents. Chunks preserve enough local context while
#   keeping retrieval precise.
#
# Input:
#   Document text, chunk size in words, and overlap in words.
#
# Output:
#   A list of chunk text strings.


def chunk_text(text: str, chunk_size_words: int, chunk_overlap_words: int) -> list[str]:
    if chunk_size_words <= 0:
        raise ValueError("chunk_size_words must be greater than zero.")

    if chunk_overlap_words < 0:
        raise ValueError("chunk_overlap_words cannot be negative.")

    if chunk_overlap_words >= chunk_size_words:
        raise ValueError("chunk_overlap_words must be smaller than chunk_size_words.")

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size_words, len(words))
        chunks.append(" ".join(words[start:end]))

        if end == len(words):
            break

        start = end - chunk_overlap_words

    return chunks
