from unittest.mock import patch


def test_agentic_ask_returns_workflow_output(client):
    mock_steps = [
        {"node": "guardrail", "status": "ok", "detail": "Guardrail passed"},
        {"node": "retrieve", "status": "ok", "detail": "Retrieved 2 chunks"},
        {"node": "generate", "status": "ok", "detail": "Generated answer"},
    ]
    mock_sources = [{"paper_id": 10, "arxiv_id": "2603.06485v1", "chunk_index": 1}]

    with patch(
        "src.routers.agentic_ask.run_agentic_workflow",
        return_value=("Agentic answer.", mock_steps, mock_sources),
    ):
        resp = client.post(
            "/api/v1/agentic-ask",
            json={"question": "What does PONTE optimize for?", "top_k": 3},
        )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["answer"] == "Agentic answer."
    assert payload["steps"][0]["node"] == "guardrail"
    assert payload["sources"][0]["arxiv_id"] == "2603.06485v1"
    assert payload["search_mode"] == "agentic_chunk_bm25"
    assert payload["retrieval_attempts"] == 1
    assert payload["confidence"] > 0
    assert payload["citations"] == ["2603.06485v1"]
    assert "x-trace-id" in resp.headers
    assert "x-latency-ms" in resp.headers


def test_agentic_ask_validation_error(client):
    resp = client.post(
        "/api/v1/agentic-ask",
        json={"question": "ok", "top_k": 3},
    )
    assert resp.status_code == 422


def test_agentic_ask_returns_out_of_scope_steps(client):
    mock_steps = [
        {"node": "guardrail", "status": "ok", "detail": "Guardrail passed"},
        {
            "node": "out_of_scope",
            "status": "blocked",
            "detail": "Question appears outside arXiv research assistant scope",
        },
    ]

    with patch(
        "src.routers.agentic_ask.run_agentic_workflow",
        return_value=("Question is out of scope for this research assistant.", mock_steps, []),
    ):
        resp = client.post(
            "/api/v1/agentic-ask",
            json={"question": "Who won yesterday?", "top_k": 3},
        )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["steps"][1]["node"] == "out_of_scope"
    assert payload["steps"][1]["status"] == "blocked"
    assert payload["retrieval_attempts"] == 0
    assert payload["confidence"] == 0.0
    assert payload["citations"] == []
