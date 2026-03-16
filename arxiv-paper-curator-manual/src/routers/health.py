from fastapi import APIRouter
from opensearchpy import OpenSearch
from sqlalchemy import create_engine, text

from src.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    status = {"api": "ok", "postgres": "down", "opensearch": "down"}

    try:
        engine = create_engine(settings.database.url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["postgres"] = "ok"
    except Exception:
        status["postgres"] = "down"

    try:
        client = OpenSearch(
            hosts=[settings.opensearch.url],
            use_ssl=False,
            verify_certs=False,
            ssl_show_warn=False,
        )
        if client.ping():
            status["opensearch"] = "ok"
    except Exception:
        status["opensearch"] = "down"

    overall = "ok" if all(v == "ok" for v in status.values()) else "degraded"
    return {"status": overall, "services": status}
