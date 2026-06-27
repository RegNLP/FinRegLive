# FinReg Live Intelligence

FinReg Live Intelligence is a source-grounded RAG system for monitoring public financial and regulatory updates, retrieving relevant evidence, and answering questions with citations.

The project is built as a local, cloud-ready prototype using FastAPI, Streamlit, SQLite, OpenSearch, hybrid retrieval, reranking, confidence-based abstention, and an evaluation layer.

## What It Does

- Ingests public regulatory updates from SEC, FCA, and Bank of England sources
- Stores document and chunk metadata in SQLite
- Indexes searchable evidence in OpenSearch
- Supports BM25, vector, and hybrid retrieval
- Applies optional reranking before answer generation
- Classifies questions for route-aware RAG behavior
- Maps query classes to simple, medium, complex, and abstain route policies
- Generates source-grounded answers with citations
- Abstains when evidence is weak, out-of-domain, speculative, or unsupported
- Provides a Streamlit UI for querying, ingestion, diagnostics, analytics, and retrieval inspection
- Runs local evaluation over a saved benchmark question set

## Current Architecture

```text
Public sources
  -> ingestion
  -> cleaning and deduplication
  -> chunking
  -> SQLite metadata storage
  -> OpenSearch indexing
  -> query classification
  -> route policy selection
  -> hybrid retrieval
  -> optional reranking
  -> confidence and abstention gate
  -> source-grounded generation
  -> answer with citations
  -> feedback and evaluation
```

Detailed diagrams are available in [ARCHITECTURE.md](ARCHITECTURE.md).

The original step-by-step development notes are preserved in [DEBUGGING_NOTES.md](DEBUGGING_NOTES.md).

General RAG learning notes are available in [LEARNING_MATERIALS.md](LEARNING_MATERIALS.md).

## Data Sources

Current source coverage includes:

- SEC press releases RSS
- SEC EDGAR current filings feed
- FCA news item pages
- FCA publication item pages
- Bank of England news RSS
- Bank of England publications RSS
- Bank of England Prudential Regulation publications RSS

## Tech Stack

| Layer | Tools |
| --- | --- |
| Backend | FastAPI, Pydantic, Uvicorn |
| Frontend | Streamlit |
| Database | SQLite with SQLModel |
| Search | OpenSearch |
| Retrieval | BM25, dense embeddings, reciprocal rank fusion |
| Reranking | Local lexical reranker |
| Generation | Local evidence formatter, optional OpenAI generation |
| Evaluation | JSONL benchmark runner, local metrics |
| Deployment | Docker Compose |

## Repository Structure

```text
backend/
  api/             FastAPI routes
  database/        SQLModel models and CRUD helpers
  generation/      answer generation, confidence gate, prompts
  indexing/        embeddings and OpenSearch indexing
  ingestion/       RSS, HTML, FCA item-level ingestion
  processing/      chunking pipeline
  reranking/       reranking logic
  retrieval/       BM25, vector, and hybrid retrieval
  search/          OpenSearch client

frontend/          Streamlit dashboard
evaluation/        benchmark questions and evaluation runner
infra/             Dockerfiles and Docker Compose
configs/           local configuration
tests/             pytest coverage
```

## Quick Start

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create local environment variables:

```bash
cp .env.example .env
```

If using OpenAI generation, add `OPENAI_API_KEY` to `.env`.

Start the local stack:

```bash
docker compose --env-file .env -f infra/docker-compose.yml up --build -d
```

Open the app:

```text
http://127.0.0.1:8502
```

Backend health check:

```bash
curl http://127.0.0.1:8000/health
```

## Common Commands

Fetch recent documents:

```bash
docker compose --env-file .env -f infra/docker-compose.yml exec -T backend \
  python -m backend.ingestion.recent --days 7 --source all --limit 20 --recreate-index
```

Ask a local source-grounded question:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"What recent FCA updates mention listing rules or investment funds?","top_k":3,"use_llm":false,"use_reranking":true}'
```

Compare retrieval methods:

```bash
curl -X POST http://127.0.0.1:8000/retrieval/diagnostics \
  -H 'Content-Type: application/json' \
  -d '{"question":"What recent SEC or CFTC updates mention derivatives or swaps?","top_k":5}'
```

Run the basic evaluation layer:

```bash
python -m evaluation.run_basic --top-k 5
```

More operational commands are in [RUNBOOK.md](RUNBOOK.md).

## API Highlights

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Backend health check |
| `GET /diagnostics` | Database and OpenSearch diagnostics |
| `POST /query` | Source-grounded question answering |
| `POST /feedback` | Store user feedback for a query |
| `GET /documents` | List stored documents |
| `GET /documents/{document_id}` | Inspect one document and its chunks |
| `GET /recent-updates` | Show recent documents |
| `POST /ingest/recent` | Fetch and index recent source updates |
| `GET /analytics/corpus` | Corpus coverage and ingestion analytics |
| `POST /retrieval/diagnostics` | Compare BM25, vector, and hybrid retrieval |

## Evaluation Status

The project includes `evaluation/questions.jsonl` with 30 benchmark questions covering:

- answerable regulatory questions
- multi-source questions
- unanswerable in-domain questions
- out-of-domain questions
- ambiguous questions
- adversarial questions

The current basic evaluation layer measures:

- source count
- duplicate sources
- answer length
- latency
- abstention behavior
- source overlap between hybrid and reranked retrieval

Latest observed behavior after adding the confidence gate:

```text
out-of-domain questions:        5/5 abstained
in-domain unanswerable:         5/5 abstained
adversarial questions:          4/4 abstained
in-domain answerable questions: 0/8 abstained
```

## Roadmap

Next planned architecture work:

- Evidence diagnostics
- Route-aware generation
- Verification and fallback
- LLM-as-a-judge evaluation
- RAGAS experiment
- DeepEval experiment
- Cloud-ready deployment mapping

## Cloud-Ready Direction

The local components are designed to map cleanly to managed services:

| Local | Cloud target |
| --- | --- |
| SQLite | Amazon RDS PostgreSQL |
| OpenSearch container | Amazon OpenSearch Service |
| FastAPI container | ECS/Fargate |
| Streamlit container | ECS/Fargate or hosted Streamlit |
| `.env` | AWS Secrets Manager |
| local logs | CloudWatch |
| manual ingestion | EventBridge scheduled task |

## Safety Note

The system provides source-grounded regulatory intelligence from public data. It is not legal, financial, or investment advice.
