def run_out_of_scope(question: str) -> tuple[bool, str]:
    q = question.lower().strip()

    blocked_prefixes = (
        "who won",
        "stock price",
        "weather",
        "recipe",
        "movie",
        "celebrity",
    )
    if q.startswith(blocked_prefixes):
        return True, "Question appears outside arXiv research assistant scope"

    generic_terms = ["password", "hack", "crack", "torrent"]
    if any(term in q for term in generic_terms):
        return True, "Question appears outside safe research retrieval scope"

    return False, "In-scope for research assistant"
