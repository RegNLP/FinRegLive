# Step 07 - Vector Retrieval
#
# Role:
#   Retrieve evidence chunks with OpenSearch k-NN vector search.
#
# Why this exists:
#   Vector retrieval can find semantically related chunks even when the query
#   and source text use different words.
#
# Input:
#   User query and top_k.
#
# Output:
#   Ranked RetrievalResult objects.

import argparse

from backend.config import get_settings
from backend.indexing.embeddings import embed_text
from backend.retrieval.common import hit_to_result, print_results
from backend.retrieval.models import RetrievalResult
from backend.search.client import get_search_client


def retrieve_vector(query: str, top_k: int = 5) -> list[RetrievalResult]:
    settings = get_settings()
    client = get_search_client()
    query_vector = embed_text(query)

    response = client.search(
        index=settings.search.index_name,
        body={
            "size": top_k,
            "_source": {"excludes": ["embedding"]},
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_vector,
                        "k": top_k,
                    }
                }
            },
        },
    )

    return [
        hit_to_result(hit, rank=rank, retrieval_method="vector")
        for rank, hit in enumerate(response["hits"]["hits"], start=1)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run vector retrieval.")
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    print_results(retrieve_vector(args.query, top_k=args.top_k))


if __name__ == "__main__":
    main()
