def run_grade_documents(question: str, sources: list[dict], min_sources: int = 2) -> tuple[bool, str]:
    if not sources:
        return False, "No sources retrieved"

    q = question.lower()
    keyword_hits = 0
    for source in sources:
        title = str(source.get("title", "")).lower()
        arxiv_id = str(source.get("arxiv_id", "")).lower()
        if any(token in title or token in arxiv_id for token in q.split() if len(token) > 3):
            keyword_hits += 1

    if len(sources) < min_sources and keyword_hits == 0:
        return False, "Too few sources and weak lexical overlap"

    if keyword_hits == 0:
        return False, "Retrieved sources do not match query intent strongly"

    return True, f"Retrieved {len(sources)} sources with acceptable relevance"
