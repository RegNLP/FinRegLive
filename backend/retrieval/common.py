# Step 07 - Retrieval Common Helpers
#
# Role:
#   Convert OpenSearch hits into structured retrieval results.
#
# Why this exists:
#   BM25, vector, and hybrid retrieval all need consistent result formatting.
#
# Input:
#   OpenSearch search hits.
#
# Output:
#   RetrievalResult objects.

from backend.retrieval.models import RetrievalResult


def hit_to_result(hit: dict, rank: int, retrieval_method: str) -> RetrievalResult:
    source = hit["_source"]
    return RetrievalResult(
        rank=rank,
        score=float(hit["_score"]),
        retrieval_method=retrieval_method,
        chunk_id=str(source["chunk_id"]),
        document_id=int(source["document_id"]),
        chunk_index=int(source["chunk_index"]),
        title=source["title"],
        source_name=source["source_name"],
        source_url=source["source_url"],
        publication_date=source.get("publication_date"),
        chunk_text=source["chunk_text"],
    )


def print_results(results: list[RetrievalResult]) -> None:
    if not results:
        print("No results.")
        return

    for result in results:
        print(f"{result.rank}. score={result.score:.6f} method={result.retrieval_method}")
        print(f"   title={result.title}")
        print(f"   source={result.source_name}")
        print(f"   url={result.source_url}")
        print(f"   text={result.chunk_text[:260]}")
