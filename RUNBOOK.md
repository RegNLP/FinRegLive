# Runbook

This file contains commands for running, checking, and stopping the project during development.

## Step 1: Project Foundation

### Create Virtual Environment

Create a project-local Python environment:

```bash
python -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

After activation, the terminal prompt should show:

```text
(.venv)
```

Why this matters:

- keeps this project's packages separate
- avoids conflicts with other Python projects
- makes `requirements.txt` reliable
- prevents relying on globally installed packages

### Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### Start Backend

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude '.venv/*'
```

What this means:

- `uvicorn` starts the FastAPI server
- `backend.main:app` points to the `app` object inside `backend/main.py`
- `--host 127.0.0.1` runs the server only on your local machine
- `--port 8000` uses port 8000
- `--reload` restarts the server automatically when code changes

### Check Health Endpoint

In another terminal:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

You can also open this URL in the browser:

```text
http://127.0.0.1:8000/health
```

### Open API Docs

FastAPI automatically creates interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### Stop Backend

In the terminal where Uvicorn is running, press:

```text
CTRL + C
```

## Step 2: Configuration and Environment

Step 2 adds configuration files so environment-specific values are not hardcoded in Python code.

Files added:

```text
configs/local.yaml
.env.example
backend/config.py
```

### Default Config File

The backend reads this file by default:

```text
configs/local.yaml
```

It contains non-secret local settings such as:

- environment name
- database type and path
- OpenSearch host
- LLM provider and model name

### Environment Variables Example

`.env.example` documents environment variables the project may need:

```text
OPENAI_API_KEY=
FINREG_CONFIG_PATH=configs/local.yaml
```

`.env.example` is safe to commit because it does not contain real secret values.

A real `.env` file should stay local and should not be committed.

### Check Config Endpoint

Start the backend first:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude '.venv/*'
```

Then run:

```bash
curl http://127.0.0.1:8000/config
```

Expected response:

```json
{"environment":"local"}
```

This confirms the backend can read `configs/local.yaml`.

### Override Config Path

The app uses `configs/local.yaml` by default. Later, another config file can be selected with `FINREG_CONFIG_PATH`.

Example:

```bash
FINREG_CONFIG_PATH=configs/local.yaml uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude '.venv/*'
```

## Step 3: Data Model and Storage

Step 3 adds a local SQLite database and database models.

Files added:

```text
backend/database/__init__.py
backend/database/db.py
backend/database/models.py
```

Dependency added:

```text
sqlmodel
```

### Install Updated Dependencies

```bash
python -m pip install -r requirements.txt
```

### Check Database Setup

Start the backend first:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude '.venv/*'
```

Then run:

```bash
curl http://127.0.0.1:8000/db-check
```

Expected response:

```json
{"database":"ok"}
```

This creates the local SQLite database at:

```text
data/app.db
```

The `data/` folder is ignored by Git because local database files should not be committed.

### Check Database Create and Read

Run this from the project root:

```bash
python - <<'PY'
from uuid import uuid4

from backend.database.db import init_db
from backend.database.crud import create_document, get_document, list_documents

init_db()

created = create_document(
    title="Sample FCA Update",
    source_name="FCA",
    source_url="https://example.com/fca-update",
    text="This is a sample FCA update about financial regulation.",
    content_hash=f"sample-{uuid4()}",
)

loaded = get_document(created.id)
documents = list_documents()

print("created:", created.id, created.title)
print("loaded:", loaded.id, loaded.title)
print("document_count:", len(documents))
PY
```

Expected output shape:

```text
created: 1 Sample FCA Update
loaded: 1 Sample FCA Update
document_count: 1
```

The exact ID and document count may be different if you have run the command before.

## Step 4: Ingestion

Step 4 adds code for fetching public source content.

Files added:

```text
backend/ingestion/__init__.py
backend/ingestion/models.py
backend/ingestion/rss.py
backend/ingestion/html.py
backend/ingestion/deduplication.py
```

Dependencies added:

```text
requests
feedparser
beautifulsoup4
```

### Install Updated Dependencies

```bash
python -m pip install -r requirements.txt
```

### Test SEC RSS Ingestion

```bash
python - <<'PY'
from backend.ingestion.rss import fetch_rss

docs = fetch_rss(
    source_name="SEC",
    source_url="https://www.sec.gov/news/pressreleases.rss",
    limit=3,
)

for doc in docs:
    print(doc.title)
    print(doc.source_url)
    print("---")
PY
```

Expected result:

```text
Three recent SEC press release titles and URLs.
```

### Test FCA HTML Ingestion

```bash
python - <<'PY'
from backend.ingestion.html import fetch_html

doc = fetch_html(
    source_name="FCA",
    source_url="https://www.fca.org.uk/news",
)

print(doc.title)
print(len(doc.text))
print(doc.text[:500])
PY
```

Expected result:

```text
The FCA page title, extracted text length, and the first part of the page text.
```

### Test Deduplication Hash

```bash
python - <<'PY'
from backend.ingestion.deduplication import content_hash

print(content_hash("AML   Update"))
print(content_hash(" aml update "))
print(content_hash("AML   Update") == content_hash(" aml update "))
PY
```

Expected final line:

```text
True
```

## Step 4b: Store Ingested Documents

Step 4b connects ingestion to the database.

Files added or updated:

```text
backend/ingestion/store.py
backend/database/crud.py
```

### Store SEC RSS Documents

```bash
python - <<'PY'
from backend.ingestion.rss import fetch_rss
from backend.ingestion.store import store_ingested_documents
from backend.database.crud import list_documents

docs = fetch_rss(
    source_name="SEC",
    source_url="https://www.sec.gov/news/pressreleases.rss",
    limit=3,
)

result = store_ingested_documents(docs)

print("stored:", result.stored)
print("duplicates:", result.duplicates)
print("total_documents:", len(list_documents()))
PY
```

Expected first run:

```text
stored: 3
duplicates: 0
```

Expected second run with the same feed:

```text
stored: 0
duplicates: 3
```

This proves the system can persist ingested documents and skip duplicates.

## Step 5: Chunking and Metadata

Step 5 splits stored document text into smaller chunks and stores those chunks in SQLite.

Files added or updated:

```text
backend/processing/__init__.py
backend/processing/chunker.py
backend/processing/build_chunks.py
backend/database/models.py
backend/database/crud.py
configs/local.yaml
```

Config added:

```yaml
processing:
  chunk_size_words: 120
  chunk_overlap_words: 20
```

### Test Chunking Function

```bash
python - <<'PY'
from backend.processing.chunker import chunk_text

text = " ".join(f"word{i}" for i in range(260))
chunks = chunk_text(text, chunk_size_words=100, chunk_overlap_words=20)

print("chunk_count:", len(chunks))
for index, chunk in enumerate(chunks):
    words = chunk.split()
    print(index, len(words), words[:3], words[-3:])
PY
```

Expected result:

```text
chunk_count: 3
```

### Build Chunks from Stored Documents

First make sure SEC documents are stored:

```bash
python - <<'PY'
from backend.ingestion.rss import fetch_rss
from backend.ingestion.store import store_ingested_documents

docs = fetch_rss(
    source_name="SEC",
    source_url="https://www.sec.gov/news/pressreleases.rss",
    limit=3,
)

result = store_ingested_documents(docs)
print("stored:", result.stored)
print("duplicates:", result.duplicates)
PY
```

Then create chunks:

```bash
python - <<'PY'
from backend.processing.build_chunks import build_chunks_for_stored_documents

result = build_chunks_for_stored_documents()

print("documents_processed:", result.documents_processed)
print("documents_skipped:", result.documents_skipped)
print("chunks_created:", result.chunks_created)
PY
```

Expected first run:

```text
documents_processed: at least 1
chunks_created: at least 1
```

Expected second run:

```text
documents_processed: 0
documents_skipped: at least 1
chunks_created: 0
```

This proves the system chunks each stored document only once.

## Step 6: Search Indexing

Step 6 will add OpenSearch indexing.

This step requires Docker Desktop because OpenSearch will run as a local container.

### Docker Desktop Requirement

Before running OpenSearch locally, install and start Docker Desktop.

Check whether Docker is available:

```bash
docker --version
docker compose version
```

If Docker Desktop is not installed or not running, these commands will fail.

Phase 6 will be implemented in smaller parts:

```text
6A: Run OpenSearch locally
6B: Add OpenSearch Python client
6C: Create OpenSearch index schema
6D: Generate embeddings
6E: Index chunks into OpenSearch
6F: Run manual BM25/vector search checks
```

### Step 6A: Start OpenSearch

Start OpenSearch:

```bash
docker compose -f infra/docker-compose.yml up -d
```

Check containers:

```bash
docker compose -f infra/docker-compose.yml ps
```

Check OpenSearch:

```bash
curl http://localhost:9200
```

Expected result:

```text
An OpenSearch JSON response with cluster information.
```

Stop OpenSearch:

```bash
docker compose -f infra/docker-compose.yml down
```

Stop OpenSearch and delete the local OpenSearch volume:

```bash
docker compose -f infra/docker-compose.yml down -v
```

## Checks So Far

Run these from the project root after activating `.venv`.

Start backend:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude '.venv/*'
```

In another terminal:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/config
curl http://127.0.0.1:8000/db-check
```

Expected responses:

```json
{"status":"ok"}
{"environment":"local"}
{"database":"ok"}
```

Then run the Step 4 and Step 4b Python checks above to confirm ingestion and storage still work.
