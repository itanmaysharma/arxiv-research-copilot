from types import SimpleNamespace

import json

from src.schemas.parsed_paper import ParsedDocument, ParsedSection
from src.services.ingestion.arxiv_ingestor import ingest_stage_parse


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
        self.commits = 0

    def execute(self, _query):
        return FakeResult(self.papers)

    def commit(self):
        self.commits += 1


def _paper(pid: int, arxiv_id: str, abstract: str, full_text: str | None = None):
    return SimpleNamespace(
        id=pid,
        arxiv_id=arxiv_id,
        abstract=abstract,
        full_text=full_text,
        pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
    )


def test_ingest_stage_parse_handles_success_failure_and_fallback(monkeypatch):
    p1 = _paper(1, "2603.10001v1", "abstract-1")
    p2 = _paper(2, "2603.10002v1", "abstract-2")
    p3 = _paper(3, "2603.10003v1", "abstract-3", full_text="already parsed")

    class Parser:
        def parse_document(self, url: str) -> ParsedDocument:
            if "10001" in url:
                return ParsedDocument(
                    full_text="parsed text one",
                    sections=[ParsedSection(title="Intro", text="parsed text one", order=1)],
                    references=[],
                    metadata={"provider": "test", "status": "ok"},
                )
            if "10002" in url:
                raise RuntimeError("broken pdf")
            return ParsedDocument(full_text="", sections=[], references=[], metadata={"status": "empty"})

    db = FakeDB([p1, p2, p3])
    monkeypatch.setattr("src.services.ingestion.arxiv_ingestor.make_pdf_parser", lambda: Parser())

    result = ingest_stage_parse(db=db, limit=10)

    assert result["stage"] == "parse"
    assert result["scanned"] == 3
    assert result["parsed"] == 1
    assert result["fallback_to_abstract"] == 1
    assert result["skipped"] == 1
    assert result["parse_failures"] == 1

    assert p1.full_text == "parsed text one"
    assert p2.full_text == "abstract-2"
    assert p3.full_text == "already parsed"
    assert json.loads(p1.parser_metadata_json)["sections"][0]["title"] == "Intro"
    assert json.loads(p2.parser_metadata_json)["status"] == "fallback_to_abstract"
    assert db.commits == 1
