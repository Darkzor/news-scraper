from __future__ import annotations

from pathlib import Path

from news_scraper_backend.scraper.service import (
    discover_article_urls_from_html,
    extract_article_from_html,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_discovers_same_site_article_urls_from_fixture() -> None:
    html = (FIXTURES / "sample_index.html").read_text()
    urls = discover_article_urls_from_html("https://example.test", html)

    assert urls == [
        "https://example.test/news/alpha",
        "https://example.test/news/beta",
    ]


def test_extracts_title_description_and_content_from_fixture() -> None:
    html = (FIXTURES / "sample_article.html").read_text()
    article = extract_article_from_html("https://example.test/news/alpha", html)

    assert article.title == "Sample Article Title"
    assert article.description == "A concise article description"
    assert "First paragraph of the controlled fixture" in article.content
    assert "Second paragraph with rendered text" in article.content
