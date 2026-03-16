# Runbook

## 1. Scope
This runbook is for local/dev operations of:
- API (`FastAPI`)
- Postgres
- OpenSearch + Dashboards
- Redis
- Ollama
- Airflow (webserver/scheduler/dag-processor)
- Optional Telegram bot lifecycle (config-gated)

Primary goals:
- restore service quickly
- verify data pipeline correctness
- isolate root cause when ingestion/search/ask fails

## 2. Fast command reference
```bash
cd <repo-root>
make start
make health
make status
make logs
make stop
make clean   # destructive (drops volumes)
```

## 3. Daily operations
### Startup
```bash
make start
make health
```

Expected `make health` signals:
- API health returns `status: ok`
- OpenSearch reachable
- Ollama reachable
- Redis returns `PONG`
- Airflow HTTP `200`
- Dashboards HTTP `302`

### Shutdown
```bash
make stop
```

### Full reset (destructive)
```bash
make clean
make start
```

## 4. Data pipeline verification
### Stage-by-stage verification
```bash
curl -s -X POST "http://localhost:8000/api/v1/papers/ingest/fetch-store?max_results=3"
curl -s -X POST "http://localhost:8000/api/v1/papers/ingest/parse?limit=10"
curl -s -X POST "http://localhost:8000/api/v1/papers/ingest/chunk?limit=10"
curl -s -X POST "http://localhost:8000/api/v1/papers/ingest/index"
```

Check parse/chunk quality hints:
- `parse.parsed` should be > 0 for valid PDFs
- `parse.parse_failures` should stay low
- `chunk.section_aware_papers` should increase when section metadata exists

### One-shot pipeline verification
```bash
curl -s -X POST "http://localhost:8000/api/v1/papers/ingest/pipeline?max_results=3"
```

### DB and index count verification
```bash
docker compose exec postgres psql -U arxiv -d arxiv_curator -c "SELECT COUNT(*) FROM papers;"
docker compose exec postgres psql -U arxiv -d arxiv_curator -c "SELECT COUNT(*) FROM paper_chunks;"
curl -s "http://localhost:9200/papers_bm25/_count"
curl -s "http://localhost:9200/paper_chunks_bm25/_count"
curl -s "http://localhost:9200/paper_chunks_vector/_count"
```

## 5. API behavior verification
### Ask
```bash
curl -i -s -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What does PONTE optimize for?","top_k":3}'
```

Validate headers:
- `x-trace-id`
- `x-cache`
- `x-latency-ms`

### Agentic ask
```bash
curl -s -X POST "http://localhost:8000/api/v1/agentic-ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Who won yesterday football match?","top_k":3}'
```

Expected:
- out-of-scope question should return blocked scope step.

### Error schema contract
Typed API errors should include:
- `detail`
- `error.code`
- `error.message`
- `error.context`

## 6. Airflow operations
### UI check
1. Open [http://localhost:8080](http://localhost:8080)
2. Open DAG `arxiv_ingestion_dag`
3. Trigger run
4. Verify task order success:
- `fetch_and_store_metadata`
- `parse_full_text`
- `chunk_papers`
- `index_search_layers`

### CLI/log check
```bash
docker compose ps
docker compose logs --tail=200 airflow-scheduler
docker compose logs --tail=200 airflow-dag-processor
```

## 7. Incident playbooks
### Incident A: API serving old code
Symptoms:
- endpoint behavior does not match recent code edits.

Actions:
```bash
docker compose up --build -d api
docker compose logs --tail=120 api
```

### Incident B: Parse stage returns mostly fallback
Symptoms:
- `fallback_to_abstract` high, `parsed` low.

Actions:
1. Confirm outbound PDF fetch works.
2. Check parse logs:
```bash
docker compose logs --tail=200 api | grep -i "\[parse\]"
```
3. Re-run parse stage on small limit for debugging.

### Incident C: Section-aware chunking not applied
Symptoms:
- `section_aware_papers` remains 0 despite parse success.

Actions:
1. Verify paper metadata exists:
```bash
docker compose exec postgres psql -U arxiv -d arxiv_curator -c \
"SELECT id, arxiv_id, LEFT(parser_metadata_json, 120) FROM papers ORDER BY id DESC LIMIT 5;"
```
2. Re-run chunk stage:
```bash
curl -s -X POST "http://localhost:8000/api/v1/papers/ingest/chunk?limit=20"
```

### Incident D: Hybrid search has no vector contribution
Symptoms:
- hybrid results always BM25-only.

Actions:
1. Ensure `JINA_API_KEY` configured.
2. Recreate/reindex vector layer:
```bash
PYTHONPATH=. uv run python scripts/opensearch/init_vector_index.py
DATABASE_URL=postgresql+psycopg://arxiv:arxivpass@localhost:5432/arxiv_curator PYTHONPATH=. uv run python scripts/opensearch/index_embeddings.py
```
3. Re-test `/api/v1/hybrid-search`.

### Incident E: Ask cache not hitting
Symptoms:
- repeated ask calls still slow and `x-cache: MISS`.

Actions:
```bash
docker compose exec -T redis redis-cli ping
docker compose exec -T redis redis-cli --scan --pattern "ask:v1:*" | head
docker compose logs --tail=120 api | grep "\[ask\] cache_"
```

### Incident F: Feedback not reaching Langfuse
Symptoms:
- feedback stored in DB but not visible in Langfuse.

Actions:
1. Verify env keys:
- `TRACING_ENABLED=true`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- optional `LANGFUSE_HOST`
2. Check API logs:
```bash
docker compose logs --tail=200 api | grep -i "langfuse\\|feedback"
```

## 8. Schema migration helper (local DBs)
If your DB was created before parsed-metadata columns were added:
```bash
PYTHONPATH=. uv run python scripts/migrations/add_part3_c2_columns.py
```

## 9. Gradio operations
```bash
uv run python gradio_launcher.py
```
Open [http://localhost:7860](http://localhost:7860)

## 10. Quality gates
```bash
make lint
make test
```

CI runs same checks on `push`/`pull_request` in `.github/workflows/ci.yml`.
