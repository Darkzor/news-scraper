from __future__ import annotations

import asyncio
from pathlib import Path

from news_scraper_backend.scraper.service import (
    ArticleCandidate,
    PlaywrightScraper,
    discover_article_candidates_from_html,
    discover_article_urls_from_html,
    extract_article_from_html,
)
from news_scraper_backend.scraper.content_quality import ContentQualityService
from news_scraper_backend.scraper.selector_inference import OllamaSelectorError
from news_scraper_backend.scraper.topic_relevance import TopicRelevanceService

FIXTURES = Path(__file__).parent / "fixtures"


class FakeLocator:
    def __init__(
        self,
        *,
        text: str = "",
        content: str | None = None,
        blocks: list[str] | None = None,
    ) -> None:
        self.text = text
        self.content = content
        self.blocks = blocks or []

    @property
    def first(self):
        return self

    async def get_attribute(self, name: str, timeout: int | None = None) -> str | None:
        return self.content if name == "content" else None

    async def inner_text(self, timeout: int | None = None) -> str:
        return self.text

    async def evaluate(self, script: str) -> list[str]:
        return self.blocks


class FakePage:
    def locator(self, selector: str) -> FakeLocator:
        assert selector == "meta[name='description']"
        return FakeLocator(content="A concise article description")


class FakeDiscoveryLocator:
    async def evaluate_all(self, script: str) -> list[str]:
        return ["https://www.example.test/news/alpha", "https://external.test/news/ignored"]


class FakeDiscoveryPage:
    url = "https://www.example.test/"

    def locator(self, selector: str) -> FakeDiscoveryLocator:
        assert selector == "a.article"
        return FakeDiscoveryLocator()

    async def content(self) -> str:
        return ""


class FakeWebsite:
    base_url = "https://example.test/"
    discovery_selector = "a.article"
    target_topics = None


class FakeTopicWebsite:
    base_url = "https://example.test/"
    discovery_selector = "a.article"
    target_topics = "politics, science, AI"


class FakeCandidateDiscoveryLocator:
    async def evaluate_all(self, script: str) -> list[dict[str, str]]:
        return [
            {
                "href": "/news/politics",
                "title": "Parliament approves new budget",
                "description": "Parliament approves new budget after a long debate.",
            },
            {
                "href": "https://external.test/news/ignored",
                "title": "External item",
                "description": "External item",
            },
        ]


class FakeCandidateDiscoveryPage:
    url = "https://example.test/"

    def locator(self, selector: str) -> FakeCandidateDiscoveryLocator:
        assert selector == "a.article"
        return FakeCandidateDiscoveryLocator()

    async def content(self) -> str:
        return ""


class FakeArticlePage:
    def __init__(self, selectors: dict[str, FakeLocator], html: str) -> None:
        self.selectors = selectors
        self.html = html

    def locator(self, selector: str) -> FakeLocator:
        return self.selectors.get(selector, FakeLocator())

    async def content(self) -> str:
        return self.html


class FakeArticleWebsite:
    title_selector = "h1"
    description_selector = "meta[name='description']"
    content_selector = "article"


class FakeOllama:
    def __init__(self, result: dict | None = None, error: Exception | None = None) -> None:
        self.result = result or {"keep_indexes": [], "remove_indexes": []}
        self.error = error

    async def generate_json(self, *, prompt: str, schema: dict) -> dict:
        if self.error:
            raise self.error
        return self.result


class FakeTopicRelevance:
    def __init__(self, result: bool = True, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict[str, str | None]] = []

    async def is_relevant(
        self,
        *,
        url: str,
        title: str,
        description: str,
        target_topics: str | None,
    ) -> bool:
        self.calls.append(
            {
                "url": url,
                "title": title,
                "description": description,
                "target_topics": target_topics,
            }
        )
        if self.error:
            raise self.error
        return self.result


def test_discovers_same_site_article_urls_from_fixture() -> None:
    html = (FIXTURES / "sample_index.html").read_text()
    urls = discover_article_urls_from_html("https://example.test", html)

    assert urls == [
        "https://example.test/news/alpha",
        "https://example.test/news/beta",
    ]


def test_discovers_article_candidates_from_rendered_page_metadata() -> None:
    scraper = PlaywrightScraper(max_articles=20)

    candidates = asyncio.run(scraper._discover_candidates(FakeCandidateDiscoveryPage(), FakeWebsite()))

    assert candidates == [
        ArticleCandidate(
            url="https://example.test/news/politics",
            title="Parliament approves new budget",
            description="Parliament approves new budget after a long debate.",
        )
    ]


def test_discovers_article_candidates_from_html_fixture() -> None:
    html = (FIXTURES / "sample_index.html").read_text()
    candidates = discover_article_candidates_from_html("https://example.test", html)

    assert [candidate.url for candidate in candidates] == [
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


def test_extracts_article_content_without_embedded_related_news() -> None:
    html = (FIXTURES / "article_with_embedded_related.html").read_text()
    article = extract_article_from_html("https://www.digi24.ro/stiri/example", html)

    assert "In Rusia, un barbat a incercat sa se urce" in article.content
    assert "In momentul in care incerca sa fixeze steagul" in article.content
    assert "embed" not in article.content
    assert "Oras intreg terorizat de ursi" not in article.content
    assert "Apa cu portia in Dolj" not in article.content


def test_playwright_selector_text_reads_meta_content_attribute() -> None:
    scraper = PlaywrightScraper()

    text = asyncio.run(scraper._selector_text(FakePage(), "meta[name='description']"))

    assert text == "A concise article description"


def test_discovery_uses_rendered_page_url_after_redirect() -> None:
    scraper = PlaywrightScraper(max_articles=20)

    urls = asyncio.run(scraper._discover_urls(FakeDiscoveryPage(), FakeWebsite()))

    assert urls == ["https://www.example.test/news/alpha"]


def test_topic_relevance_allows_matching_candidates() -> None:
    relevance = FakeTopicRelevance(result=True)
    scraper = PlaywrightScraper(topic_relevance=relevance)
    candidate = ArticleCandidate(
        url="https://example.test/news/ai",
        title="AI lab announces new model",
        description="Researchers released a new model for science workloads.",
    )

    should_crawl = asyncio.run(scraper._should_crawl_candidate(FakeTopicWebsite(), candidate))

    assert should_crawl is True
    assert relevance.calls == [
        {
            "url": "https://example.test/news/ai",
            "title": "AI lab announces new model",
            "description": "Researchers released a new model for science workloads.",
            "target_topics": "politics, science, AI",
        }
    ]


def test_topic_relevance_skips_non_matching_candidates() -> None:
    scraper = PlaywrightScraper(topic_relevance=FakeTopicRelevance(result=False))
    candidate = ArticleCandidate(
        url="https://example.test/sports",
        title="Local team wins final",
        description="The championship ended after extra time.",
    )

    should_crawl = asyncio.run(scraper._should_crawl_candidate(FakeTopicWebsite(), candidate))

    assert should_crawl is False


def test_blank_topics_bypass_qwen_relevance() -> None:
    relevance = FakeTopicRelevance(result=False)
    scraper = PlaywrightScraper(topic_relevance=relevance)
    candidate = ArticleCandidate(
        url="https://example.test/sports",
        title="Local team wins final",
        description="The championship ended after extra time.",
    )

    should_crawl = asyncio.run(scraper._should_crawl_candidate(FakeWebsite(), candidate))

    assert should_crawl is True
    assert relevance.calls == []


def test_missing_topic_relevance_service_fails_closed() -> None:
    scraper = PlaywrightScraper()
    candidate = ArticleCandidate(
        url="https://example.test/sports",
        title="Local team wins final",
        description="The championship ended after extra time.",
    )

    should_crawl = asyncio.run(scraper._should_crawl_candidate(FakeTopicWebsite(), candidate))

    assert should_crawl is False


def test_topic_relevance_errors_fail_closed() -> None:
    scraper = PlaywrightScraper(topic_relevance=FakeTopicRelevance(error=RuntimeError("qwen down")))
    candidate = ArticleCandidate(
        url="https://example.test/news/alpha",
        title="Article",
        description="Summary",
    )

    should_crawl = asyncio.run(scraper._should_crawl_candidate(FakeTopicWebsite(), candidate))

    assert should_crawl is False


def test_topic_relevance_service_accepts_valid_qwen_response() -> None:
    service = TopicRelevanceService(
        ollama=FakeOllama(
            result={
                "is_relevant": True,
                "matched_topics": ["AI"],
                "reason": "The headline is about an AI model.",
            }
        )
    )

    is_relevant = asyncio.run(
        service.is_relevant(
            url="https://example.test/news/ai",
            title="AI lab announces new model",
            description="Researchers released a new model.",
            target_topics="politics, science, AI",
        )
    )

    assert is_relevant is True


def test_topic_relevance_service_rejects_malformed_qwen_response() -> None:
    service = TopicRelevanceService(
        ollama=FakeOllama(result={"is_relevant": "yes", "matched_topics": ["AI"], "reason": "bad"})
    )

    is_relevant = asyncio.run(
        service.is_relevant(
            url="https://example.test/news/ai",
            title="AI lab announces new model",
            description="Researchers released a new model.",
            target_topics="politics, science, AI",
        )
    )

    assert is_relevant is False


def test_content_quality_removes_only_qwen_flagged_blocks() -> None:
    quality = ContentQualityService(
        ollama=FakeOllama(result={"keep_indexes": [0, 2], "remove_indexes": [1]}),
        min_block_chars=1,
    )

    blocks = asyncio.run(
        quality.filter_blocks(
            url="https://example.test/news/alpha",
            title="Tree flag fall",
            description="A man fell while fixing a flag in a tree.",
            blocks=[
                "The man climbed the tree with a flag.",
                "Unrelated headline about local water restrictions.",
                "The top of the tree broke and he fell.",
            ],
        )
    )

    assert blocks == [
        "The man climbed the tree with a flag.",
        "The top of the tree broke and he fell.",
    ]


def test_content_quality_ignores_malformed_qwen_response() -> None:
    quality = ContentQualityService(
        ollama=FakeOllama(result={"keep_indexes": [], "remove_indexes": "bad"}),
        min_block_chars=1,
    )
    original = ["Article paragraph.", "Possibly unrelated paragraph."]

    blocks = asyncio.run(
        quality.filter_blocks(
            url="https://example.test/news/alpha",
            title="Article",
            description="Summary",
            blocks=original,
        )
    )

    assert blocks == original


def test_content_quality_ignores_ollama_failure() -> None:
    quality = ContentQualityService(
        ollama=FakeOllama(error=OllamaSelectorError("invalid qwen json")),
        min_block_chars=1,
    )
    original = ["Article paragraph.", "Related-story widget that should fail open."]

    blocks = asyncio.run(
        quality.filter_blocks(
            url="https://example.test/news/alpha",
            title="Article",
            description="Summary",
            blocks=original,
        )
    )

    assert blocks == original


def test_playwright_extraction_uses_content_quality_for_selector_blocks() -> None:
    scraper = PlaywrightScraper(
        content_quality=ContentQualityService(
            ollama=FakeOllama(result={"keep_indexes": [0, 2], "remove_indexes": [1]}),
            min_block_chars=1,
        )
    )
    page = FakeArticlePage(
        selectors={
            "h1": FakeLocator(text="Tree flag fall"),
            "meta[name='description']": FakeLocator(content="A man fell from a tree."),
            "article": FakeLocator(
                blocks=[
                    "The man climbed the tree with a flag.",
                    "Unrelated headline about local water restrictions.",
                    "The top of the tree broke and he fell.",
                ]
            ),
        },
        html="<article><p>Fallback article paragraph.</p></article>",
    )

    article = asyncio.run(
        scraper._extract_article(
            page,
            "https://example.test/news/alpha",
            FakeArticleWebsite(),
        )
    )

    assert article.content == "The man climbed the tree with a flag. The top of the tree broke and he fell."
