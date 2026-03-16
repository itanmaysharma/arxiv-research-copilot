from unittest.mock import MagicMock, patch

from src.services.arxiv.client import ArxivClient


SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2603.12345v1</id>
    <title>  Sample   Title  </title>
    <summary>  Sample   abstract text. </summary>
    <author><name>Alice</name></author>
    <author><name>Bob</name></author>
    <published>2026-03-09T00:00:00Z</published>
    <link title="pdf" href="https://arxiv.org/pdf/2603.12345v1" />
  </entry>
</feed>
"""


def test_parse_feed_extracts_expected_fields():
    client = ArxivClient(delay_seconds=0)
    papers = client._parse_feed(SAMPLE_FEED)

    assert len(papers) == 1
    p = papers[0]
    assert p.arxiv_id == "2603.12345v1"
    assert p.title == "Sample Title"
    assert p.abstract == "Sample abstract text."
    assert p.authors == "Alice, Bob"
    assert p.pdf_url == "https://arxiv.org/pdf/2603.12345v1"
    assert p.published_at == "2026-03-09T00:00:00Z"


def test_fetch_uses_http_and_returns_parsed_papers():
    mock_response = MagicMock()
    mock_response.text = SAMPLE_FEED
    mock_response.raise_for_status.return_value = None

    mock_http_client = MagicMock()
    mock_http_client.get.return_value = mock_response
    mock_http_client.__enter__.return_value = mock_http_client
    mock_http_client.__exit__.return_value = False

    with patch("src.services.arxiv.client.httpx.Client", return_value=mock_http_client), patch(
        "src.services.arxiv.client.time.sleep"
    ) as mock_sleep:
        client = ArxivClient(delay_seconds=0.5)
        papers = client.fetch(query="cat:cs.AI", max_results=2)

    assert len(papers) == 1
    assert papers[0].arxiv_id == "2603.12345v1"
    mock_http_client.get.assert_called_once()
    mock_sleep.assert_called_once_with(0.5)
