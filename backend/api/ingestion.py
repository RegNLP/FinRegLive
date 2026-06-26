# Step 14 - Ingestion API Route
#
# Role:
#   Expose recent source ingestion as an explicit backend action.
#
# Why this exists:
#   The frontend needs a safe way to refresh the dataset without running shell
#   commands. Ingestion should remain explicit, not hidden inside user queries.
#
# Input:
#   POST /ingest/recent with source, days, limit, and index options.
#
# Output:
#   A recent ingestion summary with stored, duplicate, chunk, and index counts.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from backend.ingestion.recent import (
    SOURCES,
    SOURCE_ALIASES,
    RecentIngestionResult,
    ingest_recent_sources,
)

router = APIRouter(tags=["ingestion"])


class RecentIngestionRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=90)
    source: str = "all"
    limit: int = Field(default=20, ge=1, le=100)
    recreate_index: bool = True

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        valid_sources = {"all", *SOURCES.keys(), *SOURCE_ALIASES.keys()}
        if value not in valid_sources:
            raise ValueError(f"source must be one of: {', '.join(sorted(valid_sources))}")
        return value


@router.post("/ingest/recent", response_model=RecentIngestionResult)
def ingest_recent(request: RecentIngestionRequest) -> RecentIngestionResult:
    try:
        return ingest_recent_sources(
            days=request.days,
            source_key=request.source,
            limit=request.limit,
            should_index=True,
            recreate_index=request.recreate_index,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Ingestion failed: {exc}") from exc
