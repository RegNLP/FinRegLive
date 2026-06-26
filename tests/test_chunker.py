# Step 11B - Chunking Tests
#
# Role:
#   Verify that word chunking creates predictable overlapping chunks.
#
# Why this exists:
#   Retrieval quality depends on chunk boundaries. These tests protect the
#   basic chunking behavior from accidental changes.
#
# Input:
#   Short sample strings and chunking settings.
#
# Output:
#   Passing pytest checks for chunk count, overlap, and validation errors.

import pytest

from backend.processing.chunker import chunk_text


def test_chunk_text_uses_word_overlap() -> None:
    text = " ".join(f"word{i}" for i in range(10))

    chunks = chunk_text(text, chunk_size_words=4, chunk_overlap_words=1)

    assert chunks == [
        "word0 word1 word2 word3",
        "word3 word4 word5 word6",
        "word6 word7 word8 word9",
    ]


def test_chunk_text_returns_empty_list_for_empty_text() -> None:
    assert chunk_text("   ", chunk_size_words=4, chunk_overlap_words=1) == []


def test_chunk_text_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError, match="smaller"):
        chunk_text("one two three", chunk_size_words=3, chunk_overlap_words=3)
