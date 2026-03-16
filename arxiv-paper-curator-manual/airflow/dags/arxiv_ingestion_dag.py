from datetime import datetime, timedelta

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator


def _post_stage(path: str) -> None:
    url = f"http://api:8000{path}"
    print(f"[ingestion_dag] calling stage endpoint: {url}")
    resp = requests.post(url, timeout=180)
    resp.raise_for_status()
    payload = resp.json()
    print(f"[ingestion_dag] stage result: {payload}")


def stage_fetch_store() -> None:
    _post_stage("/api/v1/papers/ingest/fetch-store?max_results=5")


def stage_parse() -> None:
    _post_stage("/api/v1/papers/ingest/parse?limit=20")


def stage_chunk() -> None:
    _post_stage("/api/v1/papers/ingest/chunk?limit=20")


def stage_index() -> None:
    _post_stage("/api/v1/papers/ingest/index")


with DAG(
    dag_id="arxiv_ingestion_dag",
    start_date=datetime(2026, 3, 1),
    schedule="0 9 * * *",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=2)},
    tags=["arxiv", "ingestion"],
) as dag:
    fetch_store = PythonOperator(
        task_id="fetch_and_store_metadata",
        python_callable=stage_fetch_store,
    )

    parse_pdf = PythonOperator(
        task_id="parse_full_text",
        python_callable=stage_parse,
    )

    chunk_text = PythonOperator(
        task_id="chunk_papers",
        python_callable=stage_chunk,
    )

    index_search = PythonOperator(
        task_id="index_search_layers",
        python_callable=stage_index,
    )

    fetch_store >> parse_pdf >> chunk_text >> index_search
