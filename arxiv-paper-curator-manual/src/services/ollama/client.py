import json
import httpx


class OllamaClient:
    def __init__(self, base_url: str = "http://ollama:11434", model: str = "llama3.2:3b") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, prompt: str) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data.get("response", "").strip()

    def stream_generate(self, prompt: str):
        payload = {"model": self.model, "prompt": prompt, "stream": True}
        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    token = data.get("response", "")
                    done = data.get("done", False)
                    if token:
                        yield token
                    if done:
                        break
