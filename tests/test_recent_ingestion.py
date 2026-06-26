from datetime import datetime, timezone

from backend.ingestion.models import IngestedDocument
from backend.ingestion.recent import filter_documents_since, parse_publication_datetime, select_sources


def test_parse_rss_publication_date() -> None:
    parsed = parse_publication_datetime("Thu, 25 Jun 2026 10:30:00 GMT")

    assert parsed == datetime(2026, 6, 25, 10, 30, tzinfo=timezone.utc)


def test_filter_documents_since_keeps_only_recent_dated_documents() -> None:
    documents = [
        IngestedDocument(
            title="Recent",
            source_name="SEC",
            source_url="https://example.com/recent",
            text="recent text",
            publication_date="Thu, 25 Jun 2026 10:30:00 GMT",
        ),
        IngestedDocument(
            title="Old",
            source_name="SEC",
            source_url="https://example.com/old",
            text="old text",
            publication_date="Thu, 01 Jan 2026 10:30:00 GMT",
        ),
        IngestedDocument(
            title="No date",
            source_name="SEC",
            source_url="https://example.com/no-date",
            text="no date text",
        ),
    ]

    recent = filter_documents_since(
        documents,
        cutoff=datetime(2026, 6, 20, tzinfo=timezone.utc),
    )

    assert [document.title for document in recent] == ["Recent"]


def test_select_sources_all_includes_sec_and_fca() -> None:
    sources = select_sources("all")

    assert [source.key for source in sources] == ["sec", "fca"]
