from src.schemas.hybrid_search import HybridSearchHit


def rrf_fuse(keyword_hits: list[dict], vector_hits: list[dict], k: int, min_score: float = 0.0) -> list[HybridSearchHit]:
    scores: dict[int, float] = {}
    meta: dict[int, dict] = {}

    for rank, hit in enumerate(keyword_hits, start=1):
        source = hit["_source"]
        paper_id = int(source["paper_id"])
        scores[paper_id] = scores.get(paper_id, 0.0) + (1.0 / (k + rank))
        meta.setdefault(
            paper_id,
            {"arxiv_id": source["arxiv_id"], "title": source["title"], "sources": set()},
        )
        meta[paper_id]["sources"].add("bm25")

    for rank, hit in enumerate(vector_hits, start=1):
        source = hit["_source"]
        paper_id = int(source["paper_id"])
        scores[paper_id] = scores.get(paper_id, 0.0) + (1.0 / (k + rank))
        meta.setdefault(
            paper_id,
            {"arxiv_id": source["arxiv_id"], "title": source["title"], "sources": set()},
        )
        meta[paper_id]["sources"].add("vector")

    fused = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if min_score > 0:
        fused = [item for item in fused if item[1] >= min_score]

    return [
        HybridSearchHit(
            paper_id=paper_id,
            arxiv_id=meta[paper_id]["arxiv_id"],
            title=meta[paper_id]["title"],
            score=score,
            sources=sorted(list(meta[paper_id]["sources"])),
        )
        for paper_id, score in fused
    ]
