from datetime import datetime, timezone

from src.dependencies import get_db, get_tracer_service
from src.main import app


class FakeDB:
    def __init__(self, fail_commit: bool = False):
        self.fail_commit = fail_commit
        self.added = []
        self.next_id = 1

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        if self.fail_commit:
            from sqlalchemy.exc import SQLAlchemyError

            raise SQLAlchemyError("db write failed")

    def refresh(self, obj):
        obj.id = self.next_id
        self.next_id += 1
        obj.created_at = datetime(2026, 3, 14, tzinfo=timezone.utc)


def test_feedback_create_success(client):
    db = FakeDB()
    calls = []

    class TracerStub:
        def submit_feedback(self, **kwargs):
            calls.append(kwargs)
            return True

    tracer = TracerStub()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_tracer_service] = lambda: tracer

    try:
        response = client.post(
            "/api/v1/feedback",
            json={
                "trace_id": "trace-12345678",
                "score": 5,
                "comment": "Very helpful answer",
                "channel": "api",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "recorded"
    assert payload["trace_id"] == "trace-12345678"
    assert len(calls) == 1
    assert calls[0]["trace_id"] == "trace-12345678"
    assert calls[0]["score"] == 5


def test_feedback_validation_error(client):
    response = client.post(
        "/api/v1/feedback",
        json={
            "trace_id": "short",
            "score": 6,
            "comment": "invalid",
            "channel": "api",
        },
    )
    assert response.status_code == 422


def test_feedback_db_failure(client):
    db = FakeDB(fail_commit=True)
    tracer = type("Tracer", (), {"submit_feedback": lambda self, **kwargs: True})()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_tracer_service] = lambda: tracer

    try:
        response = client.post(
            "/api/v1/feedback",
            json={
                "trace_id": "trace-abcdef12",
                "score": 3,
                "comment": "ok",
                "channel": "api",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert "Failed to store feedback" in response.json()["detail"]
