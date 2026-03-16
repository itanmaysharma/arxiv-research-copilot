import json
from types import SimpleNamespace

from src.services.ingestion.arxiv_ingestor import ingest_stage_chunk


class FakeResult:
    def __init__(self, values):
        self._values = values

    def scalars(self):
        return self

    def all(self):
        return self._values


class FakeDB:
    def __init__(self, papers):
        self.papers = papers
        self.added = []
        self.commits = 0

    def execute(self, _query):
        return FakeResult(self.papers)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commits += 1


def _paper_with_sections():
    return SimpleNamespace(
        id=1,
        full_text="ignored when sections exist",
        abstract="fallback abstract",
        parser_metadata_json=json.dumps(
            {
                "sections": [
                    {"title": "Intro", "text": "alpha beta gamma", "order": 1},
                    {"title": "Method", "text": "delta epsilon zeta", "order": 2},
                ]
            }
        ),
    )


def test_ingest_stage_chunk_uses_section_metadata():
    db = FakeDB([_paper_with_sections()])
    result = ingest_stage_chunk(db=db, limit=10)

    assert result["stage"] == "chunk"
    assert result["papers_processed"] == 1
    assert result["chunks_created"] >= 2
    assert result["section_aware_papers"] == 1
    assert db.commits == 1

    titles = [c.section_title for c in db.added]
    assert "Intro" in titles
    assert "Method" in titles
    assert all(c.section_order in (1, 2) for c in db.added)
    assert [c.chunk_index for c in db.added] == list(range(1, len(db.added) + 1))
