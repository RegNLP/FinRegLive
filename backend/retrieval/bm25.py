# Step 07 - BM25 Retrieval
#
# Role:
#   Retrieve evidence chunks with OpenSearch keyword search.
#
# Why this exists:
#   BM25 is strong when important query terms appear directly in the source
#   text. Regulatory and financial search often depends on exact terms.
#
# Input:
#   User query and top_k.
#
# Output:
#   Ranked RetrievalResult objects.

import argparse

from backend.config import get_settings
from backend.retrieval.common import hit_to_result, print_results
from backend.retrieval.models import RetrievalResult
from backend.search.client import get_search_client


def retrieve_bm25(query: str, top_k: int = 5) -> list[RetrievalResult]:
    settings = get_settings()
    client = get_search_client()

    response = client.search(
        index=settings.search.index_name,
        body={
            "size": top_k,
            "_source": {"excludes": ["embedding"]},
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["chunk_text", "title"],
                }
            },
        },
    )

    return [
        hit_to_result(hit, rank=rank, retrieval_method="bm25")
        for rank, hit in enumerate(response["hits"]["hits"], start=1)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BM25 retrieval.")
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    print_results(retrieve_bm25(args.query, top_k=args.top_k))


if __name__ == "__main__":
    main()
