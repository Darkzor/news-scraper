from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from news_scraper_backend.scraper.selector_inference import (
    OllamaSelectorClient,
    OllamaSelectorError,
    DiscoverySuggestion,
    SelectorInferenceService,
    SelectorSuggestion,
    SelectorValidationError,
    _parse_json_object,
    selector_text,
)


class FakeLocator:
    def __init__(
        self,
        *,
        text: str = "",
        content: str | None = None,
        hrefs: list[str] | None = None,
    ) -> None:
        self.text = text
        self.content = content
        self.hrefs = hrefs or []

    @property
    def first(self):
        return self

    async def get_attribute(self, name: str, timeout: int | None = None) -> str | None:
        return self.content if name == "content" else None

    async def inner_text(self, timeout: int | None = None) -> str:
        return self.text

    async def evaluate_all(self, script: str):
        return self.hrefs


class FakePage:
    def __init__(self, selectors: dict[str, FakeLocator], html: str = "") -> None:
        self.selectors = selectors
        self.html = html

    def locator(self, selector: str) -> FakeLocator:
        return self.selectors.get(selector, FakeLocator())

    async def content(self) -> str:
        return self.html


class FakeOllama:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = responses

    async def generate_json(self, *, prompt: str, schema: dict) -> dict:
        return self.responses.pop(0)


def run(coro):
    return asyncio.run(coro)


def ollama_client(transport: httpx.MockTransport) -> OllamaSelectorClient:
    return OllamaSelectorClient(
        base_url="http://ollama.test:11434",
        model="qwen-test",
        timeout_ms=1000,
        transport=transport,
    )


def test_ollama_client_returns_json_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == "qwen-test"
        assert payload["stream"] is False
        assert payload["think"] is False
        assert payload["options"]["num_predict"] == 256
        return httpx.Response(200, json={"response": "{\"title_selector\":\"h1\"}"})

    result = run(
        ollama_client(httpx.MockTransport(handler)).generate_json(
            prompt="Return JSON",
            schema={"type": "object"},
        )
    )

    assert result == {"title_selector": "h1"}


def test_ollama_client_parses_json_wrapped_in_prose() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"response": "Here is the JSON:\\n```json\\n{\"title_selector\":\"h1\"}\\n```"},
        )

    result = run(
        ollama_client(httpx.MockTransport(handler)).generate_json(
            prompt="Return JSON",
            schema={"type": "object"},
        )
    )

    assert result == {"title_selector": "h1"}


def test_ollama_client_rejects_invalid_json_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "not json"})

    with pytest.raises(OllamaSelectorError, match="not valid JSON"):
        run(ollama_client(httpx.MockTransport(handler)).generate_json(prompt="x", schema={}))


def test_ollama_client_rejects_blank_json_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": ""})

    with pytest.raises(OllamaSelectorError, match="blank"):
        run(ollama_client(httpx.MockTransport(handler)).generate_json(prompt="x", schema={}))


def test_parse_json_object_skips_invalid_braces_before_valid_object() -> None:
    assert _parse_json_object("not json {broken then {\"title_selector\":\"h1\"}") == {
        "title_selector": "h1"
    }


def test_ollama_client_reports_model_missing_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "model not found"})

    with pytest.raises(OllamaSelectorError, match="ollama HTTP 404"):
        run(ollama_client(httpx.MockTransport(handler)).generate_json(prompt="x", schema={}))


def test_ollama_client_reports_connection_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("unreachable", request=request)

    with pytest.raises(OllamaSelectorError, match="ollama request failed"):
        run(ollama_client(httpx.MockTransport(handler)).generate_json(prompt="x", schema={}))


def test_selector_text_reads_meta_content_attribute_before_inner_text() -> None:
    page = FakePage({"meta[name='description']": FakeLocator(content=" Meta summary ")})

    assert run(selector_text(page, "meta[name='description']")) == "Meta summary"


def test_selector_inference_validates_qwen_selectors_against_fake_pages() -> None:
    index_page = FakePage(
        {
            "main a.article-link": FakeLocator(
                hrefs=["https://example.test/news/alpha", "https://external.test/ignored"]
            ),
        },
        html="<main><a class='article-link' href='/news/alpha'>Alpha</a></main>",
    )
    article_page = FakePage(
        {
            "h1": FakeLocator(text="Article title"),
            "meta[name='description']": FakeLocator(content="Article summary"),
            "article": FakeLocator(text="Article body long enough for extraction"),
        },
        html="<article><h1>Article title</h1><p>Article body</p></article>",
    )
    service = SelectorInferenceService(
        ollama=FakeOllama(
            [
                {
                    "discovery_selector": "main a.article-link",
                    "sample_article_url": "https://example.test/news/alpha",
                },
                {
                    "title_selector": "h1",
                    "description_selector": "meta[name='description']",
                    "content_selector": "article",
                },
            ]
        ),
        timeout_ms=1000,
        max_html_chars=1000,
    )

    discovery = run(service._suggest_discovery(index_page, "https://example.test"))
    validated_discovery = run(service._validated_discovery(index_page, "https://example.test", discovery))
    assert validated_discovery.discovery_selector == "main a.article-link"
    assert validated_discovery.sample_article_url == "https://example.test/news/alpha"
    article_selectors = run(service._suggest_article_selectors(article_page, "https://example.test/news/alpha"))
    run(service._validate_article_selectors(article_page, article_selectors))

    assert SelectorSuggestion(
        discovery_selector=discovery.discovery_selector,
        title_selector=article_selectors.title_selector,
        description_selector=article_selectors.description_selector,
        content_selector=article_selectors.content_selector,
    ) == SelectorSuggestion(
        discovery_selector="main a.article-link",
        title_selector="h1",
        description_selector="meta[name='description']",
        content_selector="article",
    )


def test_selector_inference_repairs_invalid_discovery_selector_from_sample_url() -> None:
    page = FakePage(
        {
            "article.article-alt a.article-title": FakeLocator(hrefs=[]),
            "article .article-title a": FakeLocator(
                hrefs=["https://www.example.test/news/alpha"]
            ),
        }
    )
    service = SelectorInferenceService(
        ollama=FakeOllama([]),
        timeout_ms=1000,
        max_html_chars=1000,
    )

    discovery = run(
        service._validated_discovery(
            page,
            "https://www.example.test/",
            discovery=DiscoverySuggestion(
                discovery_selector="article.article-alt a.article-title",
                sample_article_url="https://www.example.test/news/alpha",
            ),
        )
    )

    assert discovery.discovery_selector == "article .article-title a"
    assert discovery.sample_article_url == "https://www.example.test/news/alpha"


def test_selector_inference_rejects_selectors_without_text() -> None:
    service = SelectorInferenceService(
        ollama=FakeOllama([]),
        timeout_ms=1000,
        max_html_chars=1000,
    )
    page = FakePage({"h1": FakeLocator(text="")})

    with pytest.raises(SelectorValidationError, match="title selector"):
        run(
            service._validate_article_selectors(
                page,
                SelectorSuggestion(
                    discovery_selector="a",
                    title_selector="h1",
                    description_selector="meta[name='description']",
                    content_selector="article",
                ),
            )
        )
