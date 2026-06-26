# Step 04 - RSS Ingestion
#
# Role:
#   Fetch public RSS feeds and convert feed entries into IngestedDocument
#   objects.
#
# Why this exists:
#   RSS feeds are a reliable way to monitor recent updates from official
#   sources such as financial regulators.
#
# Input:
#   A source name, an RSS feed URL, and a limit.
#
# Output:
#   A list of IngestedDocument objects.

import feedparser

from backend.ingestion.models import IngestedDocument


def fetch_rss(source_name: str, source_url: str, limit: int = 5) -> list[IngestedDocument]:
    feed = feedparser.parse(source_url)
    documents: list[IngestedDocument] = []

    for entry in feed.entries[:limit]:
        title = " ".join(getattr(entry, "title", "Untitled").split())
        link = getattr(entry, "link", source_url)
        summary = " ".join(getattr(entry, "summary", "").split())
        publication_date = getattr(entry, "published", None)
        text = f"{title}\n\n{summary}".strip()

        if not text:
            continue

        documents.append(
            IngestedDocument(
                title=title,
                source_name=source_name,
                source_url=link,
                text=text,
                publication_date=publication_date,
            )
        )

    return documents
