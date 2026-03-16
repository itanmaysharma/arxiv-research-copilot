import pytest

from src.config import Settings


def _make_settings(**overrides) -> Settings:
    base = {
        "database_url": "postgresql+psycopg://u:p@localhost:5432/db",
        "opensearch_url": "http://localhost:9200",
        "ollama_base_url": "http://localhost:11434",
    }
    base.update(overrides)
    return Settings(**base)


def test_nested_views_and_legacy_fields_are_both_available():
    settings = _make_settings(app_name="demo-app", chunk_size=700, chunk_overlap=100)

    assert settings.app_name == "demo-app"
    assert settings.app.name == "demo-app"
    assert settings.database.url == settings.database_url
    assert settings.opensearch.url == settings.opensearch_url
    assert settings.chunking.chunk_size == 700
    assert settings.chunking.overlap == 100


def test_ollama_and_embeddings_nested_mapping():
    settings = _make_settings(
        ollama_model="phi3:mini",
        jina_embedding_model="jina-embeddings-v3",
        embedding_dimensions=1024,
    )

    assert settings.ollama.model == "phi3:mini"
    assert settings.embeddings.model == "jina-embeddings-v3"
    assert settings.embeddings.dimensions == 1024


def test_missing_or_invalid_critical_values_fail_fast():
    with pytest.raises(ValueError):
        _make_settings(database_url="")

    with pytest.raises(ValueError):
        _make_settings(chunk_size=0)

    with pytest.raises(ValueError):
        _make_settings(chunk_overlap=-1)
