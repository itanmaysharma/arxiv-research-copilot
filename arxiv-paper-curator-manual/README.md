# arxiv-paper-curator-manual

Manual, progressive implementation of an agentic RAG system for arXiv papers.

## What this project does
- Ingests latest arXiv metadata (and prepares parse/chunk/index pipeline stages)
- Stores data in Postgres
- Indexes data into OpenSearch (BM25 + vector layer)
- Supports retrieval APIs (`search`, `chunk-search`, `hybrid-search`)
- Supports answer APIs (`ask`, `ask/stream`, `agentic-ask`)
- Uses Redis cache for fast repeated ask responses
- Uses Airflow DAG for scheduled staged ingestion
- Provides Gradio UI for easy manual testing

## Tech stack
- FastAPI
- Postgres
- OpenSearch + OpenSearch Dashboards
- Airflow 3 (api-server, scheduler, dag-processor)
- Redis
- Ollama
- Gradio

## Prerequisites
- Docker + Docker Compose
- `uv` installed locally
- macOS/Linux shell

## 1. Setup
```bash
cd /Users/sharma/Github/archive-curator/arxiv-paper-curator-manual
cp .env.example .env
uv sync
```

Optional semantic retrieval key:
- Set `JINA_API_KEY` in `.env` for real embeddings quality.

## 2. Start services
```bash
make start
```

Check status:
```bash
make status
make health
```

Expected health signals:
- API health JSON returns `ok`
- OpenSearch `ok`
- Ollama `ok`
- Redis `PONG`
- Airflow HTTP `200`
- Dashboards HTTP `302`

## 3. Core API smoke tests
### API root and health
```bash
curl -s http://localhost:8000/
curl -s http://localhost:8000/health
```

### Papers list
```bash
curl -s http://localhost:8000/api/v1/papers
```

### Staged ingestion (new architecture)
```bash
curl -s -X POST "http://localhost:8000/api/v1/papers/ingest/fetch-store?max_results=3"
curl -s -X POST "http://localhost:8000/api/v1/papers/ingest/parse?limit=10"
curl -s -X POST "http://localhost:8000/api/v1/papers/ingest/chunk?limit=10"
curl -s -X POST "http://localhost:8000/api/v1/papers/ingest/index"
```

Or full pipeline in one call:
```bash
curl -s -X POST "http://localhost:8000/api/v1/papers/ingest/pipeline?max_results=3"
```

### Search APIs
```bash
curl -s -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"reasoning","size":3}'

curl -s -X POST "http://localhost:8000/api/v1/chunk-search" \
  -H "Content-Type: application/json" \
  -d '{"query":"preference vectors","size":3}'

curl -s -X POST "http://localhost:8000/api/v1/hybrid-search" \
  -H "Content-Type: application/json" \
  -d '{"query":"trustworthy personalized explanations","size":3}'
```

### Ask APIs
```bash
curl -s -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What does PONTE optimize for?","top_k":3}'

curl -N -X POST "http://localhost:8000/api/v1/ask/stream" \
  -H "Content-Type: application/json" \
  -d '{"question":"What does PONTE optimize for?","top_k":3}'
```

### Agentic ask
```bash
curl -s -X POST "http://localhost:8000/api/v1/agentic-ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What does PONTE optimize for?","top_k":3}'
```

## 4. Airflow verification
- Open http://localhost:8080
- Find DAG: `arxiv_ingestion_dag`
- Trigger run
- Confirm tasks succeed in order:
  - `fetch_and_store_metadata`
  - `parse_full_text`
  - `chunk_papers`
  - `index_search_layers`

## 5. Gradio UI
Start UI:
```bash
uv run python gradio_launcher.py
```
Open:
- http://localhost:7860

Tabs:
- Ask
- Ask Stream
- Hybrid Search
- Agentic Ask

## Useful commands
```bash
make logs
make test
make lint
make stop
make clean
```

## Project docs
- Architecture: [docs/architecture.md](docs/architecture.md)
- Runbook: [docs/runbook.md](docs/runbook.md)
- Retrospectives: `docs/retrospectives/`
- Parity worklog (simple): `PARITY_WORKLOG_SIMPLE.md`

## Notes
- Keep `.env` local and uncommitted.
- This repo preserves part-by-part progression docs and parity worklog.
