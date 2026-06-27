# Learning Materials

General RAG, retrieval, evaluation, and production architecture notes used while
building FinReg Live Intelligence.

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

## Classic RAG vs Production-Grade RAG

A classic or naive RAG system usually follows a simple retrieve-then-generate pattern:

```text
user query
  -> retrieve relevant chunks
  -> place chunks into the prompt
  -> generate answer with an LLM
```

This is a good starting point, but it is not enough for a serious financial or regulatory QA system.

A production-grade RAG system should behave more like a decision-making pipeline:

```text
user query
  -> query understanding
  -> hybrid retrieval
  -> reranking
  -> evidence diagnostics
  -> route selection
  -> generation
  -> verification
  -> fallback or abstention if needed
  -> logging and evaluation
```

The key difference is that a production RAG system does not blindly generate an answer after retrieval. It asks:

- Is the question answerable from the available corpus?
- Is the retrieved evidence strong enough?
- Is this a simple lookup or a high-risk reasoning question?
- Which model and context budget should be used?
- Should an LLM judge or citation verifier be used?
- Should the system retry, fallback, or abstain?

For FinRegLive, the target story should be:

```text
Production-oriented, evidence-grounded, cost-aware RAG for financial/regulatory QA.
```

## Production-Oriented RAG Architecture

A more industry-level RAG architecture has separate layers for ingestion, retrieval, routing, generation, verification, and observability.

```text
                         ┌────────────────────────────┐
                         │        Source Corpus        │
                         │ PDFs, regulations, reports, │
                         │ guidance, tables, HTML      │
                         └──────────────┬─────────────┘
                                        │
                                        ▼
┌────────────────────────────────────────────────────────────────┐
│ 1. Ingestion + Document Processing Layer                        │
│ - parsing                                                       │
│ - cleaning / deduplication                                      │
│ - metadata extraction                                           │
│ - section hierarchy                                             │
│ - chunking strategy                                             │
│ - document versioning                                           │
└──────────────────────────────┬─────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ 2. Indexing Layer                                               │
│ - BM25 / lexical index                                          │
│ - dense vector index                                            │
│ - metadata index                                                │
│ - optional cross-reference or graph index                       │
│ - embedding model version tracking                              │
└──────────────────────────────┬─────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     User Query        │
                    └──────────┬───────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ 3. Query Understanding Layer                                    │
│ - query classification                                          │
│ - intent detection                                              │
│ - risk detection                                                │
│ - out-of-domain detection                                       │
│ - optional query rewrite                                        │
│ - optional decomposition                                        │
└──────────────────────────────┬─────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ 4. Retrieval Layer                                              │
│ - BM25 retrieval                                                │
│ - dense retrieval                                               │
│ - hybrid retrieval                                              │
│ - RRF / fusion                                                  │
│ - metadata filtering                                            │
└──────────────────────────────┬─────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ 5. Reranking + Evidence Selection Layer                         │
│ - cross-encoder reranking                                       │
│ - passage relevance filtering                                   │
│ - duplicate removal                                             │
│ - evidence coverage check                                       │
│ - context budget control                                        │
└──────────────────────────────┬─────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ 6. Routing Layer                                                │
│ - simple lookup route                                           │
│ - medium reasoning route                                        │
│ - complex / high-risk route                                     │
│ - low-evidence abstention route                                 │
│ - fallback / retry policy                                       │
└──────────────────────────────┬─────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
┌────────────────┐   ┌────────────────┐   ┌────────────────────────┐
│ Simple Route   │   │ Medium Route   │   │ Complex / Risk Route    │
│ top-3 context  │   │ top-8 context  │   │ top-12/15 context       │
│ cheap model    │   │ medium model   │   │ stronger model          │
│ citation only  │   │ citation check │   │ judge + verification    │
└───────┬────────┘   └───────┬────────┘   └───────────┬────────────┘
        │                    │                        │
        └────────────────────┼────────────────────────┘
                             ▼
┌────────────────────────────────────────────────────────────────┐
│ 7. Answer Generation Layer                                      │
│ - grounded answer generation                                    │
│ - structured output                                             │
│ - citation-aware prompting                                      │
│ - abstention instruction                                        │
│ - uncertainty handling                                          │
└──────────────────────────────┬─────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ 8. Verification Layer                                           │
│ - citation support check                                        │
│ - answerability check                                           │
│ - hallucination / faithfulness check                            │
│ - optional LLM-as-a-judge                                       │
│ - fallback to stronger route if failed                          │
└──────────────────────────────┬─────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ 9. Response Layer                                               │
│ - final answer                                                  │
│ - citations                                                     │
│ - evidence status                                               │
│ - not-answerable response when needed                           │
└──────────────────────────────┬─────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ 10. Observability + Evaluation Layer                            │
│ - retrieval metrics                                             │
│ - generation metrics                                            │
│ - latency                                                       │
│ - token usage                                                   │
│ - cost per query                                                │
│ - route distribution                                            │
│ - fallback rate                                                 │
│ - judge call rate                                               │
│ - trace logs                                                    │
│ - human feedback                                                │
│ - offline benchmark evaluation                                  │
└────────────────────────────────────────────────────────────────┘
```

## Model Routing In RAG

Model routing means choosing the right model or pipeline based on the query, evidence quality, risk level, and cost budget.

It is not only about choosing between LLMs. In RAG, routing can decide:

- whether to answer or abstain
- how many chunks to send to the LLM
- whether to run a reranker
- whether to use a cheap, medium, or stronger model
- whether to run citation verification
- whether to run LLM-as-a-judge
- whether fallback/retry is allowed

Example route policy:

```text
simple_lookup:
  retrieval: BM25 + dense + RRF
  context: top-3 chunks
  generator: cheap / fast model
  verification: citation required
  judge: no

medium_reasoning:
  retrieval: BM25 + dense + RRF
  reranking: yes
  context: top-8 chunks
  generator: medium model
  verification: citation check
  judge: optional

complex_high_risk:
  retrieval: BM25 + dense + RRF
  reranking: yes
  context: top-12 or top-15 chunks
  generator: stronger reasoning model
  verification: citation check + faithfulness check
  judge: yes
  fallback: yes, max 1 or 2 retries

low_evidence_or_out_of_domain:
  generation: no
  response: not answerable from the provided corpus
```

The professional point is:

```text
Do not send every query to the largest model.
Route by query type, retrieval confidence, risk, and evidence strength.
```

## How To Decide Whether A Query Is Easy Or Hard

Difficulty should not be decided from the query text alone. In RAG, it is better to combine query signals and retrieval signals.

Useful signals:

```text
query type
+ risk markers
+ retrieval confidence
+ score margin
+ number of strong evidence chunks
+ source document spread
+ cross-reference presence
+ answerability
```

Easy query signs:

- asks for a definition
- asks for a direct lookup
- one chunk appears to contain the answer
- top-1 retrieval score is strong
- top-1 result is clearly better than top-2
- answer does not require conditions, exceptions, or multiple documents

Medium query signs:

- asks for requirements or obligations
- needs several chunks
- asks for a comparison
- requires a structured answer
- retrieval results are relevant but spread across a few sections

Hard or high-risk query signs:

- asks whether something is required, allowed, exempt, or prohibited
- includes conditions such as if, unless, except, provided that
- requires thresholds, deadlines, exceptions, or permissions
- needs evidence from multiple documents or sections
- asks for a compliance decision
- retrieval results are spread across many documents
- evidence is incomplete or conflicting

Example routing logic:

```python
def route_query(query, retrieved_docs, risk_level):
    top1 = retrieved_docs[0].score
    top2 = retrieved_docs[1].score
    source_count = len(set(doc.source for doc in retrieved_docs[:5]))

    if risk_level == "high":
        return "complex_high_risk"

    if top1 < 0.45:
        return "low_evidence_or_out_of_domain"

    if top1 > 0.85 and (top1 - top2) > 0.20 and source_count == 1:
        return "simple_lookup"

    if source_count >= 3:
        return "complex_reasoning"

    return "medium_reasoning"
```

The threshold values are only examples. In a real project they should be calibrated with evaluation data.

## Fallback and Retry Mechanism

A production RAG system should have a controlled retry/fallback policy.

Basic idea:

```text
generate answer
  -> verify answer
  -> if pass: return answer
  -> if fail: fallback
       -> increase top-k
       -> rerank
       -> use stronger model
       -> regenerate once
       -> if still weak: abstain
```

Examples:

```text
simple_lookup
  -> cheap model
  -> citation check fails
  -> fallback to medium route

medium_reasoning
  -> medium model
  -> judge says unsupported
  -> fallback to complex route

complex_high_risk
  -> stronger model
  -> evidence still weak
  -> abstain instead of guessing
```

Important rule:

```text
Fallback must be budgeted.
Use max_retry = 1 or 2.
Unlimited retry loops can make cost explode.
```

## Cost-Aware RAG

In classic RAG, the main LLM cost is usually answer generation.

In production RAG, cost can increase because of:

- longer context windows
- query rewriting
- reranking with expensive models
- citation verification
- LLM-as-a-judge
- fallback / retry
- feedback-triggered re-evaluation
- offline regression evaluation
- agentic loops

A useful cost formula:

```text
Total RAG cost =
  generation cost
+ context length cost
+ verification cost
+ judge evaluation cost
+ retry / fallback cost
+ offline evaluation cost
```

The goal is not to remove evaluation. The goal is to budget it.

Example cost-aware policy:

```text
simple queries:
  no judge
  small context
  cheap model
  citation-only check

medium queries:
  reranker
  medium context
  medium model
  lightweight citation check

high-risk queries:
  stronger model
  judge evaluation
  citation verification
  fallback allowed

production monitoring:
  judge only high-risk queries and random samples
  track judge call rate
  track fallback rate
  track cost per successful answer
```

Important concept:

```text
Evaluation is a budgeted component of the RAG pipeline, not an always-on step for every query.
```

## RAG Patterns and Terminology

RAG terminology should be understood as a set of patterns, not as 25 completely separate system types.

### Standard / Naive / Classic RAG

Basic retrieve-then-generate pipeline.

```text
query -> retrieve chunks -> generate answer
```

Good starting point, but weak at detecting bad retrieval, insufficient evidence, or unsupported generation.

### Conversational RAG

Uses chat history to reformulate the current user query into a standalone query.

```text
chat history + current query -> standalone query -> retrieve -> answer
```

Useful when users ask follow-up questions such as:

```text
What about the exception?
Does it apply to them?
```

### Sparse RAG

Uses sparse or lexical retrieval, usually BM25.

Good for:

- exact terms
- section numbers
- legal references
- defined terms

### Dense RAG

Uses embeddings and vector similarity search.

Good for semantic matching when the query and document use different wording.

### Hybrid RAG

Combines sparse and dense retrieval.

```text
BM25 + dense retrieval
```

This is strong for financial and regulatory search because exact terminology and semantic similarity both matter.

### Fusion RAG

Combines results from multiple retrievers or retrieval strategies.

```text
BM25 results + dense results -> RRF or weighted fusion -> final ranking
```

RRF means Reciprocal Rank Fusion. It combines rankings by rewarding documents that appear high in multiple result lists.

### Reranked / Context-Ranking RAG

Retrieves a broad candidate set, then uses a reranker to select the strongest evidence.

```text
retrieve top-50 -> cross-encoder reranker -> use top-5 or top-8
```

The retriever is fast and broad. The reranker is slower but more precise.

### Contextual Compression RAG

Compresses retrieved chunks before generation.

```text
long retrieved passage -> relevant sentences only -> generator
```

Goal:

- reduce input tokens
- reduce noise
- improve grounding
- reduce cost

Risk:

- important context may be removed if compression is poor

### Parent-Child RAG

Uses small child chunks for retrieval but expands to a larger parent section for generation.

```text
child chunk retrieval -> parent section expansion -> answer generation
```

Useful for legal and regulatory documents because a small chunk may contain the answer phrase but not the surrounding exception or condition.

### Hierarchical RAG

Uses document structure to retrieve at multiple levels.

```text
document -> chapter -> section -> paragraph / chunk
```

Useful for long structured corpora such as rulebooks, regulations, contracts, and guidance documents.

### Long-Context RAG

Uses long-context models to include more retrieved material.

Benefit:

- less aggressive context selection
- more evidence can be passed to the model

Risk:

- higher cost
- higher latency
- more noise
- model may still miss the relevant passage

Long-context models do not remove the need for good retrieval and ranking.

### Multi-Hop RAG

Used when the answer requires combining evidence from multiple passages or documents.

```text
retrieve evidence A -> retrieve evidence B -> combine -> answer
```

Example evidence needs:

```text
definition
+ obligation
+ exception
+ deadline
+ applicability condition
```

### Chain-of-Retrieval

A sequential retrieval process where each retrieval step informs the next.

```text
query -> retrieve -> identify missing information -> retrieve again -> answer
```

Useful for cross-references and multi-step regulatory reasoning.

### Reasoning RAG

Broad term for RAG systems that combine retrieved evidence with structured reasoning.

Example:

```text
If X applies and no exception Y applies, then the firm must notify the regulator within Z days.
```

This term is useful, but it is less precise than multi-hop, corrective, routed, or citation-aware RAG.

### Corrective RAG

Checks retrieval or answer quality and corrects the pipeline when needed.

```text
retrieve -> check evidence -> if weak, rewrite/retrieve again -> generate -> verify
```

Corrective RAG is closely related to fallback and retry mechanisms.

### Self-RAG

The model or system reflects on whether retrieval is needed, whether the evidence is relevant, and whether the answer is supported.

Typical pattern:

```text
generate -> critique -> revise or abstain
```

Important idea:

```text
The system should be able to detect unsupported answers.
```

### Citation-Aware RAG

Requires generated answers to include citations.

```text
claim -> citation
claim -> citation
```

For financial and regulatory QA, citation-aware generation is important because the answer must be auditable.

### Evidence-Grounded RAG

A broader term than citation-aware RAG.

Goal:

- avoid unsupported claims
- use retrieved evidence correctly
- abstain when evidence is insufficient
- make answers traceable to source documents

### Adaptive / Routed RAG

Uses different pipelines depending on query type, difficulty, risk, and evidence strength.

```text
simple query -> cheap model + top-3 context
medium query -> reranker + medium model + top-8 context
complex query -> stronger model + judge + fallback
out-of-domain query -> abstain
```

### Cost-Aware RAG

Tracks and optimizes cost, latency, and quality.

Important logs:

- input tokens
- output tokens
- model used
- context size
- route
- reranker used
- judge used
- fallback count
- latency
- estimated cost

### Agentic RAG

An agent controls the retrieval process with planning, tool use, repeated searches, and verification.

```text
plan -> retrieve -> inspect -> retrieve again -> use tools -> verify -> answer
```

Powerful, but expensive and harder to control. For FinRegLive, this can be a separate project or future extension.

### Memory-Augmented RAG

Uses long-term or session memory, such as previous user preferences, prior decisions, or conversation state.

More useful for assistants and customer support systems than for the first version of regulatory QA.

### Multimodal RAG

Retrieves and reasons over non-text content such as:

- tables
- figures
- charts
- screenshots
- scanned PDFs
- audio or video transcripts

Useful if financial reports include tables, forms, or visual evidence.

### Federated RAG

Retrieves from distributed sources.

Examples:

- document repository
- database
- internal API
- SharePoint / Confluence
- external search

Common in enterprise RAG systems.

### Graph RAG

Uses entities and relations to support retrieval and reasoning.

Example graph:

```text
Authorised Person -> has obligation -> notify Regulator
Controller Change -> triggers -> notification requirement
Rule X -> references -> Rule Y
```

Useful for:

- multi-hop reasoning
- cross-references
- legal/regulatory corpora
- relationship-heavy domains

For FinRegLive, Graph RAG is a strong future extension because financial regulation contains many entities, obligations, definitions, and cross-references.

### HyDE RAG

HyDE means Hypothetical Document Embeddings.

Pattern:

```text
query -> LLM writes hypothetical answer/document -> embed hypothetical document -> retrieve similar real documents
```

It can improve semantic retrieval, but it adds an LLM call before retrieval, so it increases cost.

### Prompt-Augmented RAG

Uses careful prompt structure around the retrieved evidence.

Examples:

- evidence table
- answer format instructions
- citation rules
- abstention rules
- examples of good answers

This is usually a prompt-engineering layer rather than a completely separate RAG architecture.

### Few-Shot RAG

Adds examples to the prompt.

```text
example question
example evidence
example grounded answer with citation
```

Can improve formatting and behavior, but it increases input tokens. In production, few-shot examples should be short, cached, or used selectively.

## Recommended RAG Direction For FinRegLive

The most useful direction is not to claim support for every RAG pattern. The stronger professional story is:

```text
FinRegLive starts from classic RAG and moves toward a production-oriented regulatory RAG architecture.
```

Recommended implementation path:

```text
1. Hybrid RAG
   BM25 + dense retrieval

2. Fusion RAG
   RRF to combine lexical and semantic retrieval

3. Reranked RAG
   Cross-encoder reranking for final evidence selection

4. Citation-Aware / Evidence-Grounded RAG
   Answers must cite supporting evidence

5. Adaptive / Routed RAG
   Different query types use different context budgets, models, and verification policies

6. Corrective RAG
   Failed citation or faithfulness checks trigger fallback/retry or abstention

7. Cost-Aware RAG
   Log tokens, latency, route, judge usage, fallback count, and estimated cost

8. Evaluation-Driven RAG
   Use retrieval metrics, generation metrics, judge scores, and regression tests
```

Possible future extensions:

```text
Hierarchical / parent-child retrieval
Multi-hop question handling
Graph RAG for cross-references and regulatory relationships
Agentic RAG as a separate project
Multimodal RAG if tables/forms/scanned PDFs become central
```

## Interview Explanation: RAG Patterns

If asked what types of RAG systems you know, a strong answer is:

```text
I think about RAG patterns in terms of the system bottleneck they address. Standard RAG is retrieve-then-generate. Hybrid and fusion RAG improve retrieval recall by combining lexical and dense retrievers. Reranked or context-ranking RAG improves evidence precision before generation. Multi-hop and chain-of-retrieval RAG are useful when the answer requires evidence from multiple passages. Corrective and self-reflective RAG add verification and retry loops. Adaptive or routed RAG chooses different retrieval depth, context budget, model, and verification policy depending on query complexity, risk, and evidence confidence. For legal or regulatory QA, I would especially prioritize hybrid retrieval, reranking, citation-aware generation, corrective fallback, and cost-aware routing.
```

## Observability Fields For Production RAG

A production-oriented RAG system should log every query trace.

Example log object:

```json
{
  "query_id": "q_001",
  "query_type": "compliance_decision",
  "route": "complex_high_risk",
  "retriever": "bm25+dense+rrf",
  "top_k_retrieved": 20,
  "top_k_used": 12,
  "reranker_used": true,
  "generator_model": "strong_model",
  "judge_used": true,
  "fallback_used": false,
  "input_tokens": 8420,
  "output_tokens": 620,
  "latency_ms": 7300,
  "estimated_cost_usd": 0.042,
  "faithfulness_score": 0.91,
  "citation_check": "pass"
}
```

Useful aggregate metrics:

- route distribution
- fallback rate
- judge call rate
- abstention rate
- average cost per query
- cost per successful answer
- latency per route
- hallucination / unsupported answer rate
- citation support score
- retrieval recall and nDCG


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



## Evaluation Layer For RAG Systems

Evaluation is the part of the RAG system that checks whether the system is actually working well.

A RAG system should not only be judged by whether the final answer sounds good. It should be evaluated at several levels:

```text
question
  -> retrieval quality
  -> evidence quality
  -> answer quality
  -> citation/support quality
  -> failure analysis
```

For FinRegLive, evaluation is important because the system works with financial and regulatory documents. In this domain, a fluent but unsupported answer is dangerous. The answer must be grounded in the source evidence.

### Main Evaluation Questions

A good RAG evaluation layer should answer questions like:

- Did the retriever find the right document chunks?
- Did the answer use the retrieved evidence correctly?
- Did the model hallucinate unsupported information?
- Did the answer miss an important obligation, exception, threshold, date, or definition?
- Are the citations actually supporting the claims?
- Did the new version of the system improve or regress?

## Retrieval Evaluation

Retrieval evaluation checks whether the search component returns useful evidence.

This is separate from generation evaluation. A RAG answer can fail because retrieval failed, even if the LLM itself is strong.

Example:

```text
Question: What must a firm do before changing its controller?

Retriever returns:
- unrelated AML paragraph
- irrelevant definition section
- old guidance note

LLM answer may then be incomplete or wrong because the right evidence was never retrieved.
```

### Retrieval Metrics

Use these when you have relevance labels or gold evidence.

### Recall@k

Recall@k asks:

```text
Did the correct evidence appear somewhere in the top k retrieved chunks?
```

Example:

```text
Recall@5 = correct passage is found in top 5 results
Recall@10 = correct passage is found in top 10 results
```

Good for RAG because the LLM usually receives the top few retrieved chunks.

### Precision@k

Precision@k asks:

```text
How many of the top k retrieved chunks are actually relevant?
```

This matters when the context window is limited. Too many irrelevant chunks can confuse the LLM.

### MRR

MRR means Mean Reciprocal Rank.

It rewards systems that rank the first relevant result very highly.

Example:

```text
Relevant chunk at rank 1 -> score 1.0
Relevant chunk at rank 2 -> score 0.5
Relevant chunk at rank 5 -> score 0.2
```

Useful when one strong evidence passage is enough.

### nDCG@k

nDCG@k is useful when relevance is graded.

Example:

```text
3 = highly relevant
2 = partially relevant
1 = weakly relevant
0 = irrelevant
```

nDCG rewards systems that put highly relevant evidence near the top.

For regulatory RAG, nDCG is useful because some chunks may be directly relevant, while others are only background context.

### Context Precision

Context precision asks:

```text
Are the retrieved contexts relevant, and are the most relevant ones ranked first?
```

This is used in RAGAS-style evaluation.

### Context Recall

Context recall asks:

```text
Did the retrieved contexts contain the information needed to answer the question?
```

This usually requires a reference answer or gold evidence.

## Generation Evaluation

Generation evaluation checks the final answer.

The answer should be:

- faithful to the evidence
- relevant to the question
- complete enough for the task
- clear and not misleading
- properly supported by citations

### Faithfulness / Groundedness

Faithfulness asks:

```text
Is every factual claim in the answer supported by the retrieved evidence?
```

This is one of the most important RAG metrics.

Example failure:

```text
Evidence: A firm must notify the regulator within 14 days.
Answer: A firm must notify the regulator within 30 days.
```

The answer is relevant, but not faithful.

### Answer Relevance

Answer relevance asks:

```text
Does the answer directly answer the user's question?
```

Example failure:

```text
Question: What is the deadline?
Answer: The rule applies to authorised firms.
```

The answer may be true, but it does not answer the question.

### Completeness

Completeness asks:

```text
Does the answer include all important conditions, exceptions, thresholds, and dates?
```

This is especially important in legal and regulatory QA.

Example:

```text
Question: When must the firm notify the regulator?
Evidence: The firm must notify the regulator within 14 days unless an exemption applies.
Bad answer: The firm must notify the regulator within 14 days.
Better answer: The firm must notify the regulator within 14 days, unless the stated exemption applies.
```

### Citation Support

Citation support asks:

```text
Do the cited chunks actually support the answer claims?
```

A RAG system should not only provide citations. The citations must be correct.

Bad pattern:

```text
Answer is correct, but citation points to an unrelated paragraph.
```

For FinRegLive, citation support should be shown in the UI because it demonstrates evidence-grounded AI.

## LLM-as-a-Judge

LLM-as-a-judge means using an LLM to evaluate another model's output.

Instead of asking the LLM to answer the user question, we ask it to judge whether an answer is good.

Basic flow:

```text
question
  -> retrieved evidence
  -> generated answer
  -> judge prompt
  -> score + explanation + pass/fail label
```

### Why Use LLM-as-a-Judge

Traditional metrics often fail for natural language answers.

For example, these two answers mean the same thing:

```text
Answer A: The firm must submit the report within 30 days.
Answer B: The report must be submitted no later than 30 days after the event.
```

Exact match would treat them as different. An LLM judge can evaluate semantic equivalence.

LLM judges are useful for:

- faithfulness
- answer relevance
- completeness
- hallucination detection
- citation support
- pairwise comparison
- instruction following
- safety and compliance checks

### Reference-Based Judge

The judge sees a gold/reference answer.

```text
Question
Gold answer
Model answer
Judge score
```

Use this when you have a curated test set.

Good for:

- benchmark evaluation
- regression testing
- comparing model versions

### Reference-Free Judge

The judge does not see a gold answer. It sees the question, retrieved evidence, and generated answer.

```text
Question
Retrieved evidence
Model answer
Judge score
```

Use this when gold answers are expensive.

Good for:

- RAG faithfulness
- hallucination checks
- evidence-grounding evaluation

### Pairwise Judge

The judge compares two answers.

```text
Question
Answer A
Answer B
Judge chooses winner
```

Use this when comparing prompts, models, or retrieval settings.

Example:

```text
BM25 answer vs hybrid retrieval answer
GPT-4 answer vs local model answer
prompt v1 vs prompt v2
```

### Rubric-Based Judge

A rubric tells the judge exactly how to score.

Example rubric:

```text
5 = fully supported, complete, and directly answers the question
4 = mostly correct, minor missing detail
3 = partially correct but incomplete
2 = weakly supported or mostly incomplete
1 = unsupported, incorrect, or misleading
```

Rubric-based judging is stronger than vague judging.

Bad prompt:

```text
Is this answer good?
```

Better prompt:

```text
Evaluate whether the answer is faithful to the evidence.
Penalize unsupported claims, missing exceptions, wrong numbers, wrong dates, and vague citations.
Return JSON with scores and explanation.
```

## Example Judge Prompt

```text
You are evaluating a regulatory QA system.

Question:
{question}

Retrieved evidence:
{contexts}

Generated answer:
{answer}

Evaluate the answer using these criteria:

1. Faithfulness
Does the answer only make claims supported by the retrieved evidence?

2. Relevance
Does the answer directly answer the question?

3. Completeness
Does the answer include all important obligations, thresholds, dates, definitions, and exceptions present in the evidence?

4. Citation support
Do the cited passages actually support the answer?

Return JSON only:

{
  "faithfulness_score": 1-5,
  "relevance_score": 1-5,
  "completeness_score": 1-5,
  "citation_support_score": 1-5,
  "unsupported_claims": [],
  "missing_information": [],
  "overall_pass": true/false,
  "explanation": "brief explanation"
}
```

## Judge Output Example

```json
{
  "faithfulness_score": 4,
  "relevance_score": 5,
  "completeness_score": 3,
  "citation_support_score": 4,
  "unsupported_claims": [],
  "missing_information": [
    "The answer does not mention the exemption condition stated in the evidence."
  ],
  "overall_pass": false,
  "explanation": "The answer is mostly grounded and relevant, but it misses an important exception, so it should not pass for regulatory QA."
}
```

## Problems With LLM-as-a-Judge

LLM judges are useful, but they are not automatically reliable.

The important professional point is this:

```text
LLM-as-a-judge is an evaluation method, not a source of truth.
```

A good evaluation pipeline should assume that the judge can be biased, inconsistent, or wrong.

### Common Judge Biases

#### Position Bias

Position bias means the judge systematically favors one answer because of where it appears.

In pairwise evaluation, the judge may prefer:

```text
Response A over Response B
```

even when the quality difference is small.

This is dangerous because a model can look better simply because it was always shown first.

Mitigation:

```text
Run the pairwise evaluation twice:

Run 1: Answer A vs Answer B
Run 2: Answer B vs Answer A

Then aggregate the results.
```

If the judge chooses the first answer both times, the result may indicate position bias rather than real quality.

For serious evaluation, randomize answer order and store the original answer identity separately.

#### Verbosity Bias

Verbosity bias means the judge prefers longer, more detailed answers even when they contain unnecessary text, vague claims, or minor inaccuracies.

This is common because long answers often look more helpful at first glance.

Bad judge behavior:

```text
Long answer with extra unsupported explanation -> high score
Short answer that is precise and correct -> lower score
```

Mitigation:

Design the rubric to explicitly penalize unnecessary wordiness.

Example rubric instruction:

```text
Do not reward length by itself.
Penalize answers that add unsupported details, irrelevant background, or unnecessary speculation.
A concise answer should receive a high score if it is correct, complete, and grounded.
```

For regulatory RAG, this matters a lot because a verbose answer may introduce compliance risk.

#### Self-Preference / Self-Appraisal Bias

Self-preference bias means a judge model may prefer outputs generated by itself or by models with a similar style or architecture.

Example:

```text
GPT-based judge evaluating GPT-generated answers
```

The judge may favor the style, wording, structure, or reasoning pattern of its own model family.

Mitigation:

Use one or more of these:

```text
- compare judge results against human labels
- use a different judge model from the generation model
- use multiple judges and aggregate scores
- inspect disagreement cases manually
```

In a production setting, this is part of judge validation.

#### Egocentric Bias

Egocentric bias means the judge gives higher scores to answers that match its own unstated preferences.

These preferences may include:

- preferred formatting
- preferred tone
- preferred explanation style
- preferred amount of detail
- preferred answer structure

The problem is that these preferences may not match the actual product requirements.

For example, a judge may prefer a polished paragraph, while the product needs a short compliance answer with bullet-pointed obligations and citations.

Mitigation:

Make the desired answer style explicit in the rubric.

Example:

```text
Evaluate according to the product requirements, not your own writing preference.
The ideal answer should be concise, evidence-grounded, citation-supported, and should avoid unsupported legal interpretation.
Do not reward style unless it improves correctness, clarity, or usability.
```

#### Inconsistency

The same judge can give different scores to the same answer across multiple runs, especially when temperature is above zero or the rubric is vague.

Mitigation:

```text
- use deterministic settings where possible
- use structured JSON output
- use a clear rubric
- run repeated judgments for important samples
- track score variance
```

#### Domain Weakness

A general LLM judge may miss legal, regulatory, financial, or medical nuance.

Example:

```text
The answer is broadly plausible, but it misses an exception, threshold, jurisdiction, date, or defined term.
```

In regulatory QA, that is not a minor issue. It can make the answer unsafe or misleading.

Mitigation:

```text
- use domain-specific rubrics
- include the evidence in the judge prompt
- use expert-labeled validation sets
- include checks for thresholds, dates, exceptions, definitions, and obligations
```

### Practical Mitigation Checklist

A strong LLM-as-a-judge setup should include:

```text
clear rubric
structured output
answer-order randomization for pairwise judging
A/B and B/A judging for pairwise comparisons
verbosity penalty
human calibration set
judge-human agreement analysis
disagreement inspection
threshold tuning
versioned judge prompts
evaluation logs
```

So the professional approach is:

```text
Do not blindly trust the judge.
Calibrate it against human labels.
Use clear rubrics.
Control for position and verbosity bias.
Track agreement.
Inspect failures manually.
```

## Human Evaluation

Human evaluation is still important, especially for high-risk domains.

Use human evaluation when:

- the domain is legal, financial, medical, or safety-critical
- the answer requires expert judgment
- the evaluation set is small but important
- the LLM judge may not understand the nuance

For FinRegLive, a good setup is:

```text
small expert-labeled gold set
  -> used to validate LLM judge
larger automatically judged set
  -> used for fast iteration
manual error analysis
  -> used to understand failure modes
```

## Evaluation Dataset

A RAG evaluation dataset usually contains:

```text
question
reference answer
gold evidence chunks
retrieved chunks
generated answer
metadata
judge scores
human labels if available
```

For FinRegLive, test questions should include:

- normal answerable questions
- multi-hop questions
- questions requiring dates, thresholds, or definitions
- questions requiring exceptions
- unanswerable questions
- out-of-domain questions
- adversarial or misleading questions

Example unanswerable question:

```text
What is the firm's required capital buffer under a rule that is not present in the corpus?
```

The correct behavior is not to guess. The system should say that the provided documents do not contain enough evidence.

## RAGAS

RAGAS is a RAG evaluation framework.

Use it when:

- you want quick RAG quality metrics
- you want faithfulness and answer relevance checks
- you want context precision and context recall
- you want to compare experiments

Common RAGAS-style metrics:

```text
faithfulness
answer relevancy
context precision
context recall
answer correctness
```

RAGAS is useful, but it should not be treated as magic.

For serious evaluation:

```text
inspect the metric prompts
check examples manually
compare with human labels
customize for the domain
track results across runs
```

## DeepEval

DeepEval is an evaluation framework for LLM applications.

Use it when:

- you want unit-test-like checks for LLM outputs
- you want custom metrics
- you want hallucination, relevance, and faithfulness tests
- you want CI-style evaluation before deployment

Good for:

```text
pytest-style LLM evaluation
regression tests
custom judge metrics
RAG test cases
```

Example idea:

```text
If faithfulness score < 0.8, fail the test.
If answer relevance score < 0.7, fail the test.
If unsupported claims are detected, fail the test.
```

## Evaluation Logs

Every evaluation run should be saved.

Useful fields:

```text
run_id
timestamp
question_id
question
retriever_type
embedding_model
reranker_model
top_k
retrieved_chunk_ids
answer
reference_answer
judge_model
judge_prompt_version
faithfulness_score
relevance_score
completeness_score
citation_support_score
latency
cost
pass_fail
error_notes
```

This makes the project look more production-oriented because it shows experiment tracking and regression testing.

## Failure Diagnosis

Evaluation should not only produce scores. It should explain why the system failed.

Common RAG failure types:

```text
retrieval_miss         = correct evidence was not retrieved
ranking_error          = correct evidence was retrieved too low
context_noise          = too many irrelevant chunks were included
generation_error       = evidence was retrieved but answer was wrong
hallucination          = answer added unsupported information
incomplete_answer      = answer missed important detail
citation_error         = answer citation does not support claim
unanswerable_failure   = system answered when it should abstain
```

For FinRegLive, this is a strong portfolio feature. It shows that the system is not just a demo; it can diagnose weaknesses.

## Production Evaluation

In production, evaluation is not a one-time notebook. It becomes a continuous quality process.

A mature setup includes:

```text
offline benchmark before release
small human-labeled validation set
LLM-as-a-judge scoring
retrieval metrics
manual review of failures
CI regression tests
production traces and feedback
monitoring over time
```

Before deploying a new model, prompt, embedding model, or retrieval setting, run the evaluation suite.

Example release gate:

```text
Deploy only if:
- Recall@10 does not decrease
- faithfulness score is above threshold
- hallucination rate does not increase
- citation support score is above threshold
- critical regulatory questions pass manually
```

## Evaluation Tools Selection For FinRegLive

Recommended staged approach:

### Stage 1: Simple Custom Evaluation

Use:

```text
CSV/JSON test set
manual labels
retrieval metrics
custom judge prompt
Streamlit results table
```

This is enough to show the core evaluation logic clearly.

### Stage 2: RAGAS / DeepEval

Add:

```text
RAGAS for faithfulness, answer relevance, context metrics
DeepEval for custom unit-test-style checks
structured pass/fail thresholds
```

This shows familiarity with current LLM evaluation tools.

### Stage 3: Observability

Add:

```text
Phoenix or LangSmith traces
MLflow experiment tracking
OpenTelemetry for production-style traces
```

This shows cloud-ready and production-aware engineering.


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
