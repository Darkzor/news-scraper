from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from urllib.parse import urljoin, urlparse

import httpx

SCRIPT_STYLE_RE = re.compile(
    r"<(script|style|noscript|svg)\b[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
WHITESPACE_RE = re.compile(r"\s+")


class SelectorInferenceError(Exception):
    """Base error for selector inference failures."""


class OllamaSelectorError(SelectorInferenceError):
    """Raised when Ollama cannot produce a usable selector response."""


class SelectorValidationError(SelectorInferenceError):
    """Raised when generated selectors do not work on rendered pages."""


@dataclass(frozen=True)
class SelectorSuggestion:
    discovery_selector: str
    title_selector: str
    description_selector: str
    content_selector: str


@dataclass(frozen=True)
class DiscoverySuggestion:
    discovery_selector: str
    sample_article_url: str


DISCOVERY_SCHEMA = {
    "type": "object",
    "properties": {
        "discovery_selector": {"type": "string"},
        "sample_article_url": {"type": "string"},
    },
    "required": ["discovery_selector", "sample_article_url"],
}

ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "title_selector": {"type": "string"},
        "description_selector": {"type": "string"},
        "content_selector": {"type": "string"},
    },
    "required": ["title_selector", "description_selector", "content_selector"],
}


class OllamaSelectorClient:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_ms: int,
        auth_header: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_ms / 1000
        self.auth_header = auth_header
        self.transport = transport

    async def generate_json(self, *, prompt: str, schema: dict) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.auth_header:
            headers["Authorization"] = self.auth_header
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "format": schema,
            "options": {"temperature": 0, "num_predict": 256},
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPStatusError as exc:
            raise OllamaSelectorError(
                f"ollama HTTP {exc.response.status_code} for model {self.model}"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaSelectorError(f"ollama request failed: {exc}") from exc

        raw_response = body.get("response")
        if not isinstance(raw_response, str):
            raise OllamaSelectorError("ollama response did not include JSON text")

        parsed = _parse_json_object(raw_response)
        if not isinstance(parsed, dict):
            raise OllamaSelectorError("ollama JSON response was not an object")
        return parsed


class SelectorInferenceService:
    def __init__(
        self,
        *,
        ollama: OllamaSelectorClient,
        timeout_ms: int,
        max_html_chars: int,
    ) -> None:
        self.ollama = ollama
        self.timeout_ms = timeout_ms
        self.max_html_chars = max_html_chars

    async def suggest_selectors(self, base_url: str) -> SelectorSuggestion:
        from playwright.async_api import async_playwright

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page()
                await page.goto(base_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                index_url = page.url or base_url
                discovery = await self._suggest_discovery(page, index_url)
                discovery = await self._validated_discovery(page, index_url, discovery)

                await page.goto(
                    discovery.sample_article_url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms,
                )
                article_selectors = await self._suggest_article_selectors(page, page.url or discovery.sample_article_url)
                await self._validate_article_selectors(page, article_selectors)
                return SelectorSuggestion(
                    discovery_selector=discovery.discovery_selector,
                    title_selector=article_selectors.title_selector,
                    description_selector=article_selectors.description_selector,
                    content_selector=article_selectors.content_selector,
                )
            finally:
                await browser.close()

    async def _suggest_discovery(self, page, base_url: str) -> DiscoverySuggestion:
        result = await self.ollama.generate_json(
            prompt=(
                "You are configuring a news scraper. Return JSON with CSS selectors only. "
                "Choose a narrow discovery_selector that matches article links on the index page, "
                "and choose one sample_article_url from those article links. "
                "Do not include prose.\n\n"
                f"Base URL: {base_url}\n\n"
                f"Rendered page snapshot:\n{await self._snapshot(page)}"
            ),
            schema=DISCOVERY_SCHEMA,
        )
        return DiscoverySuggestion(
            discovery_selector=_required_selector(result, "discovery_selector"),
            sample_article_url=_required_selector(result, "sample_article_url"),
        )

    async def _suggest_article_selectors(self, page, article_url: str) -> SelectorSuggestion:
        result = await self.ollama.generate_json(
            prompt=(
                "You are configuring a news article extractor. Return JSON with CSS selectors only. "
                "Choose selectors for the article title, article description or summary, and main article body. "
                "Use selectors that match the rendered page and prefer semantic elements. "
                "For metadata descriptions, a selector like meta[name='description'] is allowed. "
                "Do not include prose.\n\n"
                f"Article URL: {article_url}\n\n"
                f"Rendered article snapshot:\n{await self._snapshot(page)}"
            ),
            schema=ARTICLE_SCHEMA,
        )
        return SelectorSuggestion(
            discovery_selector="",
            title_selector=_required_selector(result, "title_selector"),
            description_selector=_required_selector(result, "description_selector"),
            content_selector=_required_selector(result, "content_selector"),
        )

    async def _validated_discovery(
        self,
        page,
        base_url: str,
        discovery: DiscoverySuggestion,
    ) -> DiscoverySuggestion:
        urls = await _selector_urls(page, base_url, discovery.discovery_selector)
        suggested = normalize_url(base_url, discovery.sample_article_url)
        if suggested and _same_host(base_url, suggested):
            if suggested in urls:
                return DiscoverySuggestion(discovery.discovery_selector, suggested)
            repaired_selector = await _repair_discovery_selector(page, base_url, suggested)
            if repaired_selector:
                return DiscoverySuggestion(repaired_selector, suggested)
        if urls:
            return DiscoverySuggestion(discovery.discovery_selector, urls[0])
        raise SelectorValidationError("discovery selector did not find same-site article URLs")

    async def _validate_article_selectors(self, page, selectors: SelectorSuggestion) -> None:
        checks = {
            "title selector": selectors.title_selector,
            "description selector": selectors.description_selector,
            "content selector": selectors.content_selector,
        }
        for label, selector in checks.items():
            text = await selector_text(page, selector)
            if not text:
                raise SelectorValidationError(f"{label} did not extract text")

    async def _snapshot(self, page) -> str:
        html = _compact_html(await page.content(), self.max_html_chars)
        links = await _page_links(page)
        link_lines = [
            f"- text={item.get('text', '')!r} href={item.get('href', '')!r}"
            for item in links[:80]
        ]
        return "\n".join(["Links:", *link_lines, "", "HTML:", html])


async def selector_text(page, selector: str | None) -> str:
    if not selector:
        return ""
    try:
        locator = page.locator(selector).first
        content = await locator.get_attribute("content", timeout=1_000)
        if content:
            return _normalize_text(content)
        text = await locator.inner_text(timeout=1_000)
    except Exception:
        return ""
    return _normalize_text(text)


async def _selector_urls(page, base_url: str, selector: str) -> list[str]:
    try:
        hrefs = await page.locator(selector).evaluate_all(
            "(els) => els.map((el) => el.href || el.getAttribute('href')).filter(Boolean)"
        )
    except Exception:
        return []

    urls: list[str] = []
    seen: set[str] = set()
    for href in hrefs:
        absolute = normalize_url(base_url, href)
        if not absolute or absolute in seen or not _same_host(base_url, absolute):
            continue
        seen.add(absolute)
        urls.append(absolute)
    return urls


async def _repair_discovery_selector(page, base_url: str, sample_article_url: str) -> str:
    for selector in _DISCOVERY_REPAIR_SELECTORS:
        urls = await _selector_urls(page, base_url, selector)
        if sample_article_url in urls:
            return selector
    return ""


async def _page_links(page) -> list[dict[str, str]]:
    try:
        links = await page.locator("a").evaluate_all(
            """(els) => els.map((el) => ({
                text: (el.innerText || el.textContent || '').trim().slice(0, 120),
                href: el.href || el.getAttribute('href') || ''
            })).filter((item) => item.href).slice(0, 120)"""
        )
    except Exception:
        return []
    return links if isinstance(links, list) else []


def _required_selector(result: dict, key: str) -> str:
    value = result.get(key)
    if not isinstance(value, str):
        raise OllamaSelectorError(f"ollama response missing {key}")
    selector = _normalize_text(value)
    if not selector:
        raise OllamaSelectorError(f"ollama response returned blank {key}")
    if len(selector) > 512:
        raise OllamaSelectorError(f"ollama response returned oversized {key}")
    return selector


def _parse_json_object(raw_response: str) -> dict:
    stripped = raw_response.strip()
    if not stripped:
        raise OllamaSelectorError("ollama response was blank")
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = _extract_json_object(stripped)
    if not isinstance(parsed, dict):
        raise OllamaSelectorError("ollama JSON response was not an object")
    return parsed


def _extract_json_object(raw_response: str) -> dict:
    decoder = json.JSONDecoder()
    for start in _json_object_starts(raw_response):
        try:
            parsed, _ = decoder.raw_decode(raw_response[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    raise OllamaSelectorError("ollama response was not valid JSON")


def _json_object_starts(raw_response: str) -> list[int]:
    starts = [index for index, character in enumerate(raw_response) if character == "{"]
    fenced = raw_response.find("```json")
    if fenced >= 0:
        brace = raw_response.find("{", fenced)
        if brace >= 0 and brace in starts:
            starts.remove(brace)
            starts.insert(0, brace)
    return starts


def _compact_html(html: str, max_chars: int) -> str:
    compacted = SCRIPT_STYLE_RE.sub(" ", html)
    compacted = COMMENT_RE.sub(" ", compacted)
    compacted = unescape(WHITESPACE_RE.sub(" ", compacted)).strip()
    return compacted[:max_chars]


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def normalize_url(base_url: str, href: str) -> str | None:
    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return absolute.split("#", 1)[0]


def _same_host(base_url: str, url: str) -> bool:
    return urlparse(base_url).netloc == urlparse(url).netloc


_DISCOVERY_REPAIR_SELECTORS = (
    "article .article-title a",
    ".article-title a",
    "article a[href*='/stiri/']",
    "a[href*='/stiri/']",
    "h1 a, h2 a, h3 a",
    "h2 a",
    "h3 a",
    "article a[href]",
)
