from src.services.arxiv.client import ArxivClient, ArxivPaper


class ArxivMetadataFetcher:
    def __init__(self, delay_seconds: float = 0.5) -> None:
        self.client = ArxivClient(delay_seconds=delay_seconds)

    def fetch_latest_cs_ai(self, max_results: int = 5) -> list[ArxivPaper]:
        return self.client.fetch(query="cat:cs.AI", max_results=max_results)
