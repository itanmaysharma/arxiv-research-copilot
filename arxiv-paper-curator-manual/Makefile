.PHONY: start stop restart status logs health setup lint test clean

setup:
	uv sync

start:
	docker compose up --build -d

stop:
	docker compose down

restart:
	docker compose down && docker compose up --build -d

status:
	docker compose ps

logs:
	docker compose logs -f --tail=200

health:
	curl -s http://localhost:8000/health; echo
	curl -s http://localhost:9200 >/dev/null && echo "opensearch: ok"
	curl -s http://localhost:11434/api/tags >/dev/null && echo "ollama: ok"
	docker compose exec -T redis redis-cli ping
	curl -s -o /dev/null -w "airflow: %{http_code}\n" http://localhost:8080
	curl -s -o /dev/null -w "dashboards: %{http_code}\n" http://localhost:5601

lint:
	uv run ruff check .

test:
	uv run pytest -q

clean:
	docker compose down -v
