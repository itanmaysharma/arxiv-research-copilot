import json
import os
from typing import Any

import gradio as gr
import httpx

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def _json_pretty(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=True)


def _post_json(path: str, payload: dict[str, Any], timeout: float = 120.0) -> dict[str, Any]:
    url = f"{API_BASE_URL}{path}"
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


def ask_once(question: str, top_k: int) -> tuple[str, str]:
    if not question.strip():
        return "", "Question is required."
    try:
        data = _post_json("/api/v1/ask", {"question": question, "top_k": int(top_k)})
        return data.get("answer", ""), _json_pretty(data.get("sources", []))
    except Exception as exc:
        return "", f"Ask failed: {exc}"


def ask_stream(question: str, top_k: int):
    if not question.strip():
        yield "", "Question is required."
        return

    url = f"{API_BASE_URL}/api/v1/ask/stream"
    payload = {"question": question, "top_k": int(top_k)}

    answer = ""
    sources: list[dict[str, Any]] = []
    try:
        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    if not line.startswith("data: "):
                        continue
                    raw = line[len("data: ") :]
                    event = json.loads(raw)
                    event_type = event.get("type")
                    if event_type == "sources":
                        sources = event.get("data", [])
                    elif event_type == "token":
                        answer += event.get("data", "")
                    elif event_type == "done":
                        break
                    yield answer, _json_pretty(sources)
    except Exception as exc:
        yield answer, f"Stream failed: {exc}"


def run_hybrid_search(query: str, size: int, rrf_k: int) -> str:
    if not query.strip():
        return "Query is required."
    try:
        data = _post_json(
            "/api/v1/hybrid-search",
            {"query": query, "size": int(size), "rrf_k": int(rrf_k)},
        )
        return _json_pretty(data)
    except Exception as exc:
        return f"Hybrid search failed: {exc}"


def run_agentic_ask(question: str, top_k: int) -> str:
    if not question.strip():
        return "Question is required."
    try:
        data = _post_json("/api/v1/agentic-ask", {"question": question, "top_k": int(top_k)})
        return _json_pretty(data)
    except Exception as exc:
        return f"Agentic ask failed: {exc}"


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Arxiv Curator - UI") as demo:
        gr.Markdown("# Arxiv Curator UI")
        gr.Markdown("Use this UI to test Ask, streaming Ask, hybrid search, and agentic ask.")

        gr.Textbox(label="API Base URL", value=API_BASE_URL, interactive=False)

        with gr.Tab("Ask"):
            q1 = gr.Textbox(label="Question", lines=3)
            topk1 = gr.Slider(label="Top K", minimum=1, maximum=10, step=1, value=3)
            btn1 = gr.Button("Ask")
            ans1 = gr.Textbox(label="Answer", lines=8)
            src1 = gr.Code(label="Sources", language="json")
            btn1.click(fn=ask_once, inputs=[q1, topk1], outputs=[ans1, src1])

        with gr.Tab("Ask Stream"):
            q2 = gr.Textbox(label="Question", lines=3)
            topk2 = gr.Slider(label="Top K", minimum=1, maximum=10, step=1, value=3)
            btn2 = gr.Button("Stream Ask")
            ans2 = gr.Textbox(label="Streaming Answer", lines=8)
            src2 = gr.Code(label="Sources", language="json")
            btn2.click(fn=ask_stream, inputs=[q2, topk2], outputs=[ans2, src2])

        with gr.Tab("Hybrid Search"):
            query = gr.Textbox(label="Query", lines=2)
            size = gr.Slider(label="Size", minimum=1, maximum=20, step=1, value=5)
            rrf_k = gr.Slider(label="RRF K", minimum=1, maximum=200, step=1, value=60)
            btn3 = gr.Button("Run Hybrid Search")
            out3 = gr.Code(label="Response JSON", language="json")
            btn3.click(fn=run_hybrid_search, inputs=[query, size, rrf_k], outputs=[out3])

        with gr.Tab("Agentic Ask"):
            q4 = gr.Textbox(label="Question", lines=3)
            topk4 = gr.Slider(label="Top K", minimum=1, maximum=10, step=1, value=3)
            btn4 = gr.Button("Run Agentic Ask")
            out4 = gr.Code(label="Response JSON", language="json")
            btn4.click(fn=run_agentic_ask, inputs=[q4, topk4], outputs=[out4])

    return demo
