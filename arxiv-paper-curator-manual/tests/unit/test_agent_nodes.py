from src.services.agents.nodes.grade_documents_node import run_grade_documents
from src.services.agents.nodes.out_of_scope_node import run_out_of_scope


def test_out_of_scope_blocks_non_research_question() -> None:
    blocked, reason = run_out_of_scope("Who won the football match yesterday?")
    assert blocked is True
    assert "outside" in reason.lower() or "scope" in reason.lower()


def test_out_of_scope_allows_research_question() -> None:
    blocked, reason = run_out_of_scope("What does PONTE optimize for in explanations?")
    assert blocked is False
    assert "in-scope" in reason.lower()


def test_grade_documents_rejects_empty_sources() -> None:
    ok, reason = run_grade_documents("test question", [])
    assert ok is False
    assert "no sources" in reason.lower()


def test_grade_documents_accepts_overlap() -> None:
    sources = [{"title": "PONTE trustworthy explanations", "arxiv_id": "2603.06485v1"}]
    ok, reason = run_grade_documents("What does PONTE optimize for?", sources, min_sources=1)
    assert ok is True
    assert "acceptable relevance" in reason.lower()
