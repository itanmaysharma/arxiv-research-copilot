from typing import Protocol

from src.config import settings
from src.schemas.parsed_paper import ParsedDocument
from src.services.pdf_parser.docling import DoclingPdfParser


class PdfParser(Protocol):
    def parse_from_url(self, pdf_url: str) -> str:
        """Return parsed text from a PDF URL. Return empty string when text is not extractable."""
        ...

    def parse_document(self, pdf_url: str) -> ParsedDocument:
        """Return structured parsed document for section-aware downstream flow."""
        ...


def make_pdf_parser() -> PdfParser:
    provider = settings.parser.provider.lower().strip()
    if provider == "docling":
        return DoclingPdfParser()

    print(f"[parse] unknown provider={provider}, using docling fallback")
    return DoclingPdfParser()
