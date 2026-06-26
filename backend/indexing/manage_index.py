# Step 06C - Manage OpenSearch Index
#
# Role:
#   Create or recreate the local OpenSearch chunk index.
#
# Why this exists:
#   Before chunks can be indexed, the target OpenSearch index must exist with
#   the correct text, metadata, and vector mappings.
#
# Input:
#   OpenSearch connection settings and index schema.
#
# Output:
#   A created or recreated OpenSearch index.

import argparse

from backend.config import get_settings
from backend.indexing.schema import chunk_index_schema
from backend.search.client import get_search_client


def index_exists() -> bool:
    settings = get_settings()
    client = get_search_client()
    return bool(client.indices.exists(index=settings.search.index_name))


def create_index(recreate: bool = False) -> str:
    settings = get_settings()
    client = get_search_client()
    index_name = settings.search.index_name

    if client.indices.exists(index=index_name):
        if not recreate:
            return f"exists: {index_name}"

        client.indices.delete(index=index_name)

    client.indices.create(index=index_name, body=chunk_index_schema())
    return f"created: {index_name}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the OpenSearch chunk index.")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the index if it already exists.",
    )
    args = parser.parse_args()

    print(create_index(recreate=args.recreate))


if __name__ == "__main__":
    main()
