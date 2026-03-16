from unittest.mock import patch

from src.services.ingestion.arxiv_ingestor import ingest_pipeline


class DummyDB:
    pass


def test_ingest_pipeline_calls_stages_in_order() -> None:
    db = DummyDB()

    with (
        patch("src.services.ingestion.arxiv_ingestor.ingest_stage_fetch_store", return_value={"stage": "fetch_store"}) as fetch_store,
        patch("src.services.ingestion.arxiv_ingestor.ingest_stage_parse", return_value={"stage": "parse"}) as parse_stage,
        patch("src.services.ingestion.arxiv_ingestor.ingest_stage_chunk", return_value={"stage": "chunk"}) as chunk_stage,
        patch("src.services.ingestion.arxiv_ingestor.ingest_stage_index", return_value={"stage": "index"}) as index_stage,
    ):
        result = ingest_pipeline(db=db, max_results=4)

    fetch_store.assert_called_once_with(db=db, max_results=4)
    parse_stage.assert_called_once_with(db=db, limit=12)
    chunk_stage.assert_called_once_with(db=db, limit=12)
    index_stage.assert_called_once_with(db=db)

    assert result["pipeline"] == "arxiv_ingest_v2"
    assert result["fetch_store"]["stage"] == "fetch_store"
    assert result["parse"]["stage"] == "parse"
    assert result["chunk"]["stage"] == "chunk"
    assert result["index"]["stage"] == "index"
