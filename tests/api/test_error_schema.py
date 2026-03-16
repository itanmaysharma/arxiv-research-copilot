from src.dependencies import get_db, get_tracer_service
from src.main import app


class EmptyDB:
    def get(self, _model, _paper_id):
        return None


class FeedbackFailDB:
    def add(self, _obj):
        return None

    def commit(self):
        from sqlalchemy.exc import SQLAlchemyError

        raise SQLAlchemyError("forced failure")

    def refresh(self, _obj):
        return None


def test_not_found_error_schema_for_papers(client):
    app.dependency_overrides[get_db] = lambda: EmptyDB()
    try:
        resp = client.get("/api/v1/papers/9999")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    payload = resp.json()
    assert payload["detail"] == "Paper not found"
    assert payload["error"]["code"] == "PAPER_NOT_FOUND"
    assert payload["error"]["context"]["paper_id"] == 9999


def test_bad_request_error_schema_for_ingest_limit(client):
    resp = client.post("/api/v1/papers/ingest?max_results=0")
    assert resp.status_code == 400
    payload = resp.json()
    assert payload["detail"] == "max_results must be between 1 and 50"
    assert payload["error"]["code"] == "INVALID_MAX_RESULTS"


def test_storage_error_schema_for_feedback(client):
    tracer = type("Tracer", (), {"submit_feedback": lambda self, **kwargs: False})()
    app.dependency_overrides[get_db] = lambda: FeedbackFailDB()
    app.dependency_overrides[get_tracer_service] = lambda: tracer
    try:
        resp = client.post(
            "/api/v1/feedback",
            json={
                "trace_id": "trace-xyz-1234",
                "score": 3,
                "comment": "ok",
                "channel": "api",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 500
    payload = resp.json()
    assert "Failed to store feedback" in payload["detail"]
    assert payload["error"]["code"] == "FEEDBACK_STORE_FAILED"
