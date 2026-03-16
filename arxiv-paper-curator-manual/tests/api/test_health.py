from unittest.mock import MagicMock, patch


def test_health_all_ok(client):
    with patch("src.routers.health.create_engine") as mock_engine, patch(
        "src.routers.health.OpenSearch"
    ) as mock_os:
        conn_ctx = MagicMock()
        conn_ctx.__enter__.return_value.execute.return_value = None
        mock_engine.return_value.connect.return_value = conn_ctx
        mock_os.return_value.ping.return_value = True

        resp = client.get("/health")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert payload["services"]["api"] == "ok"
    assert payload["services"]["postgres"] == "ok"
    assert payload["services"]["opensearch"] == "ok"


def test_health_degraded_when_dependencies_fail(client):
    with patch("src.routers.health.create_engine", side_effect=RuntimeError("db down")), patch(
        "src.routers.health.OpenSearch", side_effect=RuntimeError("os down")
    ):
        resp = client.get("/health")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "degraded"
    assert payload["services"]["postgres"] == "down"
    assert payload["services"]["opensearch"] == "down"
