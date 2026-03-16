from datetime import datetime, timezone
from types import SimpleNamespace

from src.dependencies import get_db
from src.main import app


class FakeResult:
    def __init__(self, values):
        self._values = values

    def scalars(self):
        return self

    def all(self):
        return self._values

    def scalar_one_or_none(self):
        if isinstance(self._values, list):
            return self._values[0] if self._values else None
        return self._values


class FakeDB:
    def __init__(self, papers=None):
        self.papers = papers or []
        self.added = []
        self.next_id = 100

    def execute(self, _query):
        return FakeResult(self.papers)

    def get(self, _model, paper_id):
        for p in self.papers:
            if p.id == paper_id:
                return p
        return None

    def add(self, obj):
        obj.id = self.next_id
        self.next_id += 1
        self.added.append(obj)
        self.papers.append(obj)

    def commit(self):
        return None

    def refresh(self, _obj):
        return None


def _paper(
    pid=1,
    arxiv_id="2603.00001v1",
    title="Sample Paper",
    authors="A. Author",
):
    return SimpleNamespace(
        id=pid,
        arxiv_id=arxiv_id,
        title=title,
        authors=authors,
        abstract="sample abstract",
        pdf_url="https://arxiv.org/pdf/2603.00001v1.pdf",
        full_text=None,
        published_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )


def test_list_papers(client):
    db = FakeDB([_paper()])
    app.dependency_overrides[get_db] = lambda: db

    try:
        resp = client.get("/api/v1/papers")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload) == 1
    assert payload[0]["arxiv_id"] == "2603.00001v1"


def test_get_paper_not_found(client):
    db = FakeDB([])
    app.dependency_overrides[get_db] = lambda: db

    try:
        resp = client.get("/api/v1/papers/999")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Paper not found"


def test_create_paper_conflict(client):
    db = FakeDB([_paper(arxiv_id="2603.00099v1")])
    app.dependency_overrides[get_db] = lambda: db

    payload = {
        "arxiv_id": "2603.00099v1",
        "title": "Duplicate Paper",
        "abstract": "duplicate abstract",
        "authors": "b",
        "pdf_url": "https://arxiv.org/pdf/2603.00099v1.pdf",
    }

    try:
        resp = client.post("/api/v1/papers", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]


def test_create_paper_success(client):
    db = FakeDB([])
    app.dependency_overrides[get_db] = lambda: db

    payload = {
        "arxiv_id": "2603.12345v1",
        "title": "New Paper",
        "abstract": "new abstract",
        "authors": "X, Y",
        "pdf_url": "https://arxiv.org/pdf/2603.12345v1.pdf",
    }

    try:
        resp = client.post("/api/v1/papers", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "created"
    assert data["arxiv_id"] == payload["arxiv_id"]
