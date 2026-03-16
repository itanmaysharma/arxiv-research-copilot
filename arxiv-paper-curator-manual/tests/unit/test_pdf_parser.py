from src.services.pdf_parser.docling import DoclingPdfParser


def test_parse_from_bytes_extracts_text(monkeypatch):
    class FakePage:
        def extract_text(self):
            return "Hello\n\nRAG World"

    class FakeReader:
        def __init__(self, _stream):
            self.pages = [FakePage()]

    monkeypatch.setattr("src.services.pdf_parser.docling.PdfReader", FakeReader)

    parser = DoclingPdfParser(timeout_seconds=5)
    text = parser.parse_from_bytes(b"%PDF-fake")

    assert text == "Hello RAG World"


def test_parse_from_url_returns_empty_on_http_error(monkeypatch):
    class FailingClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, _url, headers=None):
            raise RuntimeError("network down")

    monkeypatch.setattr("src.services.pdf_parser.docling.httpx.Client", lambda **_kwargs: FailingClient())

    parser = DoclingPdfParser(timeout_seconds=5)
    text = parser.parse_from_url("https://arxiv.org/pdf/fake.pdf")

    assert text == ""


def test_parse_document_returns_sections(monkeypatch):
    class FakePage:
        def __init__(self, text):
            self._text = text

        def extract_text(self):
            return self._text

    class FakeReader:
        def __init__(self, _stream):
            self.pages = [FakePage("Intro text"), FakePage("Method text")]

    class FakeResponse:
        content = b"%PDF-fake"

        @staticmethod
        def raise_for_status():
            return None

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, _url, headers=None):
            return FakeResponse()

    monkeypatch.setattr("src.services.pdf_parser.docling.PdfReader", FakeReader)
    monkeypatch.setattr("src.services.pdf_parser.docling.httpx.Client", lambda **_kwargs: FakeClient())

    parser = DoclingPdfParser(timeout_seconds=5)
    document = parser.parse_document("https://arxiv.org/pdf/fake.pdf")

    assert document.metadata["status"] == "ok"
    assert len(document.sections) == 2
    assert document.sections[0].title == "Page 1"
