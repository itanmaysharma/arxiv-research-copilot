from opensearchpy import OpenSearch

INDEX_NAME = "paper_chunks_bm25"


def get_client() -> OpenSearch:
    return OpenSearch(
        hosts=[{"host": "localhost", "port": 9200}],
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False,
    )


def main() -> None:
    client = get_client()

    mapping = {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
            }
        },
        "mappings": {
            "properties": {
                "paper_id": {"type": "integer"},
                "chunk_index": {"type": "integer"},
                "chunk_text": {"type": "text"},
                "section_title": {"type": "text"},
                "section_order": {"type": "integer"},
                "arxiv_id": {"type": "keyword"},
                "title": {"type": "text"},
                "authors": {"type": "text"},
                "published_at": {"type": "date"},
            }
        },
    }

    if client.indices.exists(index=INDEX_NAME):
        print(f"Index '{INDEX_NAME}' already exists.")
        return

    client.indices.create(index=INDEX_NAME, body=mapping)
    print(f"Index '{INDEX_NAME}' created.")


if __name__ == "__main__":
    main()
