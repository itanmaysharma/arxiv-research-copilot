# Architecture

## High-level components
- API service (`FastAPI`): main entrypoint for ingestion, search, ask, and agentic ask.
- Postgres: source of truth for papers and chunks.
- OpenSearch:
  - `papers_bm25` for paper-level keyword search
  - `paper_chunks_bm25` for chunk-level keyword retrieval
  - `paper_chunks_vector` for semantic vector retrieval
- Ollama: answer generation model backend.
- Redis: ask-response cache.
- Airflow: scheduled staged ingestion orchestration.
- Gradio: user-facing manual testing UI.

## System boundaries
- Source boundary:
  - arXiv metadata/PDF fetch from external network.
- Persistence boundary:
  - Postgres is source-of-truth for paper/chunk records and feedback.
- Retrieval boundary:
  - OpenSearch stores serving indexes (BM25 + vector) derived from Postgres.
- Generation boundary:
  - Ollama provides model generation only; no source-of-truth state.
- Cache boundary:
  - Redis stores short-lived ask response cache.
- Telemetry boundary:
  - Langfuse integration is optional and config-gated.

## Data model
- `papers`
  - metadata, `full_text`, parser metadata JSON
- `paper_chunks`
  - per-paper text chunks with offsets + optional section metadata
- `feedback`
  - `trace_id`, score, comment, channel, timestamp

## Ingestion architecture (staged)
Stages are now explicit and separately callable:
1. `fetch-store`
- fetch latest arXiv metadata
- upsert paper rows

2. `parse`
- parse full text from PDF URL (real parser layer)
- build structured parse output (`sections`, `references`, parser metadata)
- fallback to abstract when parse unavailable

3. `chunk`
- create overlapping chunks from full_text/abstract
- prefer section-aware chunking when parse metadata has sections
- replace prior chunks for each processed paper

4. `index`
- reindex paper BM25
- reindex chunk BM25
- reindex chunk vector embeddings

Pipeline endpoint:
- `POST /api/v1/papers/ingest/pipeline`

Stage endpoints:
- `POST /api/v1/papers/ingest/fetch-store`
- `POST /api/v1/papers/ingest/parse`
- `POST /api/v1/papers/ingest/chunk`
- `POST /api/v1/papers/ingest/index`

## Retrieval architecture
- `search`: BM25 over paper documents
- `chunk-search`: BM25 over chunks
- `hybrid-search`:
  - keyword chunk retrieval (BM25)
  - vector chunk retrieval (kNN)
  - RRF fusion to combine both

## Answering architecture
- `ask`:
  - retrieve relevant chunks
  - generate answer with grounded context
  - cache response in Redis
  - return trace headers and latency

- `ask/stream`:
  - same retrieval
  - SSE token streaming from generation backend

- `agentic-ask`:
  - guardrail check
  - out-of-scope check
  - retrieve (rewrite + retry when needed)
  - document grading
  - generation
  - returns explicit `steps`

## Tracing and observability
- typed trace sessions for ask and agentic flows
- span-level timing printed as structured logs
- optional real Langfuse trace/span/event updates
- `X-Trace-Id` and latency headers on responses
- tracing can be disabled by config (`TRACING_ENABLED=false`)
- feedback endpoint stores DB records and can forward scores to Langfuse by `trace_id`

## Error handling model
- Domain errors use typed exception taxonomy:
  - `BadRequestError`, `NotFoundError`, `ConflictError`, `StorageError`
- FastAPI global handlers map typed exceptions to consistent payload:
  - `detail`
  - `error.code`
  - `error.message`
  - `error.context`
- Unknown exceptions map to `INTERNAL_ERROR` with 500 status.

## Runtime hardening
- Docker compose healthchecks for critical services
- restart policies for long-running containers
- dependency conditions for readiness-driven startup
- explicit shared bridge network

## Failure domains and recovery strategy
- Ingestion failures:
  - localized per stage; parse failures are isolated per paper.
- Indexing failures:
  - vector indexing failure does not block BM25 indexing.
- Generation failures:
  - ask/agentic paths fail request but do not corrupt state.
- Telemetry failures:
  - Langfuse failures are non-fatal; core API flow continues.
- Cache failures:
  - cache miss path still serves full ask response.
