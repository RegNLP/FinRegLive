# Step 06B - OpenSearch Client
#
# Role:
#   Create a Python client for the local OpenSearch service.
#
# Why this exists:
#   Indexing and retrieval code should not create OpenSearch connections
#   manually. They should use one shared client helper that reads host settings
#   from the project config.
#
# Input:
#   Search settings from configs/local.yaml.
#
# Output:
#   An OpenSearch client and a helper for checking connectivity.

from opensearchpy import OpenSearch

from backend.config import get_settings


def get_search_client() -> OpenSearch:
    settings = get_settings()
    return OpenSearch(
        hosts=[settings.search.host],
        use_ssl=settings.search.host.startswith("https"),
        verify_certs=False,
    )


def ping_search() -> bool:
    client = get_search_client()
    return bool(client.ping())
