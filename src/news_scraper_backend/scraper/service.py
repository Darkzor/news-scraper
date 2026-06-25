from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from html import unescape
from urllib.parse import urljoin, urlparse

from sqlalchemy.orm import Session

from news_scraper_backend.scraper.content_quality import ContentQualityService
from news_scraper_backend.scraper.selector_inference import selector_text
from news_scraper_backend.scraper.topic_relevance import TopicRelevanceService
from news_scraper_backend.storage import models, repository

logger = logging.getLogger("news_scraper.scrape_jobs")

TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
META_DESCRIPTION_RE = re.compile(
    r"<meta\b(?=[^>]*(?:name|property)=['\"](?:description|og:description)['\"])[^>]*content=['\"]([^'\"]*)['\"][^>]*>",
    re.IGNORECASE | re.DOTALL,
)
A_RE = re.compile(r"<a\b[^>]*href=['\"]([^'\"]+)['\"][^>]*>", re.IGNORECASE)
BLOCK_TAGS = {"p", "li", "blockquote", "h2", "h3", "h4"}
UNWANTED_TAGS = {"script", "style", "noscript", "svg", "iframe", "aside", "nav"}
UNWANTED_ATTR_PATTERNS = (
    "ad-container",
    "advert",
    "also-read",
    "embed",
    "newsletter",
    "promo",
    "read-more",
    "recomand",
    "recommended",
    "related",
    "share",
    "social",
)
CONTENT_BLOCK_EXTRACTION_SCRIPT = """
(root) => {
  const clone = root.cloneNode(true);
  const unwantedSelector = [
    "script",
    "style",
    "noscript",
    "svg",
    "iframe",
    "aside",
    "nav",
    "[hidden]",
    "[aria-hidden='true']",
    "[class*='ad-container' i]",
    "[class*='advert' i]",
    "[class*='also-read' i]",
    "[class*='embed' i]",
    "[class*='newsletter' i]",
    "[class*='promo' i]",
    "[class*='read-more' i]",
    "[class*='recomand' i]",
    "[class*='recommended' i]",
    "[class*='related' i]",
    "[class*='share' i]",
    "[class*='social' i]",
    "[id*='ad-container' i]",
    "[id*='advert' i]",
    "[id*='also-read' i]",
    "[id*='embed' i]",
    "[id*='newsletter' i]",
    "[id*='promo' i]",
    "[id*='read-more' i]",
    "[id*='recomand' i]",
    "[id*='recommended' i]",
    "[id*='related' i]",
    "[id*='share' i]",
    "[id*='social' i]",
    "[aria-label*='advert' i]",
    "[aria-label*='related' i]",
    "[aria-label*='recommended' i]",
    "[data-module*='related' i]",
    "[data-testid*='related' i]"
  ].join(",");
  clone.querySelectorAll(unwantedSelector).forEach((el) => el.remove());
  const normalize = (value) => (value || "").replace(/\\s+/g, " ").trim();
  const blocks = Array.from(clone.querySelectorAll("p, li, blockquote, h2, h3, h4"))
    .map((el) => normalize(el.innerText || el.textContent))
    .filter(Boolean);
  if (blocks.length) {
    return blocks;
  }
  return normalize(clone.innerText || clone.textContent)
    .split(/\\n+/)
    .map(normalize)
    .filter(Boolean);
}
"""
DISCOVERY_CANDIDATE_SCRIPT = """
(els) => {
  const normalize = (value) => (value || "").replace(/\\s+/g, " ").trim();
  const parentSelector = [
    "article",
    "li",
    "[class*='article' i]",
    "[class*='story' i]",
    "[class*='post' i]",
    "[class*='card' i]",
    "[data-testid*='article' i]",
    "[data-testid*='story' i]"
  ].join(",");
  return els.map((el) => {
    const href = el.href || el.getAttribute("href") || "";
    const container = el.closest(parentSelector) || el.parentElement || el;
    const title = normalize(
      el.innerText ||
      el.textContent ||
      el.getAttribute("aria-label") ||
      el.getAttribute("title")
    );
    const description = normalize(container.innerText || container.textContent || "");
    return { href, title, description };
  }).filter((item) => item.href);
}
"""


@dataclass(frozen=True)
class ExtractedArticle:
    url: str
    title: str
    description: str
    content: str


@dataclass(frozen=True)
class ArticleCandidate:
    url: str
    title: str
    description: str


@dataclass(frozen=True)
class ScrapeResult:
    discovered_urls: list[str]
    articles: list[ExtractedArticle]
    skipped_articles: int = 0


def clean_text(html: str) -> str:
    text = SCRIPT_STYLE_RE.sub(" ", html)
    text = TAG_RE.sub(" ", text)
    return " ".join(unescape(text).split())


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def normalize_url(base_url: str, href: str) -> str | None:
    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return absolute.split("#", 1)[0]


def _normalize_candidate(base_url: str, raw_candidate) -> ArticleCandidate | None:
    if isinstance(raw_candidate, str):
        href = raw_candidate
        title = ""
        description = ""
    elif isinstance(raw_candidate, dict):
        href = str(raw_candidate.get("href") or "")
        title = normalize_text(str(raw_candidate.get("title") or ""))
        description = normalize_text(str(raw_candidate.get("description") or ""))
    else:
        return None

    absolute = normalize_url(base_url, href)
    if absolute is None:
        return None
    if description == title:
        description = ""
    return ArticleCandidate(
        url=absolute,
        title=title[:500],
        description=description[:1000],
    )


def discover_article_urls_from_html(base_url: str, html: str, limit: int = 20) -> list[str]:
    return [
        candidate.url
        for candidate in discover_article_candidates_from_html(base_url, html, limit=limit)
    ]


def discover_article_candidates_from_html(
    base_url: str,
    html: str,
    limit: int = 20,
) -> list[ArticleCandidate]:
    base_host = urlparse(base_url).netloc
    seen: set[str] = set()
    candidates: list[ArticleCandidate] = []
    for href in A_RE.findall(html):
        absolute = normalize_url(base_url, href)
        if absolute is None or absolute in seen or urlparse(absolute).netloc != base_host:
            continue
        seen.add(absolute)
        candidates.append(ArticleCandidate(url=absolute, title="", description=""))
        if len(candidates) >= limit:
            break
    return candidates


def _tag_body(html: str, tag: str) -> str | None:
    match = re.search(fr"<{tag}\b[^>]*>(.*?)</{tag}>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1) if match else None


class ArticleTextBlockParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self._skip_depth = 0
        self._current_tag: str | None = None
        self._current_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        if self._skip_depth:
            self._skip_depth += 1
            return
        if normalized_tag in UNWANTED_TAGS or _has_unwanted_attrs(attrs):
            self._skip_depth = 1
            return
        if normalized_tag in BLOCK_TAGS:
            self._flush_current_block()
            self._current_tag = normalized_tag
            self._current_parts = []

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth:
            self._skip_depth -= 1
            return
        if self._current_tag == tag.lower():
            self._flush_current_block()

    def handle_data(self, data: str) -> None:
        if self._skip_depth or self._current_tag is None:
            return
        self._current_parts.append(data)

    def close(self) -> None:
        self._flush_current_block()
        super().close()

    def _flush_current_block(self) -> None:
        if self._current_parts:
            text = normalize_text(unescape(" ".join(self._current_parts)))
            if text:
                self.blocks.append(text)
        self._current_tag = None
        self._current_parts = []


def _has_unwanted_attrs(attrs: list[tuple[str, str | None]]) -> bool:
    for name, value in attrs:
        if name.lower() == "aria-hidden" and str(value).lower() == "true":
            return True
        if name.lower() not in {"class", "id", "aria-label", "data-module", "data-testid"}:
            continue
        lowered = (value or "").lower()
        if any(pattern in lowered for pattern in UNWANTED_ATTR_PATTERNS):
            return True
    return False


def extract_article_text_blocks_from_html(html: str) -> list[str]:
    content_html = _tag_body(html, "article") or _tag_body(html, "main") or html
    parser = ArticleTextBlockParser()
    parser.feed(content_html)
    parser.close()
    if parser.blocks:
        return parser.blocks
    fallback = clean_text(content_html)
    return [fallback] if fallback else []


def extract_article_from_html(url: str, html: str) -> ExtractedArticle:
    title_match = TITLE_RE.search(html)
    title = clean_text(title_match.group(1)) if title_match else ""
    description_match = META_DESCRIPTION_RE.search(html)
    description = unescape(description_match.group(1)).strip() if description_match else ""
    content = normalize_text(" ".join(extract_article_text_blocks_from_html(html)))
    return ExtractedArticle(
        url=url,
        title=title or content[:120] or url,
        description=description,
        content=content,
    )


class PlaywrightScraper:
    def __init__(
        self,
        *,
        timeout_ms: int = 15_000,
        max_articles: int = 20,
        retries: int = 1,
        content_quality: ContentQualityService | None = None,
        topic_relevance: TopicRelevanceService | None = None,
    ) -> None:
        self.timeout_ms = timeout_ms
        self.max_articles = max_articles
        self.retries = retries
        self.content_quality = content_quality
        self.topic_relevance = topic_relevance

    async def scrape_website(self, website: models.Website) -> ScrapeResult:
        from playwright.async_api import async_playwright

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page()
                await self._goto(page, website.base_url)
                candidates = await self._discover_candidates(page, website)
                articles = []
                skipped_articles = 0
                for candidate in candidates:
                    if not await self._should_crawl_candidate(website, candidate):
                        skipped_articles += 1
                        continue
                    await self._goto(page, candidate.url)
                    articles.append(await self._extract_article(page, candidate.url, website))
                return ScrapeResult(
                    discovered_urls=[candidate.url for candidate in candidates],
                    articles=articles,
                    skipped_articles=skipped_articles,
                )
            finally:
                await browser.close()

    async def _goto(self, page, url: str) -> None:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                return
            except Exception as exc:
                last_error = exc
                logger.warning("scrape_load_failed", extra={"url": url, "attempt": attempt + 1})
        raise RuntimeError(f"Failed to load {url}: {last_error}") from last_error

    async def _discover_urls(self, page, website: models.Website) -> list[str]:
        return [candidate.url for candidate in await self._discover_candidates(page, website)]

    async def _discover_candidates(self, page, website: models.Website) -> list[ArticleCandidate]:
        base_url = page.url or website.base_url
        try:
            raw_candidates = await page.locator(website.discovery_selector).evaluate_all(
                DISCOVERY_CANDIDATE_SCRIPT
            )
        except Exception:
            raw_candidates = []

        candidates: list[ArticleCandidate] = []
        seen: set[str] = set()
        for raw_candidate in raw_candidates:
            candidate = _normalize_candidate(base_url, raw_candidate)
            if candidate is None:
                continue
            absolute = candidate.url
            if absolute and absolute not in seen and urlparse(absolute).netloc == urlparse(base_url).netloc:
                seen.add(absolute)
                candidates.append(candidate)
                if len(candidates) >= self.max_articles:
                    return candidates
        return candidates or discover_article_candidates_from_html(
            base_url, await page.content(), self.max_articles
        )

    async def _should_crawl_candidate(
        self,
        website: models.Website,
        candidate: ArticleCandidate,
    ) -> bool:
        target_topics = getattr(website, "target_topics", None)
        if not target_topics or not target_topics.strip():
            return True
        if self.topic_relevance is None:
            logger.warning("topic_relevance_unavailable", extra={"url": candidate.url})
            return False
        try:
            return await self.topic_relevance.is_relevant(
                url=candidate.url,
                title=candidate.title,
                description=candidate.description,
                target_topics=target_topics,
            )
        except Exception:
            logger.exception("topic_relevance_failed", extra={"url": candidate.url})
            return False

    async def _extract_article(self, page, url: str, website: models.Website) -> ExtractedArticle:
        html = await page.content()
        fallback = extract_article_from_html(url, html)
        title = await self._selector_text(page, website.title_selector) or fallback.title
        description = await self._selector_text(page, website.description_selector) or fallback.description
        content_blocks = await self._selector_text_blocks(page, website.content_selector)
        if not content_blocks:
            content_blocks = extract_article_text_blocks_from_html(html)
        if self.content_quality:
            content_blocks = await self.content_quality.filter_blocks(
                url=url,
                title=title,
                description=description,
                blocks=content_blocks,
            )
        content = normalize_text(" ".join(content_blocks)) or fallback.content
        return ExtractedArticle(
            url=url,
            title=title,
            description=description,
            content=content,
        )

    async def _selector_text(self, page, selector: str | None) -> str:
        return await selector_text(page, selector)

    async def _selector_text_blocks(self, page, selector: str | None) -> list[str]:
        if not selector:
            return []
        try:
            raw_blocks = await page.locator(selector).first.evaluate(CONTENT_BLOCK_EXTRACTION_SCRIPT)
        except Exception:
            return []
        if not isinstance(raw_blocks, list):
            return []
        return [normalize_text(str(block)) for block in raw_blocks if normalize_text(str(block))]


def run_scrape_job(session: Session, job: models.ScrapeJob, scraper: PlaywrightScraper) -> None:
    website = repository.get_website(session, job.website_id)
    if website is None:
        job.status = "failed"
        job.failure = "Website not found"
        job.finished_at = models.utcnow()
        session.commit()
        return

    job.status = "running"
    job.started_at = models.utcnow()
    session.commit()
    logger.info("scrape_job_started", extra={"job_id": job.id, "website_id": website.id})

    try:
        result = asyncio.run(scraper.scrape_website(website))
        saved = 0
        for article in result.articles:
            repository.upsert_article(
                session,
                website_id=website.id,
                url=article.url,
                title=article.title,
                description=article.description,
                content=article.content,
            )
            saved += 1
        job.status = "succeeded"
        job.discovered_urls = result.discovered_urls
        job.saved_articles = saved
        job.skipped_articles = result.skipped_articles
        job.failure = None
    except Exception as exc:
        job.status = "failed"
        job.failure = str(exc)
        logger.exception("scrape_job_failed", extra={"job_id": job.id, "website_id": website.id})
    finally:
        job.finished_at = models.utcnow()
        session.commit()
        logger.info("scrape_job_finished", extra={"job_id": job.id, "status": job.status})
