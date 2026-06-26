# Step 01 - FastAPI Application Entry Point
#
# Role:
#   Create the backend API application and define simple check endpoints.
#
# Why this exists:
#   The backend needs one starting point that Uvicorn can run. Later, this file
#   will connect API routers for ingestion, querying, feedback, and diagnostics.
#
# Input:
#   HTTP requests such as GET /health, GET /config, and GET /db-check.
#
# Output:
#   JSON responses that confirm the backend, config layer, and database layer
#   are working.

from fastapi import FastAPI

from backend.config import get_settings
from backend.database.db import init_db


app = FastAPI(title="FinReg Live Intelligence")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
def config() -> dict[str, str]:
    settings = get_settings()
    return {"environment": settings.environment}


@app.get("/db-check")
def db_check() -> dict[str, str]:
    init_db()
    return {"database": "ok"}
