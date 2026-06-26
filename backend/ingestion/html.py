# Step 04 - HTML Ingestion
#
# Role:
#   Fetch a public HTML page and extract readable text.
#
# Why this exists:
#   Not every useful financial or regulatory source exposes RSS. HTML ingestion
#   lets the system collect content from normal public web pages.
#
# Input:
#   A source name and a public web page URL.
#
# Output:
#   One IngestedDocument object containing extracted page text.

import requests
from bs4 import BeautifulSoup

from backend.ingestion.models import IngestedDocument


def fetch_html(source_name: str, source_url: str) -> IngestedDocument:
    response = requests.get(source_url, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    title = " ".join((soup.title.string if soup.title else source_url).split())
    text = " ".join(soup.get_text(" ").split())

    return IngestedDocument(
        title=title,
        source_name=source_name,
        source_url=source_url,
        text=text,
    )
