def run_rewrite(question: str) -> str:
    q = question.strip()
    # Minimal deterministic rewrite for retrieval robustness
    replacements = {
        "optimize for": "optimization objectives",
        "focus on": "key objectives",
        "about": "main contributions of",
    }
    rewritten = q.lower()
    for src, tgt in replacements.items():
        rewritten = rewritten.replace(src, tgt)
    return rewritten
