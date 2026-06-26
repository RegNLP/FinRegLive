# Step 04C - Recent Source Ingestion
#
# Role:
#   Fetch recent regulator updates from configured RSS and HTML sources.
#
# Why this exists:
#   The RAG dataset should be refreshed as a pipeline step before users ask
#   questions. This command gives us one reusable ingestion entry point that
#   can later be called by a scheduler or an admin UI button.
#
# Input:
#   Source choices, a lookback window in days, and optional indexing flags.
#
# Output:
#   Stored documents, database chunks, and updated OpenSearch chunk index.

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from pydantic import BaseModel

from backend.indexing.index_chunks import IndexChunksResult, index_chunks
from backend.ingestion.gdelt import fetch_gdelt_news
from backend.ingestion.html import fetch_html
from backend.ingestion.models import IngestedDocument
from backend.ingestion.rss import fetch_rss
from backend.ingestion.store import store_ingested_documents
from backend.processing.build_chunks import build_chunks_for_stored_documents


@dataclass(frozen=True)
class SourceDefinition:
    key: str
    source_name: str
    source_url: str
    source_type: str


SOURCES = {
    "sec_press": SourceDefinition(
        key="sec_press",
        source_name="SEC",
        source_url="https://www.sec.gov/news/pressreleases.rss",
        source_type="rss",
    ),
    "sec_edgar": SourceDefinition(
        key="sec_edgar",
        source_name="SEC EDGAR",
        source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&count=100&output=atom",
        source_type="rss",
    ),
    "fca_news": SourceDefinition(
        key="fca_news",
        source_name="FCA",
        source_url="https://www.fca.org.uk/news",
        source_type="html",
    ),
    "fca_publications": SourceDefinition(
        key="fca_publications",
        source_name="FCA Publications",
        source_url="https://www.fca.org.uk/publications",
        source_type="html",
    ),
    "gdelt_news": SourceDefinition(
        key="gdelt_news",
        source_name="GDELT",
        source_url="https://api.gdeltproject.org/api/v2/doc/doc",
        source_type="gdelt",
    ),
}

SOURCE_ALIASES = {
    "sec": "sec_press",
    "fca": "fca_news",
}


class RecentIngestionResult(BaseModel):
    days: int
    source_keys: list[str]
    fetched_documents: int
    recent_documents: int
    stored: int
    duplicates: int
    documents_processed: int
    chunks_created: int
    chunks_indexed: int
    html_snapshots: int
    source_failures: list[str]


def parse_publication_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def filter_documents_since(
    documents: list[IngestedDocument],
    cutoff: datetime,
) -> list[IngestedDocument]:
    recent_documents = []

    for document in documents:
        publication_datetime = parse_publication_datetime(document.publication_date)
        if publication_datetime and publication_datetime >= cutoff:
            recent_documents.append(document)

    return recent_documents


def fetch_recent_source(
    source: SourceDefinition,
    days: int,
    limit: int,
) -> tuple[list[IngestedDocument], int]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    if source.source_type == "rss":
        documents = fetch_rss(
            source_name=source.source_name,
            source_url=source.source_url,
            limit=limit,
        )
        return filter_documents_since(documents, cutoff), 0

    if source.source_type == "html":
        document = fetch_html(source_name=source.source_name, source_url=source.source_url)
        return [document], 1

    if source.source_type == "gdelt":
        documents = fetch_gdelt_news(
            source_name=source.source_name,
            days=days,
            limit=limit,
        )
        return documents, 0

    raise ValueError(f"Unsupported source type: {source.source_type}")


def select_sources(source_key: str) -> list[SourceDefinition]:
    if source_key == "all":
        return list(SOURCES.values())

    resolved_source_key = SOURCE_ALIASES.get(source_key, source_key)
    source = SOURCES.get(resolved_source_key)
    if source is None:
        valid_sources = ", ".join(["all", *SOURCES, *SOURCE_ALIASES])
        raise ValueError(f"Unknown source '{source_key}'. Use one of: {valid_sources}")

    return [source]


def ingest_recent_sources(
    days: int = 7,
    source_key: str = "all",
    limit: int = 50,
    should_index: bool = True,
    recreate_index: bool = False,
) -> RecentIngestionResult:
    selected_sources = select_sources(source_key)

    documents: list[IngestedDocument] = []
    html_snapshots = 0
    source_failures = []

    for source in selected_sources:
        try:
            source_documents, source_html_snapshots = fetch_recent_source(
                source=source,
                days=days,
                limit=limit,
            )
        except Exception as exc:
            source_failures.append(f"{source.key}: {exc}")
            continue

        documents.extend(source_documents)
        html_snapshots += source_html_snapshots

    store_result = store_ingested_documents(documents)
    chunk_result = build_chunks_for_stored_documents()

    index_result = IndexChunksResult(chunks_seen=0, chunks_indexed=0, chunks_skipped=0)
    if should_index:
        index_result = index_chunks(recreate_index=recreate_index)

    return RecentIngestionResult(
        days=days,
        source_keys=[source.key for source in selected_sources],
        fetched_documents=len(documents),
        recent_documents=len(documents),
        stored=store_result.stored,
        duplicates=store_result.duplicates,
        documents_processed=chunk_result.documents_processed,
        chunks_created=chunk_result.chunks_created,
        chunks_indexed=index_result.chunks_indexed,
        html_snapshots=html_snapshots,
        source_failures=source_failures,
    )


def print_result(result: RecentIngestionResult) -> None:
    print("days:", result.days)
    print("sources:", ", ".join(result.source_keys))
    print("fetched_documents:", result.fetched_documents)
    print("stored:", result.stored)
    print("duplicates:", result.duplicates)
    print("documents_processed:", result.documents_processed)
    print("chunks_created:", result.chunks_created)
    print("chunks_indexed:", result.chunks_indexed)
    print("html_snapshots:", result.html_snapshots)
    if result.source_failures:
        print("source_failures:")
        for failure in result.source_failures:
            print(f"- {failure}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest recent regulator updates.")
    parser.add_argument("--days", type=int, default=7, help="RSS lookback window in days.")
    parser.add_argument(
        "--source",
        choices=["all", *SOURCES.keys(), *SOURCE_ALIASES.keys()],
        default="all",
        help="Source to ingest.",
    )
    parser.add_argument("--limit", type=int, default=50, help="Maximum RSS entries per source.")
    parser.add_argument("--skip-index", action="store_true", help="Store and chunk without indexing.")
    parser.add_argument(
        "--recreate-index",
        action="store_true",
        help="Delete and recreate the OpenSearch index before indexing chunks.",
    )
    args = parser.parse_args()

    result = ingest_recent_sources(
        days=args.days,
        source_key=args.source,
        limit=args.limit,
        should_index=not args.skip_index,
        recreate_index=args.recreate_index,
    )
    print_result(result)


if __name__ == "__main__":
    main()
