# FinReg Live Intelligence Development and Debugging Notes

This file preserves the detailed step-by-step project notes, build phases,
learning explanations, and debugging context. The concise project overview is
now in [README.md](README.md).

# Original Project Notes

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

## Architecture Diagrams

Detailed Mermaid diagrams are available in [ARCHITECTURE.md](ARCHITECTURE.md).
They include the general architecture, ingestion pipeline, route-aware query
flow, retrieval/reranking detail, evidence diagnostics, verification/fallback,
evaluation layers, and local-to-cloud mapping.

## Target Route-Aware RAG Architecture

The next architecture will make the RAG pipeline route-aware. Instead of using
the same retrieval, context size, model, and verification strategy for every
question, the system will classify the query and choose a cost-appropriate path.

```text
User question
  -> query classifier
  -> hybrid retrieval
       -> BM25
       -> dense embeddings
       -> reciprocal rank fusion
  -> reranker
  -> evidence diagnostics
       -> top-k relevance
       -> score margin
       -> source document spread
       -> number of strong passages
       -> cross-reference presence
       -> risk markers
  -> route decision
       -> simple route
       -> medium route
       -> complex route
       -> abstain route
  -> generation
  -> verification
       -> citation check
       -> faithfulness check
       -> answerability check
       -> optional judge
  -> final answer or fallback
```

### Query Classes

- `definition_lookup`: definitions, short lookups, abbreviations, and simple explanations
- `obligation_question`: duties, requirements, notifications, reporting, and compliance obligations
- `comparison_question`: compare two rules, regulators, sections, or obligations
- `multi_hop_cross_reference`: questions that need multiple sections or linked evidence
- `compliance_decision`: approval, exemption, threshold, deadline, penalty, or decision-style questions
- `out_of_domain`: questions outside the indexed financial/regulatory corpus
- `general_question`: low-confidence fallback for questions that do not match a specific rule

### Runtime Routes

Route A: simple lookup

- Use for definitions, short explanations, and single-point lookups
- Retrieve with BM25 + dense retrieval + RRF
- Use top-3 evidence chunks
- Use a cheap/fast model or local answer mode
- Require citations
- Do not run an LLM judge

Route B: medium reasoning

- Use for obligations, summaries, and comparison questions
- Retrieve with BM25 + dense retrieval + RRF
- Apply reranking
- Use top-8 evidence chunks
- Use a medium model
- Run citation check
- Fallback if evidence is unsupported

Route C: complex or high-risk regulatory reasoning

- Use for compliance decisions, exceptions, thresholds, deadlines, approvals, penalties, or multi-hop legal/regulatory reasoning
- Retrieve with BM25 + dense retrieval + RRF
- Apply reranking
- Expand cross-references where possible
- Use top-12 to top-15 evidence chunks
- Use a stronger reasoning model
- Run citation verification
- Run LLM-as-a-judge
- Abstain if evidence is weak

Route D: low-evidence or out-of-domain

- Use when the question is outside the corpus or retrieval confidence is weak
- Do not generate a normal answer
- Return an abstention explaining that the answer is not supported by the indexed corpus

### Fallback Policy

The system should not retry forever. The first version will use `max_retry = 1`.

```text
generate answer
  -> verification check
       -> pass: return answer
       -> fail: fallback once
            -> increase top-k
            -> use reranker
            -> use stronger route/model
            -> regenerate or abstain
```

Examples:

- Simple route fails citation check -> fallback to medium route
- Medium route judge says unsupported -> fallback to complex route
- Complex route still fails -> abstain

### Cost Controls

- Model choice: simple uses cheaper generation, medium uses stronger generation, complex uses the strongest available reasoning mode
- Context budget: simple top-3, medium top-8, complex top-12/top-15
- Verification budget: simple citation check only, medium citation and answerability checks, complex citation check plus LLM-as-a-judge

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
- Phase 9A: FastAPI `/query` endpoint for local and OpenAI answer generation
- Phase 9B: query logging for `/query` requests
- Phase 9C: feedback API connected to saved query IDs
- Phase 9D: diagnostics API for database and OpenSearch status
- Phase 10: Streamlit frontend for query, sources, feedback, and diagnostics
- Phase 11A: API validation and cleaner service error responses
- Phase 11B: pytest coverage for chunking, deduplication, and API behavior
- Phase 11C: document and recent update API endpoints
- Phase 11D: Streamlit UI polish with recent updates and document inspection
- Phase 12: Docker Compose setup for OpenSearch, backend, and frontend
- Recent ingestion command for SEC, FCA, and Bank of England sources
- Evaluation question set in `evaluation/questions.jsonl`
- Phase 13: FCA item-level ingestion for news and publications
- Phase 14A/14B: corpus analytics endpoint and Streamlit Analytics tab
- Phase 14C: ingestion run tracking with recent run history
- Phase 15: retrieval diagnostics API and Streamlit Retrieval tab
- Phase 16: local lexical reranking for hybrid retrieval candidates
- Phase 17A: basic local evaluation runner
- Phase 17A fix: confidence and abstention gate
- Phase 18A: rule-based query classifier
- Phase 18B: route policy mapping
- Phase 18C: evidence diagnostics module
- Phase 18D: route-aware local answer pipeline

Current working flow:

```text
SEC RSS / SEC EDGAR / FCA item pages / Bank of England RSS
  -> recent ingestion command
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
  -> FastAPI /query endpoint
  -> SQLite query log
  -> feedback storage
  -> diagnostics checks
  -> Streamlit user interface
  -> API quality checks
  -> automated tests
  -> document browsing endpoints
  -> recent updates UI
  -> UI-triggered ingestion
  -> corpus analytics
  -> ingestion run history
  -> retrieval diagnostics
  -> query classification
  -> route policy selection
  -> evidence diagnostics
  -> route-aware local answer pipeline
  -> optional reranking before answer generation
  -> confidence and abstention gate
  -> basic local evaluation
  -> Docker Compose local stack
```

Not built yet:

- live `/query` integration for route-aware generation
- verification and fallback
- evaluation layer 2: LLM-as-a-judge
- evaluation layer 3: RAGAS experiment
- evaluation layer 4: DeepEval experiment
- scheduled ingestion
- cloud deployment

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

- Running `.venv/bin/python -m uvicorn backend.main:app --reload` starts the API
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

### Phase 12: Docker and Local Deployment

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

### Phase 13: FCA Item-Level Ingestion

Goal:

- Replace FCA listing-page snapshots with individual FCA article/publication documents
- Increase corpus quality before increasing corpus size

Deliverables:

- FCA listing parser
- FCA item URL extraction
- item-level HTML fetching
- deduplication using existing content hashes
- smoke test showing FCA item documents, chunks, and indexed chunks

Checkpoint:

- FCA queries retrieve individual FCA pages instead of broad listing-page snapshots

### Phase 14: Corpus and Ingestion Analytics

Goal:

- Make the data pipeline observable
- Show source coverage and ingestion health

Deliverables:

- source-level document counts
- chunk counts by source
- duplicate counts
- latest ingestion time
- failed ingestion attempts
- diagnostics/API or UI view for corpus health

Checkpoint:

- We can quickly answer what data exists, when it was ingested, and which sources failed

### Phase 15: Retrieval Diagnostics

Goal:

- Make retrieval behavior visible and comparable

Deliverables:

- BM25 vs vector vs hybrid comparison for the same query
- retrieved chunk score display
- overlap metrics showing where retrieval methods agree

Checkpoint:

- We can explain why a query retrieved specific evidence

### Phase 16: Reranking

Goal:

- Improve evidence ranking after the first hybrid retrieval step
- Reduce weak or off-topic chunks before answer generation

Deliverables:

- reranking module
- reranker applied after hybrid retrieval
- optional `/query` setting for reranking
- Streamlit toggle for reranking
- tests comparing reranked and non-reranked behavior

Checkpoint:

- We can retrieve more candidates than needed, rerank them, and pass the strongest chunks to generation

### Phase 17: Evaluation Layer

Goal:

- Evaluate answer quality instead of only manually testing the app

The evaluation layer will be built in four maturity levels. Each level adds
more judgment quality, but also more cost, dependency weight, or complexity.

### Phase 17A: Evaluation Layer 1 - Basic Local Evaluation

Goal:

- Create a fast, repeatable evaluation baseline without using another LLM

Deliverables:

- `evaluation/questions.jsonl`
- local evaluation runner
- result files under `evaluation/results/`
- hybrid vs hybrid-reranked comparison
- basic metrics: source count, duplicate sources, empty answers, abstention detection, answer length, latency, and source overlap

Checkpoint:

- We can run the same question set repeatedly and compare normal hybrid retrieval against reranked retrieval

### Phase 18A: Query Classifier

Goal:

- Classify each user question before retrieval/generation policy is selected

Deliverables:

- `backend/routing/`
- rule-based query classifier
- query classes: definition lookup, obligation, comparison, multi-hop, compliance decision, out-of-domain, and general question
- tests for representative question types

Checkpoint:

- The system can explain what type of question it received before answering

### Phase 18B: Route Policy

Goal:

- Map query classes to route settings and cost controls

Deliverables:

- route definitions for simple, medium, complex, and abstain
- per-route `top_k`, reranking, model mode, verification level, and judge policy
- route metadata returned in API responses or diagnostics
- `backend/routing/policy.py`
- `backend/routing/route_question.py`
- tests for query class to route policy mapping

Current route mapping:

```text
definition_lookup          -> simple
obligation_question        -> medium
comparison_question        -> medium
general_question           -> medium
multi_hop_cross_reference  -> complex
compliance_decision        -> complex
out_of_domain              -> abstain
```

Current route settings:

```text
simple:
  top_k: 3
  candidate_k: 3
  use_reranking: false
  generation_mode: local
  verification_level: citation
  requires_judge: false
  max_retry: 1

medium:
  top_k: 8
  candidate_k: 20
  use_reranking: true
  generation_mode: medium_model
  verification_level: citation_and_answerability
  requires_judge: false
  max_retry: 1

complex:
  top_k: 12
  candidate_k: 30
  use_reranking: true
  generation_mode: strong_model
  verification_level: strict_with_judge
  requires_judge: true
  max_retry: 1

abstain:
  top_k: 0
  candidate_k: 0
  use_reranking: false
  generation_mode: none
  verification_level: none
  requires_judge: false
  max_retry: 0
```

Manual check:

```bash
python -m backend.routing.route_question "Does the firm need approval if its controller structure changes?"
```

Checkpoint:

- The same `/query` flow can choose different retrieval and verification settings by route

### Phase 18C: Evidence Diagnostics

Goal:

- Measure retrieved evidence quality before answer generation

Deliverables:

- top-k relevance summary
- score margin
- source document spread
- strong passage count
- cross-reference indicators
- risk markers for high-stakes regulatory questions
- integration with the existing confidence gate
- `backend/evidence/diagnostics.py`
- `EvidenceDiagnostics` dataclass
- evidence strength labels: `none`, `weak`, `moderate`, `strong`
- tests for empty evidence, strong evidence, document spread, duplicate documents, cross-reference signals, risk markers, and serialization

Current diagnostics fields:

```text
route_name
retrieved_count
top_score
score_margin
source_document_count
duplicate_document_count
source_name_count
strong_passage_count
max_token_overlap
avg_token_overlap
has_cross_reference_signal
risk_markers
evidence_strength
reasons
```

Important design note:

- Evidence diagnostics does not generate an answer.
- Evidence diagnostics does not call an LLM.
- It only measures the retrieved evidence so later route-aware generation,
  verification, and fallback can make explainable decisions.

Checkpoint:

- The system can decide whether evidence is strong enough for simple, medium, or complex answering

### Phase 18D: Route-Aware Generation

Goal:

- Generate answers using the route policy selected for the question

Deliverables:

- simple route using small context and low-cost generation
- medium route using reranking and more evidence
- complex route using larger context and stronger generation
- abstain route that avoids unsupported generation
- `backend/pipeline/route_aware_answer.py`
- `RouteAwareAnswer` dataclass
- route-aware retrieval using route policy `top_k`, `candidate_k`, and `use_reranking`
- evidence diagnostics before generation
- abstention when route is `abstain` or evidence strength is too weak
- local source-grounded generation when evidence passes route checks
- tests for simple, medium, complex, abstain, and metadata serialization

Manual check:

```bash
python -m backend.pipeline.route_aware_answer "What is an Authorised Person?"
```

Important design note:

- Phase 18D creates the route-aware answer pipeline.
- The live `/query` endpoint is not switched to this pipeline yet.
- API wiring should be done after this pipeline is validated independently.

Checkpoint:

- Query behavior changes based on route instead of one fixed pipeline

### Phase 18E: Verification and Fallback

Goal:

- Check generated answers before returning them and retry once when useful

Deliverables:

- citation check
- answerability check
- faithfulness check placeholder
- `max_retry = 1` fallback policy
- simple-to-medium and medium-to-complex fallback behavior
- final abstention when verification still fails

Checkpoint:

- Unsupported answers are caught before final response, and retry cost is bounded

### Phase 19A: Evaluation Layer 2 - LLM-as-a-Judge

Goal:

- Use an LLM to score qualitative answer quality against retrieved evidence

Deliverables:

- judge prompt
- OpenAI-based evaluation runner
- scores for answer relevance, faithfulness, source support, regulatory caution, limitation awareness, and clarity
- saved judge explanations for failure analysis

Checkpoint:

- Each evaluated answer receives structured judge scores and short explanations

### Phase 19B: Evaluation Layer 3 - RAGAS

Goal:

- Experiment with a standard RAG evaluation framework

Deliverables:

- RAGAS evaluation script
- metrics such as faithfulness, answer relevancy, context precision, and context recall where supported
- comparison with the local and LLM-as-a-judge results

Checkpoint:

- RAGAS can run against the project question set and produce reusable metric output

### Phase 19C: Evaluation Layer 4 - DeepEval

Goal:

- Add a second evaluation framework suitable for test-case style checks

Deliverables:

- DeepEval test cases
- hallucination, answer relevance, contextual precision, and contextual recall checks where supported
- custom regulatory QA criteria

Checkpoint:

- DeepEval can run repeatable RAG quality checks that could later be added to CI

### Phase 20: Cloud-Ready Architecture

Goal:

- Show how the local Docker system maps to production infrastructure

Deliverables:

- cloud architecture notes
- FastAPI backend to container service mapping
- Streamlit frontend to container app mapping
- SQLite to PostgreSQL or managed relational database mapping
- OpenSearch container to managed OpenSearch mapping
- `.env` to secrets manager mapping
- scheduled ingestion strategy
- logging and monitoring strategy

Checkpoint:

- Each local component has a clear production equivalent

### Phase 21: Final README and Presentation Rewrite

Goal:

- Present the project clearly for technical reviewers

Deliverables:

- problem statement
- architecture diagram or description
- ingestion pipeline explanation
- retrieval and generation explanation
- evaluation summary
- cloud-ready design summary
- screenshots
- limitations and future work

Checkpoint:

- A reviewer can understand the system, run it, and see why each component exists

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
