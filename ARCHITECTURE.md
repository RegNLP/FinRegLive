# FinReg Live Intelligence Architecture

This document shows the system architecture with diagrams. The main README
explains the project plan; this file focuses on how the parts connect.

## 1. General Architecture

```mermaid
flowchart TD
    sources[Public regulatory sources<br/>SEC, FCA, Bank of England] --> ingestion[Ingestion layer<br/>RSS, HTML, item pages]
    ingestion --> cleaning[Cleaning and deduplication<br/>content hash]
    cleaning --> documents[(SQLite metadata<br/>documents, chunks, queries, feedback)]
    cleaning --> chunking[Chunking<br/>word windows with overlap]
    chunking --> documents
    chunking --> embeddings[Embedding generation]
    embeddings --> index[(OpenSearch<br/>BM25 + vector index)]

    user[User question] --> api[FastAPI backend]
    api --> routing[Query classifier<br/>route policy]
    routing --> retrieval[Hybrid retrieval<br/>BM25 + vector + RRF]
    retrieval --> index
    retrieval --> reranker[Reranker]
    reranker --> diagnostics[Evidence diagnostics<br/>confidence, spread, risk]
    diagnostics --> generation[Source-grounded generation]
    generation --> verification[Verification<br/>citations, answerability]
    verification --> response[Final answer<br/>sources + limitations]
    response --> frontend[Streamlit UI]
    frontend --> user

    api --> logs[(Query logs<br/>feedback)]
    logs --> documents
```

## 2. Ingestion and Indexing Pipeline

```mermaid
flowchart TD
    start[Start ingestion] --> choose{Source type}
    choose --> rss[RSS feed<br/>SEC, Bank of England]
    choose --> html[HTML listing page<br/>FCA news/publications]
    choose --> item[Item-level page fetch]

    rss --> normalize[Normalize into IngestedDocument]
    html --> item
    item --> normalize

    normalize --> hash[Create content hash]
    hash --> duplicate{Already stored?}
    duplicate -->|yes| skip[Skip duplicate]
    duplicate -->|no| store[Store Document in SQLite]
    store --> chunks[Build chunks]
    chunks --> store_chunks[Store Chunk rows]
    store_chunks --> embed[Create local embeddings]
    embed --> opensearch[Index chunks in OpenSearch]
    opensearch --> done[Ready for retrieval]
```

## 3. Route-Aware Query Pipeline

```mermaid
flowchart TD
    question[User question] --> classify[Query classifier]
    classify --> qtype{Question class}

    qtype -->|definition_lookup| simple[Route A: simple lookup<br/>top-3, no judge]
    qtype -->|general_question| medium
    qtype -->|obligation or comparison| medium[Route B: medium reasoning<br/>top-8, reranker]
    qtype -->|multi-hop or compliance decision| complex[Route C: complex reasoning<br/>top-12/15, judge]
    qtype -->|out_of_domain| abstain[Route D: abstain]

    simple --> retrieve[Hybrid retrieval<br/>BM25 + vector + RRF]
    medium --> retrieve
    complex --> retrieve

    retrieve --> maybe_rerank{Use reranker?}
    maybe_rerank -->|no| evidence[Evidence set]
    maybe_rerank -->|yes| rerank[Rerank candidates]
    rerank --> evidence

    evidence --> diagnostics[Evidence diagnostics]
    diagnostics --> route_check{Enough evidence?}
    route_check -->|yes| generate[Generate answer]
    route_check -->|no| abstain

    generate --> verify[Verify answer]
    verify --> verified{Pass?}
    verified -->|yes| final[Final answer with citations]
    verified -->|no| fallback[Fallback once]
    fallback --> fallback_route{Higher route available?}
    fallback_route -->|yes| retrieve
    fallback_route -->|no| abstain

    abstain --> final_abstain[Not answerable from indexed corpus]
```

## 4. Retrieval and Reranking Detail

```mermaid
flowchart LR
    query[Question] --> bm25[BM25 keyword search]
    query --> vector[Dense vector search]
    bm25 --> rrf[RRF fusion]
    vector --> rrf
    rrf --> candidates[Candidate chunks]
    candidates --> reranker[Lexical reranker<br/>future: cross-encoder]
    reranker --> topk[Final evidence top-k]
    topk --> citations[Citation-ready sources]
```

## 5. Evidence Diagnostics and Abstention

```mermaid
flowchart TD
    evidence[Retrieved evidence] --> metrics[Compute diagnostics]
    metrics --> relevance[Top-k relevance]
    metrics --> margin[Score margin]
    metrics --> spread[Source document spread]
    metrics --> strong[Strong passage count]
    metrics --> risk[Risk markers]
    metrics --> xref[Cross-reference hints]

    relevance --> decision{Can answer?}
    margin --> decision
    spread --> decision
    strong --> decision
    risk --> decision
    xref --> decision

    decision -->|yes| generation[Continue to generation]
    decision -->|no| abstain[Return abstention]
```

## 6. Verification and Fallback

```mermaid
flowchart TD
    answer[Generated answer] --> citation[Citation check]
    citation --> answerability[Answerability check]
    answerability --> faithfulness[Faithfulness check<br/>basic now, stronger later]
    faithfulness --> judge{Judge required?}
    judge -->|no| passcheck{Pass?}
    judge -->|yes| llmjudge[LLM-as-a-judge]
    llmjudge --> passcheck

    passcheck -->|yes| final[Return final answer]
    passcheck -->|no| retry{Retry budget left?}
    retry -->|yes| stronger[Escalate route<br/>more top-k, reranker, stronger model]
    stronger --> answer
    retry -->|no| fallback[Return fallback abstention]
```

## 7. Evaluation Architecture

```mermaid
flowchart TD
    questions[Evaluation questions<br/>questions.jsonl] --> basic[Layer 1: basic local evaluation]
    basic --> metrics[Basic metrics<br/>sources, latency, abstention, overlap]
    basic --> results[(evaluation/results)]

    questions --> judge[Layer 2: LLM-as-a-judge]
    judge --> judge_metrics[Faithfulness, relevance,<br/>source support, caution]
    judge_metrics --> results

    questions --> ragas[Layer 3: RAGAS]
    ragas --> ragas_metrics[Context precision/recall,<br/>faithfulness, relevancy]
    ragas_metrics --> results

    questions --> deepeval[Layer 4: DeepEval]
    deepeval --> deepeval_metrics[Test-case style checks]
    deepeval_metrics --> results
```

## 8. Local to Cloud Mapping

```mermaid
flowchart LR
    subgraph Local
        local_frontend[Streamlit container]
        local_backend[FastAPI container]
        local_db[(SQLite)]
        local_search[(OpenSearch container)]
        local_env[.env]
        local_logs[Local logs]
    end

    subgraph AWS_Target[AWS target]
        cloud_frontend[ECS/Fargate or hosted Streamlit]
        cloud_backend[ECS/Fargate FastAPI service]
        cloud_db[(RDS PostgreSQL)]
        cloud_search[(Amazon OpenSearch Service)]
        cloud_secrets[AWS Secrets Manager]
        cloud_logs[CloudWatch]
        scheduler[EventBridge scheduled ingestion]
    end

    local_frontend --> cloud_frontend
    local_backend --> cloud_backend
    local_db --> cloud_db
    local_search --> cloud_search
    local_env --> cloud_secrets
    local_logs --> cloud_logs
    local_backend --> scheduler
```
