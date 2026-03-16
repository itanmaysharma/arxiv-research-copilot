from types import SimpleNamespace
from unittest.mock import patch

from src.dependencies import get_db
from src.main import app


def test_ingest_stage_routes_call_services(client):
    fake_db = SimpleNamespace()
    app.dependency_overrides[get_db] = lambda: fake_db

    with (
        patch("src.routers.papers.ingest_stage_fetch_store", return_value={"stage": "fetch_store"}) as fetch_store,
        patch("src.routers.papers.ingest_stage_parse", return_value={"stage": "parse"}) as parse_stage,
        patch("src.routers.papers.ingest_stage_chunk", return_value={"stage": "chunk"}) as chunk_stage,
        patch("src.routers.papers.ingest_stage_index", return_value={"stage": "index"}) as index_stage,
    ):
        try:
            r1 = client.post("/api/v1/papers/ingest/fetch-store?max_results=2")
            r2 = client.post("/api/v1/papers/ingest/parse?limit=10")
            r3 = client.post("/api/v1/papers/ingest/chunk?limit=10")
            r4 = client.post("/api/v1/papers/ingest/index")
        finally:
            app.dependency_overrides.clear()

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 200
    assert r4.status_code == 200

    fetch_store.assert_called_once_with(db=fake_db, max_results=2)
    parse_stage.assert_called_once_with(db=fake_db, limit=10)
    chunk_stage.assert_called_once_with(db=fake_db, limit=10)
    index_stage.assert_called_once_with(db=fake_db)
