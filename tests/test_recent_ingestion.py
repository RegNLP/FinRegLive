from datetime import datetime, timezone

from backend.ingestion.models import IngestedDocument
from backend.ingestion.recent import filter_documents_since, parse_publication_datetime, select_sources


def test_parse_rss_publication_date() -> None:
    parsed = parse_publication_datetime("Thu, 25 Jun 2026 10:30:00 GMT")

    assert parsed == datetime(2026, 6, 25, 10, 30, tzinfo=timezone.utc)


def test_parse_atom_updated_date() -> None:
    parsed = parse_publication_datetime("2026-06-26T11:09:13-04:00")

    assert parsed == datetime(2026, 6, 26, 15, 9, 13, tzinfo=timezone.utc)


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


def test_select_sources_all_includes_registered_sources() -> None:
    sources = select_sources("all")

    assert [source.key for source in sources] == [
        "sec_press",
        "sec_edgar",
        "fca_news",
        "fca_publications",
        "boe_news",
        "boe_publications",
        "boe_prudential",
    ]


def test_select_sources_supports_old_aliases() -> None:
    assert select_sources("sec")[0].key == "sec_press"
    assert select_sources("fca")[0].key == "fca_news"
