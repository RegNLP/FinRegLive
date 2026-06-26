# Step 13 - FCA Item-Level Ingestion
#
# Role:
#   Extract individual FCA item links from listing pages and fetch each item.
#
# Why this exists:
#   FCA listing pages contain many updates in one HTML page. For better RAG
#   retrieval, each FCA news item or publication should be stored as its own
#   document with its own title, URL, date, and body text.
#
# Input:
#   FCA listing page URLs such as /news or /publications.
#
# Output:
#   IngestedDocument objects for individual FCA item pages.

from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests import RequestException

from backend.ingestion.models import IngestedDocument


FCA_BASE_URL = "https://www.fca.org.uk"
FCA_NEWS_CATEGORIES = {
    "blogs",
    "news-stories",
    "press-releases",
    "speeches",
    "statements",
    "warnings",
}

FCA_SKIP_PATH_PARTS = {
    "inside-fca-podcasts",
    "media-library",
    "see-all-fca-events",
}


def request_headers() -> dict[str, str]:
    return {"User-Agent": "FinRegLive/0.1 educational-prototype"}


def is_fca_item_path(path: str) -> bool:
    parts = [part for part in path.strip("/").split("/") if part]

    if len(parts) < 3:
        return False

    section = parts[0]
    category = parts[1]
    slug = parts[2]

    if slug in FCA_SKIP_PATH_PARTS:
        return False

    if section == "news":
        return category in FCA_NEWS_CATEGORIES and slug not in FCA_NEWS_CATEGORIES

    if section == "publications":
        return category != "search-results"

    return False


def extract_fca_item_urls(listing_html: str, listing_url: str) -> list[str]:
    soup = BeautifulSoup(listing_html, "html.parser")
    urls = []
    seen = set()

    for link in soup.find_all("a", href=True):
        absolute_url = urljoin(FCA_BASE_URL, link["href"])
        parsed = urlparse(absolute_url)

        if parsed.netloc != "www.fca.org.uk":
            continue

        if not is_fca_item_path(parsed.path):
            continue

        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if clean_url == listing_url or clean_url in seen:
            continue

        seen.add(clean_url)
        urls.append(clean_url)

    return urls


def extract_fca_page_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "footer", "form", "aside"]):
        tag.decompose()

    content = soup.select_one(".node-content__wrapper") or soup.find("article") or soup.find(
        attrs={"role": "main"}
    )
    if content is None:
        content = soup

    return " ".join(content.get_text(" ").split())


def fetch_fca_item(source_name: str, item_url: str) -> IngestedDocument | None:
    response = requests.get(item_url, headers=request_headers(), timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title_tag = soup.select_one("h1.page-header") or soup.find("h1")
    title = " ".join(title_tag.get_text(" ").split()) if title_tag else item_url

    if title.lower() == "page not found":
        return None

    publication_time = soup.find("time")
    publication_date = None
    if publication_time and publication_time.get("datetime"):
        publication_date = publication_time["datetime"]

    if publication_date is None:
        published_meta = soup.find("meta", property="article:published_time")
        if published_meta:
            publication_date = published_meta.get("content")

    text = extract_fca_page_text(soup)
    if not text:
        return None

    return IngestedDocument(
        title=title,
        source_name=source_name,
        source_url=item_url,
        text=text,
        publication_date=publication_date,
    )


def fetch_fca_listing_items(
    source_name: str,
    listing_url: str,
    limit: int = 20,
) -> list[IngestedDocument]:
    response = requests.get(listing_url, headers=request_headers(), timeout=20)
    response.raise_for_status()

    item_urls = extract_fca_item_urls(response.text, listing_url)[:limit]
    documents = []

    for item_url in item_urls:
        try:
            document = fetch_fca_item(source_name=source_name, item_url=item_url)
        except RequestException:
            continue

        if document is not None:
            documents.append(document)

    return documents
