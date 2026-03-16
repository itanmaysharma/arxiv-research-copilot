from functools import lru_cache

from opensearchpy import OpenSearch

from src.config import settings


@lru_cache(maxsize=1)
def make_opensearch_client() -> OpenSearch:
    return OpenSearch(
        hosts=[settings.opensearch.url],
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False,
    )
