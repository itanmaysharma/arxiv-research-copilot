from opensearchpy import OpenSearch


def _client() -> OpenSearch:
    return OpenSearch(
        hosts=[{"host": "opensearch", "port": 9200}],
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False,
    )


def run_retrieve(question: str, top_k: int, min_score: float = 2.0) -> tuple[str, list[dict]]:
    body = {
        "size": top_k,
        "query": {
            "multi_match": {
                "query": question,
                "fields": ["chunk_text^2", "title", "authors"],
                "type": "best_fields",
                "operator": "or",
                "minimum_should_match": "50%",
            }
        },
    }
    resp = _client().search(index="paper_chunks_bm25", body=body)
    hits = resp["hits"]["hits"]

    if not hits:
        return "", []

    top_score = float(hits[0].get("_score") or 0.0)
    if top_score < min_score:
        return "", []

    sources = []
    context_parts = []
    for h in hits:
        s = h["_source"]
        sources.append(
            {
                "paper_id": s["paper_id"],
                "arxiv_id": s["arxiv_id"],
                "title": s["title"],
                "chunk_index": s["chunk_index"],
            }
        )
        context_parts.append(f"[{s['arxiv_id']}:{s['chunk_index']}] {s['chunk_text']}")
    return "\n\n".join(context_parts), sources
