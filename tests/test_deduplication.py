# Step 11B - Deduplication Tests
#
# Role:
#   Verify stable text normalization and content hashes.
#
# Why this exists:
#   Deduplication should treat case and spacing differences as the same content
#   so repeated public updates do not create duplicate document rows.
#
# Input:
#   Equivalent text strings with different casing and spacing.
#
# Output:
#   Passing pytest checks for normalized text and stable hashes.

from backend.ingestion.deduplication import content_hash, normalize_text


def test_normalize_text_lowercases_and_collapses_whitespace() -> None:
    assert normalize_text(" AML   Update\nToday ") == "aml update today"


def test_content_hash_is_stable_for_equivalent_text() -> None:
    assert content_hash("AML   Update") == content_hash(" aml update ")
