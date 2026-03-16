def build_paper_search_query(
    query: str,
    size: int,
    author: str | None = None,
    published_after: str | None = None,
) -> dict:
    filters: list[dict] = []
    if author:
        filters.append({"match": {"authors": author}})
    if published_after:
        filters.append({"range": {"published_at": {"gte": published_after}}})

    return {
        "size": size,
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^2", "abstract", "authors"],
                            "type": "best_fields",
                        }
                    }
                ],
                "filter": filters,
            }
        },
    }


def build_chunk_search_query(query: str, size: int) -> dict:
    return {
        "size": size,
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["chunk_text^2", "title", "authors"],
                "type": "best_fields",
            }
        },
    }


def build_keyword_chunk_search_query(
    query: str,
    size: int,
    from_: int = 0,
    categories: list[str] | None = None,
    latest_papers: bool = False,
) -> dict:
    bool_query: dict = {
        "must": [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["chunk_text^2", "title", "authors"],
                    "type": "best_fields",
                }
            }
        ]
    }
    if categories:
        bool_query["filter"] = [{"terms": {"arxiv_id": categories}}]

    body: dict = {
        "from": from_,
        "size": size,
        "query": {"bool": bool_query},
    }
    if latest_papers:
        body["sort"] = [{"published_at": {"order": "desc"}}, {"_score": {"order": "desc"}}]
    return body


def build_vector_chunk_search_query(
    query_embedding: list[float],
    size: int,
    categories: list[str] | None = None,
) -> dict:
    knn_query = {
        "knn": {
            "embedding": {
                "vector": query_embedding,
                "k": size,
            }
        }
    }

    if not categories:
        return {"size": size, "query": knn_query}

    return {
        "size": size,
        "query": {
            "bool": {
                "must": [knn_query],
                "filter": [{"terms": {"arxiv_id": categories}}],
            }
        },
    }
