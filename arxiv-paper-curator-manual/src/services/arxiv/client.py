import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import httpx

from src.config import settings


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    abstract: str
    authors: str
    pdf_url: str
    published_at: str


class ArxivClient:
    def __init__(self, delay_seconds: float = 1.0, timeout_seconds: float = 20.0) -> None:
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds

    def fetch(self, query: str, max_results: int = 5) -> list[ArxivPaper]:
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            resp = client.get(settings.arxiv.api_url, params=params)
            resp.raise_for_status()

        time.sleep(self.delay_seconds)
        return self._parse_feed(resp.text)

    def _parse_feed(self, xml_text: str) -> list[ArxivPaper]:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(xml_text)
        papers: list[ArxivPaper] = []

        for entry in root.findall("atom:entry", ns):
            entry_id = (entry.findtext("atom:id", default="", namespaces=ns) or "").strip()
            arxiv_id = entry_id.rsplit("/", 1)[-1] if entry_id else ""

            title = " ".join(
                (entry.findtext("atom:title", default="", namespaces=ns) or "").split()
            ).strip()
            abstract = " ".join(
                (entry.findtext("atom:summary", default="", namespaces=ns) or "").split()
            ).strip()

            author_nodes = entry.findall("atom:author", ns)
            authors = ", ".join(
                (a.findtext("atom:name", default="", namespaces=ns) or "").strip()
                for a in author_nodes
                if (a.findtext("atom:name", default="", namespaces=ns) or "").strip()
            )

            published_at = (entry.findtext("atom:published", default="", namespaces=ns) or "").strip()

            pdf_url = ""
            for link in entry.findall("atom:link", ns):
                if link.attrib.get("title") == "pdf":
                    pdf_url = link.attrib.get("href", "").strip()
                    break
            if not pdf_url and arxiv_id:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            if arxiv_id and title and abstract:
                papers.append(
                    ArxivPaper(
                        arxiv_id=arxiv_id,
                        title=title,
                        abstract=abstract,
                        authors=authors,
                        pdf_url=pdf_url,
                        published_at=published_at,
                    )
                )

        return papers
