def run_guardrail(question: str) -> tuple[bool, str]:
    blocked_terms = ["hack password", "malware", "exploit zero-day"]
    q = question.lower()
    for term in blocked_terms:
        if term in q:
            return False, f"Blocked by guardrail term: {term}"
    return True, "Guardrail passed"
