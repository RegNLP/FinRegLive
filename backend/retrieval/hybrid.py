# Step 07 - Hybrid Retrieval
#
# Role:
#   Combine BM25 and vector retrieval results.
#
# Why this exists:
#   BM25 is good for exact terms, while vector search is good for semantic
#   similarity. Hybrid retrieval uses both signals to produce stronger evidence
#   candidates for RAG.
#
# Input:
#   User query and top_k.
#
# Output:
#   Ranked RetrievalResult objects.

import argparse

from backend.retrieval.bm25 import retrieve_bm25
from backend.retrieval.common import print_results
from backend.retrieval.models import RetrievalResult
from backend.retrieval.vector import retrieve_vector


def reciprocal_rank_fusion(
    result_lists: list[list[RetrievalResult]],
    top_k: int,
    rrf_k: int = 60,
) -> list[RetrievalResult]:
    fused_scores: dict[str, float] = {}
    results_by_chunk_id: dict[str, RetrievalResult] = {}

    for results in result_lists:
        for result in results:
            fused_scores[result.chunk_id] = fused_scores.get(result.chunk_id, 0.0) + (
                1.0 / (rrf_k + result.rank)
            )
            results_by_chunk_id.setdefault(result.chunk_id, result)

    ranked_chunk_ids = sorted(
        fused_scores,
        key=lambda chunk_id: fused_scores[chunk_id],
        reverse=True,
    )[:top_k]

    fused_results: list[RetrievalResult] = []
    for rank, chunk_id in enumerate(ranked_chunk_ids, start=1):
        result = results_by_chunk_id[chunk_id].model_copy()
        result.rank = rank
        result.score = fused_scores[chunk_id]
        result.retrieval_method = "hybrid"
        fused_results.append(result)

    return fused_results


def retrieve_hybrid(query: str, top_k: int = 5) -> list[RetrievalResult]:
    bm25_results = retrieve_bm25(query, top_k=top_k)
    vector_results = retrieve_vector(query, top_k=top_k)
    return reciprocal_rank_fusion([bm25_results, vector_results], top_k=top_k)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run hybrid retrieval.")
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    print_results(retrieve_hybrid(args.query, top_k=args.top_k))


if __name__ == "__main__":
    main()
