# FinReg Live Intelligence

FinReg Live Intelligence is a production-oriented RAG system for monitoring, searching, and querying public financial and regulatory information.

The system will collect public updates from financial and regulatory sources, process them into searchable evidence, and answer user questions with source-grounded responses. The first implementation will run locally, while the architecture will be designed so the same components can later map to AWS services.

## Problem

Financial and regulatory information changes frequently. Users need a way to monitor recent public updates and ask questions such as:

- What are the latest regulatory updates related to AML?
- What has the FCA published recently?
- Which recent sources mention liquidity risk?
- What evidence supports this answer?
- Show recent public sources related to consumer duty.

The system should not invent unsupported answers. It should retrieve evidence first, generate an answer from that evidence, and show the sources used.

## Core Workflow

```text
Public sources
  -> ingestion
  -> cleaning and deduplication
  -> document chunking
  -> metadata storage
  -> search indexing
  -> retrieval
  -> source-grounded answer generation
  -> evidence display
  -> query logging and feedback
```

## Main Features

- Ingest public RSS, HTML, and PDF sources
- Deduplicate documents using content hashes
- Clean and chunk document text
- Store document, chunk, query, answer, and feedback metadata
- Index chunks in OpenSearch
- Support BM25 keyword search
- Support vector search
- Support hybrid retrieval
- Generate answers using only retrieved evidence
- Show citations and evidence snippets
- Log queries, retrieval settings, latency, and retrieved chunk IDs
- Collect user feedback on usefulness, correctness, and evidence quality
- Provide a dashboard for asking questions, inspecting evidence, and checking diagnostics
- Run locally with Docker Compose
- Keep configuration ready for a later AWS deployment

## Technology Stack

### Language

- Python

### Backend

- FastAPI
- Pydantic
- Uvicorn

### Frontend

- Streamlit

### Ingestion

- requests
- feedparser
- BeautifulSoup
- pypdf

### Processing

- text cleaning
- chunking
- metadata enrichment
- content hashing

### Search and Retrieval

- OpenSearch
- BM25 search
- vector search
- hybrid retrieval

### Database

Local:

- SQLite

Cloud target:

- Amazon RDS PostgreSQL

### LLM Layer

Local/API option:

- OpenAI API

Possible cloud option:

- AWS Bedrock

### Local Deployment

- Docker
- Docker Compose

### Cloud-Ready Mapping

- Local files -> Amazon S3
- SQLite/PostgreSQL -> Amazon RDS PostgreSQL
- Local OpenSearch -> Amazon OpenSearch Service
- FastAPI container -> Amazon ECS/Fargate
- Streamlit container -> ECS/Fargate or hosted Streamlit
- `.env` file -> AWS Secrets Manager
- Local logs -> Amazon CloudWatch
- Local scheduler -> EventBridge scheduled task

### Testing

- pytest

## Planned API Endpoints

```text
GET  /health
POST /ingest
POST /query
GET  /documents
GET  /documents/{document_id}
GET  /recent-updates
POST /feedback
GET  /diagnostics
```

## Planned User Interface

The Streamlit dashboard will include:

- Ask page
- Recent updates page
- Evidence viewer
- Feedback page
- Diagnostics page

## Local MVP Scope

The first working version should include:

- FastAPI backend
- Streamlit frontend
- RSS or HTML ingestion from a small number of public sources
- deduplication
- chunking
- SQLite metadata storage
- OpenSearch indexing
- BM25 retrieval
- basic vector or hybrid retrieval
- source-grounded answer generation
- evidence display
- query logging
- feedback collection
- Docker Compose setup
- basic tests

## Out of Scope for Version 1

The first version will not include:

- complex authentication
- React frontend
- Kafka
- Kubernetes
- fine-tuning
- agentic workflows
- RLHF
- large-scale evaluation
- full AWS deployment automation

## Build Phases

This project will be built step by step. Each phase has one clear learning goal, one technical outcome, and one checkpoint before moving forward.

## Current Status

Completed:

- Phase 0: Project understanding
- Phase 1: FastAPI foundation and `/health`
- Phase 2: configuration loading from `configs/local.yaml`
- Phase 3: SQLite data models and basic CRUD helpers
- Phase 4: RSS/HTML ingestion and text deduplication
- Phase 4b: storing ingested documents and skipping duplicates
- Phase 5: word-based chunking and chunk storage
- Phase 6A: local OpenSearch service with Docker Compose
- Phase 6B: OpenSearch Python client
- Phase 6C: OpenSearch index schema
- Phase 6D: local embedding generation
- Phase 6E: indexing chunks into OpenSearch
- Phase 6F: manual BM25 and vector search checks
- Phase 7: BM25, vector, and hybrid retrieval
- Phase 8: local source-grounded answer generation
- Phase 8b: optional OpenAI source-grounded answer generation

Current working flow:

```text
SEC RSS / FCA HTML
  -> IngestedDocument
  -> content hash
  -> duplicate check
  -> SQLite Document row
  -> word-based chunks
  -> SQLite Chunk rows
  -> local embeddings
  -> OpenSearch chunk index
  -> BM25/vector search checks
  -> reusable retrieval functions
  -> source-grounded answer with citations
  -> optional OpenAI answer generation
```

Not built yet:

- Streamlit frontend
- full Docker setup for backend/frontend

### Phase 0: Project Understanding

Goal:

- Understand the purpose of the system before writing code
- Understand what RAG means in this project
- Understand the difference between ingestion, retrieval, generation, and feedback

Deliverables:

- README as the source of truth
- Initial architecture explanation
- Local MVP scope agreed

Checkpoint:

- We can explain the project workflow without looking at code

### Phase 1: Project Foundation

Goal:

- Create a clean Python project structure
- Understand why each folder exists
- Run the first backend endpoint locally

Deliverables:

- `backend/`
- `backend/main.py`
- `requirements.txt`
- `.gitignore`
- basic FastAPI app
- `GET /health` endpoint

Tools:

- Python
- FastAPI
- Uvicorn

Checkpoint:

- Running `uvicorn backend.main:app --reload` starts the API
- Visiting `/health` returns a simple success response

### Phase 2: Configuration and Environment

Goal:

- Learn how applications separate code from environment-specific settings
- Prepare local settings without hardcoding secrets or paths

Deliverables:

- `.env.example`
- `configs/local.yaml`
- configuration loader

Tools:

- environment variables
- YAML
- Pydantic settings or a simple config loader

Checkpoint:

- The backend can read local configuration
- Secret values are not committed to the project

### Phase 3: Data Model and Storage

- Define documents table
- Define chunks table
- Define query logs table
- Define feedback table
- Add SQLite database setup

Goal:

- Understand what metadata the system must remember
- Store documents, chunks, queries, and feedback in a local database

Deliverables:

- `backend/database/`
- database models
- database initialization
- simple create/read functions

Tools:

- SQLite
- SQLModel or SQLAlchemy

Checkpoint:

- The app can create the database locally
- We can store and retrieve a document record

Why a database is needed:

- The system must remember which public documents were ingested
- The system must keep document metadata for filtering and citations
- The system must track chunks created from each document
- The system must log user queries for debugging and evaluation
- The system must store feedback for future improvement

Why SQLite first:

- It is simple and local
- It does not require a separate database server
- It is enough for the first working version
- It can later be replaced by PostgreSQL with the same general data model

Why SQLModel:

- It works well with FastAPI
- It combines Pydantic-style models with SQL database tables
- It is easier to learn than raw SQLAlchemy
- It still uses SQLAlchemy underneath, so the concepts transfer to more advanced systems

### Phase 4: Ingestion

- Add RSS ingestion
- Add HTML ingestion
- Add PDF parsing
- Add text cleaning
- Add deduplication with content hashes

Goal:

- Fetch public regulatory or financial content
- Convert messy source content into clean text
- Avoid storing duplicate documents

Deliverables:

- `backend/ingestion/`
- RSS ingestor
- HTML ingestor
- basic PDF parser
- deduplication helper

Tools:

- requests
- feedparser
- BeautifulSoup
- pypdf
- hashlib

Checkpoint:

- The system can ingest at least one public source
- Re-ingesting the same content skips duplicates

Initial sources:

- SEC press releases RSS feed: `https://www.sec.gov/news/pressreleases.rss`
- FCA news/publications HTML pages: `https://www.fca.org.uk/news` and `https://www.fca.org.uk/publications`

Why these sources:

- They are official public sources
- They are relevant to financial and regulatory monitoring
- SEC provides RSS, which is easier to parse reliably
- FCA pages are useful for HTML ingestion practice

Why start with only a few sources:

- It keeps the ingestion pipeline understandable
- It makes debugging easier
- It avoids mixing source-specific problems before the core pipeline works
- More sources can be added once the first pipeline is stable

### Phase 4b: Store Ingested Documents

Goal:

- Connect ingestion output to the database
- Store only new documents
- Skip documents already seen before

Deliverables:

- `backend/ingestion/store.py`
- database helper for finding a document by content hash

Tools:

- SQLModel
- SHA-256 content hashes

Checkpoint:

- First run stores SEC RSS documents
- Second run with the same feed marks the same documents as duplicates

Why this bridge step exists:

- Ingestion alone only fetches temporary Python objects
- The database needs persistent records for later chunking
- Deduplication should happen before chunking and indexing to avoid duplicate evidence

### Phase 5: Chunking and Metadata

- Split documents into chunks
- Attach metadata to each chunk

Goal:

- Understand why long documents must be split before retrieval
- Preserve source metadata for citations

Deliverables:

- `backend/processing/`
- chunker
- chunk-building helper
- document text stored in the `Document` table
- chunk rows stored in the `Chunk` table

Tools:

- Python text processing

Checkpoint:

- A document can be split into valid chunks
- Each chunk keeps a link to its source document

Why chunking is needed:

- Regulatory and financial documents can be too long to retrieve or pass to an LLM as one block
- Smaller chunks make search results more precise
- Overlap keeps context from being lost between chunk boundaries
- Each chunk can later become one searchable evidence item

Current chunking strategy:

- Split by words
- Use `chunk_size_words` from `configs/local.yaml`
- Use `chunk_overlap_words` from `configs/local.yaml`
- Store each chunk with `document_id` and `chunk_index`

### Phase 6: Search Indexing

Goal:

- Move from database storage to searchable evidence
- Understand why OpenSearch is used instead of only a database

Deliverables:

- `backend/search/`
- `backend/indexing/`
- OpenSearch client
- index schema
- embedding helper
- indexing function
- Docker Compose file for local OpenSearch

Tools:

- OpenSearch
- Docker
- opensearch-py
- sentence-transformers

Checkpoint:

- OpenSearch runs locally
- Chunks can be indexed and searched

Phase 6 will be split into smaller steps:

#### Phase 6A: Local OpenSearch Service

Goal:

- Run OpenSearch locally as a separate search service

Deliverables:

- `infra/docker-compose.yml`

Checkpoint:

- `curl http://localhost:9200` returns an OpenSearch response

Note:

- This requires Docker Desktop. Until Docker Desktop is installed and running, this phase can be planned but not executed locally.

#### Phase 6B: OpenSearch Python Client

Goal:

- Let backend code connect to OpenSearch

Deliverables:

- `backend/search/__init__.py`
- `backend/search/client.py`

Checkpoint:

- Python can ping OpenSearch successfully

#### Phase 6C: Index Schema

Goal:

- Define how chunk records are stored in OpenSearch

Deliverables:

- `backend/indexing/__init__.py`
- `backend/indexing/schema.py`

Fields:

- `chunk_id`
- `document_id`
- `chunk_index`
- `chunk_text`
- `title`
- `source_name`
- `source_url`
- `publication_date`
- `embedding`

Checkpoint:

- The `finreg_chunks` index can be created

#### Phase 6D: Embeddings

Goal:

- Generate vector embeddings for chunk text

Deliverables:

- `backend/indexing/embeddings.py`

Initial model:

- `BAAI/bge-small-en-v1.5`

Embedding dimension:

- `384`

Checkpoint:

- A chunk text can be converted into a 384-dimensional vector

#### Phase 6E: Index Chunks

Goal:

- Read chunks from SQLite and send them to OpenSearch

Deliverables:

- `backend/indexing/index_chunks.py`

Checkpoint:

- Stored chunks are indexed into OpenSearch with metadata and embeddings

#### Phase 6F: Manual Search Checks

Goal:

- Confirm OpenSearch can retrieve indexed chunks

Checks:

- BM25 text search
- vector search
- later hybrid search

Checkpoint:

- A manual search returns relevant indexed chunks

### Phase 7: Retrieval

- Implement BM25 search
- Implement vector search
- Implement hybrid retrieval
- Add filters for source, date, and document type

Goal:

- Understand how the system finds evidence before calling an LLM
- Compare keyword, vector, and hybrid retrieval

Deliverables:

- `backend/retrieval/`
- BM25 retrieval
- vector retrieval
- hybrid retrieval
- retrieval filters

Tools:

- OpenSearch BM25
- embeddings

Checkpoint:

- A user query returns ranked evidence chunks
- Retrieved evidence includes source metadata

### Phase 8: Answer Generation

- Build grounded prompt template
- Connect LLM client
- Generate answers only from retrieved evidence
- Return citations and limitations

Goal:

- Use retrieved evidence to generate an answer
- Prevent unsupported answers
- Return citations and limitations

Deliverables:

- `backend/generation/`
- prompt template
- LLM client
- answer generator

Tools:

- OpenAI API or local stub first

Checkpoint:

- The answer cites retrieved evidence
- The system says when evidence is insufficient

### Phase 9: API Layer

Goal:

- Expose the system through backend endpoints
- Keep UI, retrieval, ingestion, and storage separated

Deliverables:

- `backend/api/`
- `/ingest`
- `/query`
- `/documents`
- `/feedback`
- `/diagnostics`

Tools:

- FastAPI routers
- Pydantic request and response models

Checkpoint:

- API responses have predictable JSON structure
- Endpoints can be tested without the frontend

### Phase 10: User Interface

- Build Ask page
- Build evidence panel
- Build recent updates page
- Build feedback page
- Build diagnostics page

Goal:

- Create a usable dashboard for interacting with the backend
- Show answers, citations, evidence, and diagnostics clearly

Deliverables:

- `frontend/`
- Streamlit app
- Ask page
- Recent updates page
- Evidence viewer
- Feedback page
- Diagnostics page

Tools:

- Streamlit
- requests

Checkpoint:

- A user can ask a question through the UI
- Evidence is visible and inspectable

### Phase 11: Docker and Local Deployment

- Add Dockerfiles
- Add Docker Compose

Goal:

- Run the system consistently without manual setup
- Separate backend, frontend, database/search services

Deliverables:

- `infra/`
- backend Dockerfile
- frontend Dockerfile
- Docker Compose file

Tools:

- Docker
- Docker Compose

Checkpoint:

- One command starts the local application stack

### Phase 12: Cloud-Ready Design

- Document AWS service mapping
- Document secrets, logging, and scheduled ingestion strategy

Goal:

- Show how local components map to AWS services
- Prepare the codebase for future cloud deployment

Deliverables:

- `docs/cloud_mapping.md`
- AWS architecture notes
- secrets strategy
- logging strategy
- scheduled ingestion strategy

Tools:

- AWS S3
- Amazon RDS
- Amazon OpenSearch Service
- ECS/Fargate
- Secrets Manager
- CloudWatch
- EventBridge

Checkpoint:

- Each local component has a clear AWS equivalent

### Phase 13: Testing and Documentation

- Add tests for ingestion
- Add tests for deduplication
- Add tests for chunking
- Add tests for query response structure
- Add tests for feedback storage
- Improve README and architecture documentation

Goal:

- Make the system safer to change
- Document decisions clearly

Deliverables:

- `tests/`
- pytest setup
- focused unit and API tests
- architecture documentation
- limitations documentation

Tools:

- pytest
- FastAPI TestClient

Checkpoint:

- Tests pass locally
- README explains how to run and understand the system

## Working Method

For each phase, we will follow the same process:

1. Explain the concept.
2. Decide the files we need.
3. Write the smallest useful code.
4. Run it locally.
5. Test it.
6. Review what each line does.
7. Update documentation before moving on.

We will not add a new layer until the current layer is understood.

## Design Principle

The answer generation step must always be grounded in retrieved evidence. If the system does not retrieve enough evidence, it should say that the evidence is insufficient instead of producing an unsupported answer.
