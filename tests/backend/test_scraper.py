from __future__ import annotations

import asyncio
from pathlib import Path

from news_scraper_backend.scraper.service import (
    PlaywrightScraper,
    discover_article_urls_from_html,
    extract_article_from_html,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeLocator:
    @property
    def first(self):
        return self

    async def get_attribute(self, name: str, timeout: int | None = None) -> str | None:
        return "A concise article description" if name == "content" else None

    async def inner_text(self, timeout: int | None = None) -> str:
        return ""


class FakePage:
    def locator(self, selector: str) -> FakeLocator:
        assert selector == "meta[name='description']"
        return FakeLocator()


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


def test_playwright_selector_text_reads_meta_content_attribute() -> None:
    scraper = PlaywrightScraper()

    text = asyncio.run(scraper._selector_text(FakePage(), "meta[name='description']"))

    assert text == "A concise article description"
