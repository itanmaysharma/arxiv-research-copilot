import hashlib
import json

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from opensearchpy import OpenSearch

from src.dependencies import (
    get_cache_client,
    get_ollama_client,
    get_opensearch_client,
    get_tracer_service,
)
from src.errors import NotFoundError
from src.schemas.ask import AskRequest, AskResponse
from src.services.cache.redis_client import RedisCache
from src.services.langfuse.tracer import Tracer
from src.services.ollama.client import OllamaClient

router = APIRouter(prefix="/api/v1/ask", tags=["ask"])


def make_cache_key(question: str, top_k: int) -> str:
    raw = json.dumps({"question": question.strip(), "top_k": top_k}, sort_keys=True)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"ask:v1:{digest}"


def build_context(client: OpenSearch, question: str, top_k: int) -> tuple[str, list[dict]]:
    body = {
        "size": top_k,
        "query": {
            "multi_match": {
                "query": question,
                "fields": ["chunk_text^2", "title", "authors"],
                "type": "best_fields",
            }
        },
    }

    resp = client.search(index="paper_chunks_bm25", body=body)
    hits = resp["hits"]["hits"]

    if not hits:
        return "", []

    sources = []
    context_parts = []
    for h in hits:
        s = h["_source"]
        sources.append(
            {
                "paper_id": s["paper_id"],
                "arxiv_id": s["arxiv_id"],
                "title": s["title"],
                "chunk_index": s["chunk_index"],
            }
        )
        context_parts.append(f"[{s['arxiv_id']} - chunk {s['chunk_index']}] {s['chunk_text']}")

    return "\n\n".join(context_parts), sources


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


def _confidence_from_sources(sources: list[dict]) -> float:
    if not sources:
        return 0.0
    score = min(1.0, 0.35 + (0.15 * len(sources)))
    return round(score, 2)


@router.post("", response_model=AskResponse)
def ask(
    request: AskRequest,
    response: Response,
    client: OpenSearch = Depends(get_opensearch_client),
    cache: RedisCache = Depends(get_cache_client),
    ollama: OllamaClient = Depends(get_ollama_client),
    tracer_service: Tracer = Depends(get_tracer_service),
) -> AskResponse:
    trace = tracer_service.start_trace("ask")

    cache_key = make_cache_key(request.question, request.top_k)

    with trace.span("cache_lookup", cache_key=cache_key):
        cached = cache.get_json(cache_key)

    if cached:
        trace.event("cache_hit", cache_key=cache_key)
        elapsed_ms = trace.finish(status="ok", cache="HIT")
        response.headers["X-Trace-Id"] = trace.trace_id
        response.headers["X-Cache"] = "HIT"
        response.headers["X-Latency-Ms"] = str(elapsed_ms)
        cached_sources = cached.get("sources", [])
        return AskResponse(
            answer=cached["answer"],
            sources=cached_sources,
            search_mode=cached.get("search_mode", "chunk_bm25"),
            retrieval_attempts=cached.get("retrieval_attempts", 1),
            confidence=float(cached.get("confidence", _confidence_from_sources(cached_sources))),
            citations=cached.get("citations", _citations_from_sources(cached_sources)),
        )

    trace.event("cache_miss", cache_key=cache_key)

    with trace.span("retrieve_context", top_k=request.top_k):
        context, sources = build_context(client, request.question, request.top_k)

    if not context:
        trace.finish(status="error", reason="no_context")
        raise NotFoundError(
            message="No relevant context found",
            code="CONTEXT_NOT_FOUND",
            context={"route": "ask", "top_k": request.top_k},
        )

    prompt = (
        "You are a research assistant. Answer ONLY from the provided context. "
        "If context is insufficient, say so clearly.\n\n"
        f"Question: {request.question}\n\n"
        f"Context:\n{context}\n\n"
        "Answer:"
    )

    with trace.span("generate_answer"):
        answer = ollama.generate(prompt)

    result = AskResponse(
        answer=answer,
        sources=sources,
        search_mode="chunk_bm25",
        retrieval_attempts=1,
        confidence=_confidence_from_sources(sources),
        citations=_citations_from_sources(sources),
    )

    with trace.span("cache_store", cache_key=cache_key):
        cache.set_json(
            cache_key,
            {
                "answer": result.answer,
                "sources": result.sources,
                "search_mode": result.search_mode,
                "retrieval_attempts": result.retrieval_attempts,
                "confidence": result.confidence,
                "citations": result.citations,
            },
            ttl_seconds=3600,
        )

    elapsed_ms = trace.finish(status="ok", cache="MISS", sources=len(result.sources))
    response.headers["X-Trace-Id"] = trace.trace_id
    response.headers["X-Cache"] = "MISS"
    response.headers["X-Latency-Ms"] = str(elapsed_ms)
    return result


@router.post("/stream")
def stream_ask(
    request: AskRequest,
    client: OpenSearch = Depends(get_opensearch_client),
    ollama: OllamaClient = Depends(get_ollama_client),
    tracer_service: Tracer = Depends(get_tracer_service),
):
    trace = tracer_service.start_trace("ask_stream")

    with trace.span("retrieve_context", top_k=request.top_k):
        context, sources = build_context(client, request.question, request.top_k)

    if not context:
        trace.finish(status="error", reason="no_context")
        raise NotFoundError(
            message="No relevant context found",
            code="CONTEXT_NOT_FOUND",
            context={"route": "ask_stream", "top_k": request.top_k},
        )

    prompt = (
        "You are a research assistant. Answer ONLY from the provided context. "
        "If context is insufficient, say so clearly.\n\n"
        f"Question: {request.question}\n\n"
        f"Context:\n{context}\n\n"
        "Answer:"
    )

    def event_gen():
        yield f"data: {json.dumps({'type': 'trace', 'data': {'trace_id': trace.trace_id}})}\n\n"
        yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"
        with trace.span("stream_generate"):
            for token in ollama.stream_generate(prompt):
                yield f"data: {json.dumps({'type': 'token', 'data': token})}\n\n"
        trace.finish(status="ok", sources=len(sources))
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")
