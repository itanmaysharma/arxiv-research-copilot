from src.services.ollama.client import OllamaClient


def run_generate(question: str, context: str) -> str:
    prompt = (
        "You are a research assistant. Answer ONLY from provided context. "
        "If insufficient, say insufficient context.\n\n"
        f"Question: {question}\n\n"
        f"Context:\n{context}\n\n"
        "Answer:"
    )
    return OllamaClient().generate(prompt)
