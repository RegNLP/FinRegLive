# Step 03 - Database Connection
#
# Role:
#   Create the database engine and initialize database tables.
#
# Why this exists:
#   The system needs a local place to store document metadata, chunks, query
#   logs, and feedback. This file centralizes database setup so other files do
#   not create their own connections.
#
# Input:
#   Database settings from configs/local.yaml.
#
# Output:
#   A SQLModel engine and an init_db() function that creates tables.

from pathlib import Path

from sqlalchemy import inspect, text
from sqlmodel import SQLModel, create_engine

from backend.config import get_settings


def get_database_url() -> str:
    settings = get_settings()

    if settings.database.type != "sqlite":
        raise ValueError("Step 3 supports SQLite only.")

    sqlite_path = Path(settings.database.sqlite_path)
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{sqlite_path}"


engine = create_engine(get_database_url(), echo=False)


def _add_missing_document_text_column() -> None:
    inspector = inspect(engine)

    if "document" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("document")}
    if "text" in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE document ADD COLUMN text TEXT DEFAULT ''"))


def init_db() -> None:
    import backend.database.models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    _add_missing_document_text_column()
