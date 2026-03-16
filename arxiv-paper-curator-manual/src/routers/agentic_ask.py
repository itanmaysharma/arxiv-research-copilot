from fastapi import APIRouter, Depends, Response

from src.dependencies import get_tracer_service
from src.schemas.agentic import AgenticAskRequest, AgenticAskResponse
from src.services.agents.agentic_rag import run_agentic_workflow
from src.services.langfuse.tracer import Tracer

router = APIRouter(prefix="/api/v1/agentic-ask", tags=["agentic"])


def _citations_from_sources(sources: list[dict]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for source in sources:
        arxiv_id = str(source.get("arxiv_id", "")).strip()
        if not arxiv_id or arxiv_id in seen:
            continue
        seen.add(arxiv_id)
        ordered.append(arxiv_id)
    return ordered


def _step_value(step: dict | object, key: str):
    if isinstance(step, dict):
        return step.get(key)
    return getattr(step, key, None)


def _retrieval_attempts(steps: list[dict] | list[object]) -> int:
    return sum(1 for s in steps if _step_value(s, "node") in {"retrieve", "retrieve_retry"})


def _confidence_from_steps_and_sources(steps: list[dict] | list[object], sources: list[dict]) -> float:
    if not sources:
        return 0.0

    score = 0.3 + (0.12 * len(sources))
    if any(_step_value(step, "status") in {"blocked", "reject", "empty"} for step in steps):
        score -= 0.15
    if any(_step_value(step, "node") == "grade_documents" and _step_value(step, "status") == "ok" for step in steps):
        score += 0.2
    return round(max(0.0, min(1.0, score)), 2)


@router.post("", response_model=AgenticAskResponse)
def agentic_ask(
    request: AgenticAskRequest,
    response: Response,
    tracer_service: Tracer = Depends(get_tracer_service),
) -> AgenticAskResponse:
    trace = tracer_service.start_trace("agentic_ask")

    with trace.span("agentic_workflow", top_k=request.top_k):
        answer, steps, sources = run_agentic_workflow(
            question=request.question,
            top_k=request.top_k,
        )

    elapsed_ms = trace.finish(status="ok", steps=len(steps), sources=len(sources))
    response.headers["X-Trace-Id"] = trace.trace_id
    response.headers["X-Latency-Ms"] = str(elapsed_ms)

    return AgenticAskResponse(
        answer=answer,
        steps=steps,
        sources=sources,
        search_mode="agentic_chunk_bm25",
        retrieval_attempts=_retrieval_attempts(steps),
        confidence=_confidence_from_steps_and_sources(steps, sources),
        citations=_citations_from_sources(sources),
    )
