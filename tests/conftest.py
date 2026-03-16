import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

# Tests should not depend on a developer .env or CI secrets just to import the app.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test_db")
os.environ.setdefault("OPENSEARCH_URL", "http://localhost:9200")
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")

from src.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
