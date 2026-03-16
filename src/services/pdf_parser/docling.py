from io import BytesIO

import httpx
from pypdf import PdfReader

from src.config import settings
from src.schemas.parsed_paper import ParsedDocument, ParsedSection


class DoclingPdfParser:
    """PDF parser using pypdf extraction for manual pipeline."""

    def __init__(self, timeout_seconds: float | None = None, user_agent: str | None = None) -> None:
        parser_cfg = settings.parser
        self.user_agent = user_agent or parser_cfg.user_agent
        self.timeout_seconds = timeout_seconds
        if self.timeout_seconds is None:
            self.timeout_seconds = float(parser_cfg.timeout_seconds)

    def parse_from_url(self, pdf_url: str) -> str:
        try:
            headers = {"User-Agent": self.user_agent}
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                response = client.get(pdf_url, headers=headers)
                response.raise_for_status()
            return self.parse_from_bytes(response.content)
        except Exception as exc:
            print(f"[parse] failed url={pdf_url} error={exc}")
            return ""

    def parse_document(self, pdf_url: str) -> ParsedDocument:
        try:
            headers = {"User-Agent": self.user_agent}
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                response = client.get(pdf_url, headers=headers)
                response.raise_for_status()
            pages = self._extract_pages(response.content)
        except Exception as exc:
            print(f"[parse] failed url={pdf_url} error={exc}")
            return ParsedDocument(
                full_text="",
                sections=[],
                references=[],
                metadata={"provider": "docling", "status": "error", "error": str(exc)},
            )

        sections = [
            ParsedSection(title=f"Page {idx}", text=page_text, order=idx)
            for idx, page_text in enumerate(pages, start=1)
            if page_text
        ]

        full_text = "\n\n".join(section.text for section in sections).strip()
        return ParsedDocument(
            full_text=full_text,
            sections=sections,
            references=[],
            metadata={
                "provider": "docling",
                "status": "ok" if full_text else "empty",
                "page_count": len(sections),
            },
        )

    def parse_from_bytes(self, pdf_bytes: bytes) -> str:
        pages = self._extract_pages(pdf_bytes)
        return "\n\n".join(pages).strip()

    def _extract_pages(self, pdf_bytes: bytes) -> list[str]:
        if not pdf_bytes:
            return []

        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            pages: list[str] = []
            for page in reader.pages:
                text = page.extract_text() or ""
                text = " ".join(text.split()).strip()
                if text:
                    pages.append(text)
            return pages
        except Exception as exc:
            print(f"[parse] failed bytes error={exc}")
            return []
