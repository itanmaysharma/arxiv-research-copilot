from src.services.arxiv.client import ArxivClient


def main() -> None:
    client = ArxivClient(delay_seconds=0.5)
    papers = client.fetch(query="cat:cs.AI", max_results=3)
    for i, p in enumerate(papers, start=1):
        print(f"{i}. {p.arxiv_id} | {p.title[:80]}")


if __name__ == "__main__":
    main()
