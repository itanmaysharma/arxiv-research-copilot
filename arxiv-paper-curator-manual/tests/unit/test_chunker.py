import pytest

from src.services.indexing.text_chunker import TextChunker


def test_chunker_invalid_config():
    with pytest.raises(ValueError):
        TextChunker(chunk_size=0, overlap=0)
    with pytest.raises(ValueError):
        TextChunker(chunk_size=10, overlap=-1)
    with pytest.raises(ValueError):
        TextChunker(chunk_size=10, overlap=10)


def test_chunker_empty_text_returns_empty_list():
    chunker = TextChunker(chunk_size=50, overlap=10)
    assert chunker.chunk_text("   ") == []


def test_chunker_creates_overlapping_chunks():
    text = " ".join(["token"] * 60)
    chunker = TextChunker(chunk_size=40, overlap=10)
    chunks = chunker.chunk_text(text)

    assert len(chunks) > 1
    assert chunks[0].chunk_id == 1
    assert chunks[1].chunk_id == 2
    assert chunks[0].start_char == 0
    assert chunks[1].start_char <= chunks[0].end_char
    assert chunks[-1].end_char <= len(" ".join(text.split()).strip())
