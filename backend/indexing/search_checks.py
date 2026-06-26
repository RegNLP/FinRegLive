# Step 06F - Manual OpenSearch Checks
#
# Role:
#   Run simple BM25 and vector searches against the OpenSearch chunk index.
#
# Why this exists:
#   Before building the retrieval layer, we need to prove that OpenSearch can
#   return indexed chunks using both keyword search and vector search.
#
# Input:
#   A text query and the indexed OpenSearch chunk documents.
#
# Output:
#   Search result summaries printed to the terminal.

import argparse

from backend.config import get_settings
from backend.indexing.embeddings import embed_text
from backend.search.client import get_search_client


def bm25_search(query: str, size: int = 3) -> list[dict]:
    settings = get_settings()
    client = get_search_client()

    response = client.search(
        index=settings.search.index_name,
        body={
            "size": size,
            "_source": {"excludes": ["embedding"]},
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["chunk_text", "title"],
                }
            },
        },
    )
    return response["hits"]["hits"]


def vector_search(query: str, size: int = 3) -> list[dict]:
    settings = get_settings()
    client = get_search_client()
    query_vector = embed_text(query)

    response = client.search(
        index=settings.search.index_name,
        body={
            "size": size,
            "_source": {"excludes": ["embedding"]},
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_vector,
                        "k": size,
                    }
                }
            },
        },
    )
    return response["hits"]["hits"]


def print_results(label: str, results: list[dict]) -> None:
    print(f"\n{label}\n")

    if not results:
        print("No results.")
        return

    for rank, result in enumerate(results, start=1):
        source = result["_source"]
        print(f"{rank}. score={result['_score']:.6f}")
        print(f"   title={source['title']}")
        print(f"   source={source['source_name']}")
        print(f"   url={source['source_url']}")
        print(f"   text={source['chunk_text'][:240]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run manual OpenSearch search checks.")
    parser.add_argument("query", help="Search query.")
    parser.add_argument("--size", type=int, default=3)
    args = parser.parse_args()

    print_results("BM25 results", bm25_search(args.query, size=args.size))
    print_results("Vector results", vector_search(args.query, size=args.size))


if __name__ == "__main__":
    main()
