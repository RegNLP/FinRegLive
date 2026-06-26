# Step 09D - Diagnostics API Route
#
# Role:
#   Report local system counts and search service status.
#
# Why this exists:
#   During development, we need one quick endpoint that answers: is the database
#   initialized, how much data is stored, is OpenSearch reachable, and how many
#   chunks are indexed?
#
# Input:
#   GET /diagnostics.
#
# Output:
#   JSON with SQLite counts and OpenSearch status.

from fastapi import APIRouter
from pydantic import BaseModel

from backend.config import get_settings
from backend.database.crud import (
    count_chunks,
    count_documents,
    count_feedback,
    count_query_logs,
)
from backend.database.db import init_db
from backend.ingestion.recent import SOURCES
from backend.search.client import get_search_client, ping_search

router = APIRouter(tags=["diagnostics"])


class DatabaseDiagnostics(BaseModel):
    status: str
    document_count: int
    chunk_count: int
    query_count: int
    feedback_count: int


class SearchDiagnostics(BaseModel):
    status: str
    host: str
    index_name: str
    index_exists: bool
    indexed_chunk_count: int | None = None


class SourceDiagnostics(BaseModel):
    key: str
    source_name: str
    source_type: str
    source_url: str


class DiagnosticsResponse(BaseModel):
    environment: str
    database: DatabaseDiagnostics
    search: SearchDiagnostics
    sources: list[SourceDiagnostics]


def _search_diagnostics() -> SearchDiagnostics:
    settings = get_settings()
    search_status = "ok" if ping_search() else "unavailable"

    if search_status != "ok":
        return SearchDiagnostics(
            status=search_status,
            host=settings.search.host,
            index_name=settings.search.index_name,
            index_exists=False,
        )

    client = get_search_client()
    index_exists = bool(client.indices.exists(index=settings.search.index_name))
    indexed_chunk_count = None

    if index_exists:
        indexed_chunk_count = int(client.count(index=settings.search.index_name)["count"])

    return SearchDiagnostics(
        status=search_status,
        host=settings.search.host,
        index_name=settings.search.index_name,
        index_exists=index_exists,
        indexed_chunk_count=indexed_chunk_count,
    )


@router.get("/diagnostics", response_model=DiagnosticsResponse)
def diagnostics() -> DiagnosticsResponse:
    init_db()
    settings = get_settings()

    return DiagnosticsResponse(
        environment=settings.environment,
        database=DatabaseDiagnostics(
            status="ok",
            document_count=count_documents(),
            chunk_count=count_chunks(),
            query_count=count_query_logs(),
            feedback_count=count_feedback(),
        ),
        search=_search_diagnostics(),
        sources=[
            SourceDiagnostics(
                key=source.key,
                source_name=source.source_name,
                source_type=source.source_type,
                source_url=source.source_url,
            )
            for source in SOURCES.values()
        ],
    )
