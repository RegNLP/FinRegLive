# Step 04 - Ingestion Data Models
#
# Role:
#   Define the temporary Python object used for fetched source content.
#
# Why this exists:
#   Ingested content is not immediately a database record. First, each source
#   is converted into a consistent object that later steps can clean, store,
#   chunk, and index.
#
# Input:
#   Parsed fields from RSS feeds or HTML pages.
#
# Output:
#   IngestedDocument objects with title, source, URL, date, and text.

from pydantic import BaseModel


class IngestedDocument(BaseModel):
    title: str
    source_name: str
    source_url: str
    text: str
    publication_date: str | None = None
