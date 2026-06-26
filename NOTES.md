# Notes

## RAG Tool Categories

These tools support different parts of a RAG system. They are not all the same type of tool.

A basic RAG flow looks like this:

```text
documents
  -> chunks
  -> embeddings
  -> storage/index
  -> retrieval
  -> prompt
  -> LLM answer
```

## Vector Databases

A vector database stores embeddings and lets you search by semantic similarity.

Example:

```text
"AML compliance" -> [0.12, -0.04, 0.88, ...]
```

Then it can find chunks with similar meaning, even if the exact words are different.

### Pinecone

Pinecone is a managed vector database.

Use it when:

- you want a cloud-hosted vector database
- you do not want to manage infrastructure
- you need scaling, APIs, namespaces, and metadata filtering

Good for:

- production SaaS RAG
- fast setup
- managed cloud vector search

Tradeoff:

- external paid service
- less infrastructure control

### Weaviate

Weaviate is an open-source vector database with managed/cloud options.

Use it when:

- you want vector search plus metadata filtering
- you want an open-source option
- you want hybrid search features
- you may self-host

Good for:

- semantic search apps
- document search
- hybrid retrieval

### Qdrant

Qdrant is an open-source vector database focused on performance and filtering.

Use it when:

- you want a clean vector database
- you need strong metadata filtering
- you want Docker/self-hosting
- you want simpler operations than some larger search stacks

Good for:

- RAG systems
- recommendation search
- semantic search

### Chroma

Chroma is a lightweight local vector database.

Use it when:

- you are prototyping locally
- you want simple setup
- you are building demos or notebooks

Good for:

- learning
- small local apps
- quick prototypes

Chroma is usually not the first choice for serious production systems.

## Search Engines

Search engines usually support keyword search, filtering, ranking, and sometimes vector search.

### Elasticsearch

Elasticsearch is a popular search engine built on Lucene.

Good at:

- BM25 keyword search
- full-text search
- filters
- aggregations
- logs
- analytics
- large-scale search

Modern Elasticsearch also supports vector search.

Use it when:

- search is central to the product
- you need mature full-text search
- you need filtering, scoring, analytics
- your company already uses Elastic

### OpenSearch

OpenSearch is an open-source fork of Elasticsearch.

It was created after Elastic changed licensing.

Good at:

- BM25 search
- metadata filtering
- vector k-NN search
- hybrid search
- log analytics
- AWS integration

Use it when:

- you want Elasticsearch-like functionality
- you want open-source friendly tooling
- you may deploy to AWS OpenSearch Service
- you need both keyword and vector search

For FinRegLive, OpenSearch is a good choice because the project needs:

```text
BM25 + vector + hybrid + metadata filters + AWS mapping
```

## PostgreSQL + pgvector

`pgvector` is a PostgreSQL extension for vector search.

PostgreSQL is a relational database. `pgvector` adds vector columns and similarity search.

Use it when:

- your app already uses PostgreSQL
- your data size is moderate
- you want one database for metadata and vectors
- you do not need a separate search cluster

Good for:

- small to medium RAG systems
- internal tools
- apps where simplicity matters

Tradeoff:

- BM25 and full-text search are not as specialized as OpenSearch
- large vector search may need more tuning

Example design:

```text
documents table
chunks table
embedding vector column
```

Then search inside PostgreSQL.

## Redis

Redis is an in-memory data store. Redis Stack can also support vector search.

Use Redis for:

- caching
- session storage
- rate limiting
- queues
- fast key-value lookup
- temporary memory

Use Redis vector search when:

- you already use Redis
- you need very fast retrieval
- your vector dataset fits the use case

Redis is not usually the first choice as the main document search system for this project.

In RAG, Redis is often used for:

- caching LLM responses
- caching embeddings
- storing chat sessions
- rate limiting API calls
- queueing ingestion jobs

## RAG Frameworks

These are not databases. They help build LLM and RAG pipelines.

### LangChain

LangChain is a framework for building LLM applications.

It provides:

- document loaders
- text splitters
- retrievers
- chains
- agents
- memory
- tool calling helpers
- integrations

Use it when:

- you want many integrations quickly
- you are prototyping
- you need agent/tool workflows
- you want prebuilt pipeline pieces

Tradeoff:

- can become abstract and hard to debug
- fast-changing APIs
- may hide important engineering details

For learning, it is useful. For this project, building the core pieces directly first makes the RAG flow easier to understand.

### LlamaIndex

LlamaIndex is a framework focused on connecting data to LLMs.

It provides:

- data connectors
- indexes
- retrievers
- query engines
- document parsing
- RAG workflows

Use it when:

- your main problem is indexing/querying documents
- you want document ingestion abstractions
- you want to quickly build RAG over many data sources

Tradeoff:

- abstracts many details
- less backend/product-oriented by default

Good for document-heavy RAG prototypes.

## Simple Categories

```text
Vector databases:
Pinecone, Weaviate, Qdrant, Chroma

Search engines:
Elasticsearch, OpenSearch

Relational database with vector extension:
PostgreSQL + pgvector

Cache / fast store:
Redis

LLM/RAG frameworks:
LangChain, LlamaIndex
```

## When To Use What

For a small local learning project:

```text
Chroma or FAISS
```

For a backend app already using PostgreSQL:

```text
PostgreSQL + pgvector
```

For production search with keyword + vector + filters:

```text
OpenSearch or Elasticsearch
```

For managed vector-only infrastructure:

```text
Pinecone
```

For open-source vector database:

```text
Qdrant or Weaviate
```

For fast caching, sessions, or queues:

```text
Redis
```

For quickly assembling RAG workflows:

```text
LangChain or LlamaIndex
```

## Choice For FinRegLive

Best fit:

```text
OpenSearch
```

Why:

- financial/regulatory search needs keyword search
- metadata filters matter
- citations and evidence matter
- hybrid retrieval is useful
- AWS OpenSearch maps well to cloud deployment

OpenSearch lets us practice vector database concepts because it supports vector fields and k-NN search.

For FinRegLive:

```text
SQLite = metadata database for now
OpenSearch = search + vector database
Later PostgreSQL/RDS = production metadata database
```

That gives the project a strong engineering story.

## Other Important Tools

### FAISS

FAISS is a local vector similarity search library from Meta.

Use it when:

- you want fast local vector search
- you are building a notebook or offline prototype
- you do not need a full database server
- metadata filtering is simple or handled separately

Good for:

- learning vector search
- local experiments
- evaluation pipelines

Tradeoff:

- not a full database
- metadata storage must be handled separately
- production deployment requires extra work

FinanceRAG-mini uses FAISS for dense vector retrieval.

### Milvus

Milvus is an open-source vector database designed for large-scale vector search.

Use it when:

- you have large embedding collections
- vector search is the main workload
- you want an open-source vector database with scale-oriented architecture

Good for:

- large semantic search systems
- image/text embedding search
- high-volume vector workloads

Tradeoff:

- more infrastructure complexity than Chroma or Qdrant

### Vespa

Vespa is a search and serving engine for large-scale ranking.

Use it when:

- you need advanced ranking
- you need keyword, vector, and structured retrieval together
- you are building search at serious scale

Good for:

- search platforms
- recommendation systems
- complex ranking pipelines

Tradeoff:

- steeper learning curve
- heavier than needed for most small RAG projects

### Apache Solr

Solr is another Lucene-based search engine.

Use it when:

- an organization already uses Solr
- you need mature full-text search
- you need faceting, filters, and search APIs

Good for:

- enterprise search
- catalog search
- document search

Tradeoff:

- OpenSearch/Elasticsearch are more common in many modern RAG examples

### Azure AI Search

Azure AI Search is a managed search service from Microsoft.

Use it when:

- your cloud stack is Azure
- you want managed keyword, vector, and hybrid search
- you are building enterprise RAG with Azure OpenAI

Good for:

- Azure-based RAG systems
- enterprise document search
- hybrid search with managed infrastructure

### MongoDB Atlas Vector Search

MongoDB Atlas supports vector search inside MongoDB.

Use it when:

- your app already stores data in MongoDB
- you want document metadata and embeddings together
- you want managed vector search without a separate vector database

Good for:

- document-oriented applications
- applications already using MongoDB Atlas

### LanceDB

LanceDB is a lightweight vector database built around the Lance columnar format.

Use it when:

- you want local or embedded vector search
- you work with multimodal data
- you want a simple developer experience

Good for:

- local RAG apps
- experimentation
- multimodal search prototypes

### DuckDB

DuckDB is an embedded analytical database.

Use it when:

- you need local analytics
- you want to query CSV/Parquet files easily
- you need fast SQL over local data

Good for:

- data exploration
- evaluation analysis
- local analytics pipelines

It is not primarily a vector database, but it is very useful around RAG evaluation and data preparation.

### Neo4j

Neo4j is a graph database.

Use it when:

- relationships between entities matter
- you need graph queries
- you are building graph RAG

Good for:

- entity relationship search
- knowledge graphs
- regulatory relationship mapping

Example:

```text
company -> filing -> risk factor -> regulation
```

## Document Parsing Tools

### PyMuPDF

PyMuPDF is a strong PDF parsing library.

Use it when:

- you need page-level PDF text extraction
- you need coordinates, page numbers, or layout details

FinanceRAG-mini uses PyMuPDF through `fitz`.

### pypdf

pypdf is a simple Python PDF library.

Use it when:

- basic PDF text extraction is enough
- you want a lighter dependency

Tradeoff:

- less powerful than PyMuPDF for layout-heavy PDFs

### pdfplumber

pdfplumber is useful for extracting text and tables from PDFs.

Use it when:

- PDFs contain tables
- layout matters
- you need more control than basic text extraction

### Unstructured

Unstructured is a document parsing framework.

Use it when:

- you need to parse many file types
- PDFs, Word docs, emails, HTML, and images may appear
- you want higher-level document partitioning

Good for:

- enterprise document ingestion
- mixed file formats
- quick document parsing pipelines

Tradeoff:

- heavier dependency
- may hide parsing details while learning

### Apache Tika

Apache Tika extracts text and metadata from many file types.

Use it when:

- you need broad file format support
- you are building document ingestion at enterprise scale

Good for:

- document management systems
- mixed file ingestion

## Embedding and Reranking Tools

### sentence-transformers

Python library for local embedding and reranking models.

Use it when:

- you want local embeddings
- you want no API cost
- you want to test models like BGE, MiniLM, or E5

Good for:

- local RAG
- learning embeddings
- offline evaluation

### Hugging Face Transformers

General library for using transformer models.

Use it when:

- you need custom NLP models
- you want local inference
- you want access to many open-source models

### Cohere Rerank

Managed reranking API.

Use it when:

- first-stage retrieval returns many candidates
- you want better final evidence ranking
- you do not want to host a reranker

Good for:

- improving retrieval quality
- production RAG ranking

### Cross-Encoder Rerankers

Cross-encoders score a query and document together.

Use them when:

- retrieval quality matters more than speed
- you need to rerank top candidates

Good for:

- final evidence selection
- evaluation experiments

Tradeoff:

- slower than embedding similarity search

## RAG Evaluation and Observability

### RAGAS

RAGAS is a RAG evaluation framework.

Use it when:

- you want to evaluate faithfulness
- you want to evaluate answer relevance
- you want to evaluate context precision/recall

Good for:

- RAG quality checks
- experiment comparison

### TruLens

TruLens helps evaluate and trace LLM apps.

Use it when:

- you want feedback functions
- you want traces of retrieval and generation
- you want quality monitoring

### DeepEval

DeepEval is an evaluation framework for LLM applications.

Use it when:

- you want unit-test-like evaluations for LLM outputs
- you need metrics for RAG, hallucination, and answer quality

### LangSmith

LangSmith is an observability and evaluation platform from LangChain.

Use it when:

- you use LangChain
- you need traces
- you need prompt/version experiment tracking

### Arize Phoenix

Phoenix is an open-source observability and evaluation tool for LLM apps.

Use it when:

- you want traces for RAG
- you want to inspect retrieval quality
- you want local/open-source observability

### OpenTelemetry

OpenTelemetry is a standard for traces, metrics, and logs.

Use it when:

- you want production observability
- you need traces across backend, retrieval, and LLM calls

Good for:

- production services
- debugging latency
- monitoring errors

## Workflow and Data Pipeline Tools

### Airflow

Airflow schedules and orchestrates data pipelines.

Use it when:

- ingestion has many steps
- jobs run on a schedule
- you need retries, logs, and dependency graphs

Good for:

- production data engineering workflows

### Prefect

Prefect is another workflow orchestration tool.

Use it when:

- you want Python-friendly workflows
- you need scheduled ingestion
- you want easier local development than Airflow

### Dagster

Dagster is a data orchestration platform focused on data assets.

Use it when:

- you want structured data pipelines
- you care about asset lineage
- your project grows into a real data platform

### Celery

Celery runs background jobs.

Use it when:

- ingestion should run outside the API request
- PDF parsing or indexing takes time
- you need async workers

Common pairing:

```text
FastAPI + Celery + Redis
```

### Kafka

Kafka is an event streaming platform.

Use it when:

- many systems produce/consume events
- ingestion is high-volume
- real-time pipelines matter

Not needed for early FinRegLive.

## Storage and Infrastructure

### Amazon S3

Object storage for files.

Use it for:

- raw documents
- parsed text
- exported feedback
- archived ingestion outputs

Cloud mapping for FinRegLive:

```text
local files -> S3
```

### MinIO

S3-compatible object storage that can run locally.

Use it when:

- you want to simulate S3 locally
- you want object storage without AWS

### Docker

Docker packages services into containers.

Use it when:

- you want reproducible local setup
- you need OpenSearch locally
- you want backend/frontend/search services to run together

### Docker Compose

Docker Compose runs multiple containers together.

Use it for:

- backend
- frontend
- OpenSearch
- PostgreSQL
- Redis

### Kubernetes

Kubernetes orchestrates containers at scale.

Use it when:

- many services need production orchestration
- scaling, rollout, service discovery, and resilience matter

Not needed for the first FinRegLive version.

## Model and Experiment Tracking

### MLflow

MLflow tracks experiments, metrics, artifacts, and models.

Use it when:

- you compare retrieval settings
- you compare embedding models
- you track evaluation runs

Good for:

- experiment management
- model lifecycle tracking

### Weights & Biases

Experiment tracking platform.

Use it when:

- you run many ML experiments
- you want dashboards and metrics
- you compare model runs

For FinRegLive, MLflow or simple CSV evaluation logs are enough at first.

## API and Application Tools

### FastAPI

Python web framework for APIs.

Use it when:

- you need backend endpoints
- you want validation with Pydantic
- you want automatic API docs

FinRegLive uses FastAPI for the backend.

### Streamlit

Python framework for simple data apps.

Use it when:

- frontend engineering is not the main focus
- you need dashboards quickly
- you want to demonstrate RAG results

FinRegLive will use Streamlit for the dashboard.

### Gradio

Python framework for ML demos.

Use it when:

- you want quick model demos
- you need simple input/output interfaces

Streamlit is better for this project because we need multiple dashboard pages and diagnostics.

## Practical Selection Rule

For FinRegLive, avoid adding tools just because they are popular.

Use a tool only when it clearly solves the next engineering problem:

```text
Need source text?              -> ingestion/parser
Need persistence?              -> SQLite now, PostgreSQL later
Need keyword/vector search?    -> OpenSearch
Need embeddings?               -> sentence-transformers first
Need background jobs?          -> Celery or scheduled task later
Need cloud raw storage?        -> S3 later
Need evaluation?               -> simple tests first, RAGAS/Phoenix later
Need UI?                       -> Streamlit
```
