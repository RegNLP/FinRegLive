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
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude '.venv/*'
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
FINREG_USER_AGENT=FinRegLive/0.1 contact=your_email@example.com
```

`.env.example` is safe to commit because it does not contain real secret values.

A real `.env` file should stay local and should not be committed.

### Check Config Endpoint

Start the backend first:

```bash
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude '.venv/*'
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
FINREG_CONFIG_PATH=configs/local.yaml .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude '.venv/*'
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
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude '.venv/*'
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

### Step 6B: Check Python OpenSearch Client

Install updated dependencies:

```bash
python -m pip install -r requirements.txt
```

Make sure OpenSearch is running:

```bash
docker compose -f infra/docker-compose.yml ps
```

Then run:

```bash
python - <<'PY'
from backend.search.client import get_search_client, ping_search

client = get_search_client()

print("ping:", ping_search())
print("info:", client.info()["version"]["distribution"], client.info()["version"]["number"])
PY
```

Expected result:

```text
ping: True
info: opensearch 2.13.0
```

### Step 6C: Create OpenSearch Index

Create the chunk index:

```bash
python -m backend.indexing.manage_index
```

Expected first result:

```text
created: finreg_chunks
```

Expected later result if the index already exists:

```text
exists: finreg_chunks
```

Recreate the index from scratch:

```bash
python -m backend.indexing.manage_index --recreate
```

Check the mapping:

```bash
curl http://localhost:9200/finreg_chunks/_mapping
```

### Step 6D: Generate Embeddings

Install updated dependencies:

```bash
python -m pip install -r requirements.txt
```

Generate one embedding:

```bash
python - <<'PY'
from backend.indexing.embeddings import embed_text

vector = embed_text("Financial crime compliance and AML controls")

print("dimension:", len(vector))
print("first_values:", vector[:5])
PY
```

Expected result:

```text
dimension: 384
```

The first run may take longer because the embedding model is downloaded.

### Step 6E: Index Chunks Into OpenSearch

Make sure documents have been ingested and chunked first.

Index stored chunks:

```bash
python -m backend.indexing.index_chunks
```

Expected result:

```text
chunks_seen: at least 1
chunks_indexed: at least 1
chunks_skipped: 0
```

Check OpenSearch document count:

```bash
curl http://localhost:9200/finreg_chunks/_count
```

Run a simple BM25 search directly in OpenSearch:

```bash
curl "http://localhost:9200/finreg_chunks/_search?q=derivatives&_source_excludes=embedding&size=2"
```

### Step 6F: Manual BM25 and Vector Search Checks

Run a Python search check:

```bash
python -m backend.indexing.search_checks "derivatives product definitions"
```

Expected result:

```text
BM25 results
...
Vector results
...
```

Both sections should return indexed SEC chunks.

## Step 7: Retrieval

Step 7 turns manual search checks into reusable retrieval functions.

Files added:

```text
backend/retrieval/__init__.py
backend/retrieval/models.py
backend/retrieval/common.py
backend/retrieval/bm25.py
backend/retrieval/vector.py
backend/retrieval/hybrid.py
```

### BM25 Retrieval

```bash
python -m backend.retrieval.bm25 "derivatives product definitions"
```

### Vector Retrieval

```bash
python -m backend.retrieval.vector "swap market reporting rules"
```

### Hybrid Retrieval

```bash
python -m backend.retrieval.hybrid "derivatives product definitions"
```

Expected result:

```text
Ranked evidence chunks with score, title, source, URL, and text preview.
```

## Step 8: Answer Generation

Step 8 turns retrieved evidence into a source-grounded answer.

Files added:

```text
backend/generation/__init__.py
backend/generation/models.py
backend/generation/prompts.py
backend/generation/answer.py
```

Run a grounded answer:

```bash
python -m backend.generation.answer "What did the SEC and CFTC publish about derivatives?"
```

Expected result:

```text
Question
Answer
Sources
Limitations
```

The current answer generator is a local grounded fallback. It uses retrieved evidence only and does not call an LLM yet.

### Optional OpenAI Answer Generation

Make sure `.env` contains:

```text
OPENAI_API_KEY=your_real_key
FINREG_CONFIG_PATH=configs/local.yaml
```

Install updated dependencies:

```bash
python -m pip install -r requirements.txt
```

Run with OpenAI:

```bash
python -m backend.generation.answer "What did the SEC and CFTC publish about derivatives?" --top-k 2 --use-llm
```

The retrieval still happens locally through OpenSearch. OpenAI only receives the question and retrieved evidence.
The app prints sources and limitations separately, so the LLM should return only the answer text.

## Step 9A: Query API Endpoint

Step 9A exposes the RAG flow through FastAPI.

Files added or updated:

```text
backend/api/__init__.py
backend/api/query.py
backend/main.py
```

Start the backend:

```bash
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude '.venv/*'
```

Call `/query` with local fallback generation:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What did the SEC and CFTC publish about derivatives?",
    "top_k": 2,
    "use_llm": false
  }'
```

Call `/query` with OpenAI generation:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What did the SEC and CFTC publish about derivatives?",
    "top_k": 2,
    "use_llm": true
  }'
```

The response includes:

```text
query_id
question
answer
sources
limitations
```

`query_id` is useful for later feedback. It lets the app connect feedback to the exact question and answer.

## Step 9B: Query Logging

Step 9B stores every successful `/query` call in SQLite.

Why this exists:

- we need to know what users asked
- we need to know whether the answer used local generation or OpenAI
- we need to know which chunks were retrieved
- feedback will later connect to a saved query log

Stored fields:

```text
query_text
retrieval_method
answer_mode
top_k
retrieved_chunk_ids
source_count
latency_ms
created_at
```

Check recent query logs:

```bash
python - <<'PY'
from backend.database.crud import list_query_logs
from backend.database.db import init_db

init_db()

for log in list_query_logs()[:5]:
    print("id:", log.id)
    print("query:", log.query_text)
    print("retrieval:", log.retrieval_method)
    print("answer_mode:", log.answer_mode)
    print("top_k:", log.top_k)
    print("chunk_ids:", log.retrieved_chunk_ids)
    print("source_count:", log.source_count)
    print("latency_ms:", log.latency_ms)
    print("---")
PY
```

## Step 9C: Feedback API Endpoint

Step 9C stores user feedback for a saved query.

Why this exists:

- feedback tells us whether an answer was useful
- feedback tells us whether the answer looked correct
- feedback tells us whether the cited evidence was good enough
- feedback must connect to `query_id` so we know which answer was reviewed

Files added or updated:

```text
backend/api/feedback.py
backend/database/crud.py
backend/main.py
```

First, create a query and note the returned `query_id`:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What did the SEC and CFTC publish about derivatives?",
    "top_k": 2,
    "use_llm": false
  }'
```

Then submit feedback using that `query_id`:

```bash
curl -X POST http://127.0.0.1:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": 1,
    "useful_label": "useful",
    "correctness_label": "correct",
    "evidence_label": "supported",
    "note": "The answer cites the two relevant SEC/CFTC updates."
  }'
```

Expected response shape:

```json
{
  "feedback_id": 1,
  "query_id": 1,
  "status": "stored"
}
```

Check recent feedback rows:

```bash
python - <<'PY'
from backend.database.crud import list_feedback
from backend.database.db import init_db

init_db()

for feedback in list_feedback()[:5]:
    print("id:", feedback.id)
    print("query_id:", feedback.query_id)
    print("useful:", feedback.useful_label)
    print("correctness:", feedback.correctness_label)
    print("evidence:", feedback.evidence_label)
    print("note:", feedback.note)
    print("---")
PY
```

## Step 9D: Diagnostics API Endpoint

Step 9D adds one endpoint for checking local system state.

Why this exists:

- diagnostics quickly show whether the database is initialized
- diagnostics show how many documents, chunks, queries, and feedback rows exist
- diagnostics show whether OpenSearch is reachable
- diagnostics show whether the configured chunk index exists
- diagnostics show how many chunks are indexed in OpenSearch

Files added or updated:

```text
backend/api/diagnostics.py
backend/database/crud.py
backend/main.py
```

Call diagnostics:

```bash
curl http://127.0.0.1:8000/diagnostics
```

Pretty-print diagnostics:

```bash
curl -s http://127.0.0.1:8000/diagnostics | python -m json.tool
```

Expected response shape:

```json
{
  "environment": "local",
  "database": {
    "status": "ok",
    "document_count": 5,
    "chunk_count": 3,
    "query_count": 3,
    "feedback_count": 1
  },
  "search": {
    "status": "ok",
    "host": "http://localhost:9200",
    "index_name": "finreg_chunks",
    "index_exists": true,
    "indexed_chunk_count": 3
  }
}
```

The exact counts may be different on your machine depending on how many test commands you have run.

## Step 10: Streamlit Frontend

Step 10 adds a browser UI for the existing FastAPI backend.

Why this exists:

- users should not need terminal commands to ask questions
- answers, sources, limitations, and feedback should be visible in one place
- diagnostics should be easy to check during development

Files added or updated:

```text
frontend/__init__.py
frontend/app.py
requirements.txt
```

Install updated dependencies:

```bash
python -m pip install -r requirements.txt
```

Start OpenSearch:

```bash
docker compose -f infra/docker-compose.yml up -d
```

Start the backend:

```bash
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude '.venv/*'
```

Start the frontend in another terminal:

```bash
.venv/bin/python -m streamlit run frontend/app.py --server.port 8501
```

If port `8501` is already used by another Streamlit app, use another port:

```bash
.venv/bin/python -m streamlit run frontend/app.py --server.port 8502
```

Open the frontend:

```text
http://localhost:8501
```

The frontend calls this backend by default:

```text
http://127.0.0.1:8000
```

To point the frontend at a different backend URL:

```bash
FINREG_API_BASE_URL=http://127.0.0.1:8000 .venv/bin/python -m streamlit run frontend/app.py --server.port 8501
```

## Step 11A: API Quality Fixes

Step 11A improves API validation and error handling.

Why this exists:

- blank questions should not run retrieval
- feedback labels should use known values only
- OpenSearch failures should return a clear service error
- missing OpenAI configuration should return a clear service error

Validation added:

```text
question: 3 to 1000 non-space characters
top_k: 1 to 10
useful_label: useful, not_useful, unsure
correctness_label: correct, incorrect, unsure
evidence_label: supported, weak, missing, unsure
note: up to 1000 characters
```

Check blank question validation:

```bash
curl -i -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "   ",
    "top_k": 2,
    "use_llm": false
  }'
```

Expected status:

```text
422 Unprocessable Entity
```

Check invalid feedback label validation:

```bash
curl -i -X POST http://127.0.0.1:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": 1,
    "useful_label": "bad_value",
    "correctness_label": "correct",
    "evidence_label": "supported"
  }'
```

Expected status:

```text
422 Unprocessable Entity
```

If OpenSearch is unavailable, `/query` returns:

```json
{
  "detail": "Search service is unavailable or the chunk index is not ready."
}
```

If OpenAI mode is requested but `OPENAI_API_KEY` is missing, `/query` returns:

```json
{
  "detail": "OpenAI answer generation is not configured. Check OPENAI_API_KEY."
}
```

## Step 11B: Tests with Pytest

Step 11B adds automated tests.

Why this exists:

- tests protect important behavior while the project grows
- tests catch accidental changes in chunking and deduplication
- tests verify API validation and friendly error responses
- mocked API tests avoid real OpenSearch and OpenAI calls

Files added or updated:

```text
tests/__init__.py
tests/test_api.py
tests/test_chunker.py
tests/test_deduplication.py
readline.py
requirements.txt
```

Install updated dependencies:

```bash
python -m pip install -r requirements.txt
```

Run tests:

```bash
python -m pytest -q
```

Expected result:

```text
16 passed
```

Note:

- `readline.py` is a local compatibility stub.
- It exists because this macOS/conda Python environment crashes on native `import readline` during pytest startup.
- The application does not depend on readline.

## Step 11C: Documents and Recent Updates Endpoints

Step 11C adds read-only endpoints for browsing stored documents.

Why this exists:

- users need to see which public documents were ingested
- the frontend needs a way to show recent updates
- document detail should show the original text and retrieval chunks

Files added or updated:

```text
backend/api/documents.py
backend/main.py
tests/test_api.py
README.md
RUNBOOK.md
```

List documents:

```bash
curl http://127.0.0.1:8000/documents
```

Pretty-print documents:

```bash
curl -s http://127.0.0.1:8000/documents | python -m json.tool
```

Limit document count:

```bash
curl "http://127.0.0.1:8000/documents?limit=5"
```

Get one document with text and chunks:

```bash
curl -s http://127.0.0.1:8000/documents/1 | python -m json.tool
```

Get recent updates:

```bash
curl -s http://127.0.0.1:8000/recent-updates | python -m json.tool
```

Limit recent updates:

```bash
curl "http://127.0.0.1:8000/recent-updates?limit=5"
```

Response fields for document lists:

```text
id
title
source_name
source_url
publication_date
created_at
text_length
chunk_count
```

Extra fields for document detail:

```text
text
chunks
```

## Step 11D: Streamlit UI Polish

Step 11D improves the frontend with document browsing.

What changed:

- added a `Recent Updates` tab
- recent updates call `GET /recent-updates`
- document inspection calls `GET /documents/{document_id}`
- document summaries show source, chunk count, text length, and source link
- document detail can show stored text and chunks

Run backend:

```bash
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Run frontend:

```bash
.venv/bin/python -m streamlit run frontend/app.py --server.port 8502
```

Open:

```text
http://localhost:8502
```

Quick frontend API helper check:

```bash
python - <<'PY'
from frontend.app import api_get

updates = api_get("/recent-updates?limit=2")
print("updates:", len(updates))

if updates:
    detail = api_get(f"/documents/{updates[0]['id']}")
    print("title:", detail["title"])
    print("chunks:", len(detail["chunks"]))
PY
```

## Step 12: Dockerize Backend and Frontend

Step 12 adds Docker support for the local application stack.

Why this exists:

- Docker makes the backend/frontend run the same way on another machine
- Docker Compose starts OpenSearch, FastAPI, and Streamlit together
- the backend container needs Docker-specific config because `localhost` inside a container is not your Mac

Files added or updated:

```text
.dockerignore
configs/docker.yaml
infra/backend.Dockerfile
infra/frontend.Dockerfile
infra/docker-compose.yml
README.md
RUNBOOK.md
```

Build and start the full stack:

```bash
docker compose -f infra/docker-compose.yml up --build
```

Run in the background:

```bash
docker compose -f infra/docker-compose.yml up --build -d
```

Run in the background with `.env` loaded for OpenAI mode:

```bash
docker compose --env-file .env -f infra/docker-compose.yml up --build -d
```

Check running services:

```bash
docker compose -f infra/docker-compose.yml ps
```

Open services:

```text
Backend:  http://127.0.0.1:8000
Frontend: http://127.0.0.1:8502
OpenSearch: http://127.0.0.1:9200
```

Check backend:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/diagnostics
```

Stop services:

```bash
docker compose -f infra/docker-compose.yml down
```

Stop services and delete Docker volumes:

```bash
docker compose -f infra/docker-compose.yml down -v
```

Important notes:

- `configs/local.yaml` is for running directly on your machine.
- `configs/docker.yaml` is for containers.
- The Docker backend uses `http://opensearch:9200` because `opensearch` is the Compose service name.
- The Docker backend uses deterministic hash embeddings to keep the container lightweight.
- OpenAI mode needs `.env` loaded with `docker compose --env-file .env ...`.
- The backend data volume is separate from your local `data/app.db`.
- The Docker OpenSearch volume is separate from your existing local OpenSearch data.
- After starting a fresh Docker stack, you may need to run ingestion, chunking, index creation, and indexing inside the backend container before query answers have evidence.

Run a backend command inside Docker:

```bash
docker compose -f infra/docker-compose.yml exec backend python -m backend.indexing.manage_index
```

Ingest recent source data from the last 7 days:

```bash
docker compose --env-file .env -f infra/docker-compose.yml exec -T backend \
  python -m backend.ingestion.recent --days 7 --source all --limit 50 --recreate-index
```

Available source keys:

```text
sec_press        -> https://www.sec.gov/news/pressreleases.rss
sec_edgar        -> https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&count=100&output=atom
fca_news         -> https://www.fca.org.uk/news
fca_publications -> https://www.fca.org.uk/publications
boe_news         -> https://www.bankofengland.co.uk/rss/news
boe_publications -> https://www.bankofengland.co.uk/rss/publications
boe_prudential   -> https://www.bankofengland.co.uk/rss/prudential-regulation-publications
```

Source notes:

- SEC automated requests should include `FINREG_USER_AGENT` with contact information.
- GDELT is not part of the active source set because the public API was unreliable during smoke testing.
- Do not run multiple ingestion commands with `--recreate-index` at the same time.

Ingest only SEC press releases:

```bash
docker compose --env-file .env -f infra/docker-compose.yml exec -T backend \
  python -m backend.ingestion.recent --days 7 --source sec_press --limit 50 --recreate-index
```

Ingest only SEC EDGAR current filings:

```bash
docker compose --env-file .env -f infra/docker-compose.yml exec -T backend \
  python -m backend.ingestion.recent --days 7 --source sec_edgar --limit 50 --recreate-index
```

Ingest FCA news as individual item pages:

```bash
docker compose --env-file .env -f infra/docker-compose.yml exec -T backend \
  python -m backend.ingestion.recent --days 7 --source fca_news --recreate-index
```

Ingest FCA publications as individual item pages:

```bash
docker compose --env-file .env -f infra/docker-compose.yml exec -T backend \
  python -m backend.ingestion.recent --days 7 --source fca_publications --recreate-index
```

Ingest only Bank of England PRA publications:

```bash
docker compose --env-file .env -f infra/docker-compose.yml exec -T backend \
  python -m backend.ingestion.recent --days 7 --source boe_prudential --limit 50 --recreate-index
```

Test a Docker API query:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What did the SEC and CFTC publish about derivatives?","top_k":2,"use_llm":false}'
```

## Checks So Far

Run these from the project root after activating `.venv`.

Start backend:

```bash
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude '.venv/*'
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
