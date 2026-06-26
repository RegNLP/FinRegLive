# Step 04 - GDELT News Ingestion
#
# Role:
#   Fetch public news article metadata from the GDELT DOC API.
#
# Why this exists:
#   Regulator websites give official source material, while GDELT gives broader
#   public news coverage around financial regulation topics.
#
# Input:
#   A search query, lookback window, and maximum article count.
#
# Output:
#   A list of IngestedDocument objects built from GDELT article records.

import os

import requests

from backend.ingestion.models import IngestedDocument


GDELT_DOC_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
DEFAULT_GDELT_QUERY = '"financial regulation" OR "securities regulation" OR "banking regulation"'


def request_headers() -> dict[str, str]:
    return {
        "User-Agent": os.getenv(
            "FINREG_USER_AGENT",
            "FinRegLive/0.1 educational-prototype contact=example@example.com",
        )
    }


def fetch_gdelt_news(
    source_name: str = "GDELT",
    query: str = DEFAULT_GDELT_QUERY,
    days: int = 7,
    limit: int = 25,
) -> list[IngestedDocument]:
    response = requests.get(
        GDELT_DOC_API_URL,
        params={
            "query": query,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": limit,
            "sort": "HybridRel",
            "timespan": f"{days}d",
        },
        headers=request_headers(),
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    articles = data.get("articles", [])
    documents: list[IngestedDocument] = []

    for article in articles:
        title = " ".join(str(article.get("title") or "Untitled").split())
        url = str(article.get("url") or "").strip()
        if not url:
            continue

        domain = article.get("domain") or "unknown domain"
        source_country = article.get("sourceCountry") or "unknown country"
        seen_date = article.get("seendate")
        text = " ".join(
            [
                title,
                f"Domain: {domain}.",
                f"Source country: {source_country}.",
                f"URL: {url}",
            ]
        )

        documents.append(
            IngestedDocument(
                title=title,
                source_name=source_name,
                source_url=url,
                text=text,
                publication_date=seen_date,
            )
        )

    return documents
