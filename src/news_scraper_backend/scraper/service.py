from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from html import unescape
from urllib.parse import urljoin, urlparse

from sqlalchemy.orm import Session

from news_scraper_backend.scraper.selector_inference import selector_text
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


@dataclass(frozen=True)
class ExtractedArticle:
    url: str
    title: str
    description: str
    content: str


@dataclass(frozen=True)
class ScrapeResult:
    discovered_urls: list[str]
    articles: list[ExtractedArticle]


def clean_text(html: str) -> str:
    text = SCRIPT_STYLE_RE.sub(" ", html)
    text = TAG_RE.sub(" ", text)
    return " ".join(unescape(text).split())


def normalize_url(base_url: str, href: str) -> str | None:
    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return absolute.split("#", 1)[0]


def discover_article_urls_from_html(base_url: str, html: str, limit: int = 20) -> list[str]:
    base_host = urlparse(base_url).netloc
    seen: set[str] = set()
    urls: list[str] = []
    for href in A_RE.findall(html):
        absolute = normalize_url(base_url, href)
        if absolute is None or absolute in seen or urlparse(absolute).netloc != base_host:
            continue
        seen.add(absolute)
        urls.append(absolute)
        if len(urls) >= limit:
            break
    return urls


def _tag_body(html: str, tag: str) -> str | None:
    match = re.search(fr"<{tag}\b[^>]*>(.*?)</{tag}>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1) if match else None


def extract_article_from_html(url: str, html: str) -> ExtractedArticle:
    title_match = TITLE_RE.search(html)
    title = clean_text(title_match.group(1)) if title_match else ""
    description_match = META_DESCRIPTION_RE.search(html)
    description = unescape(description_match.group(1)).strip() if description_match else ""
    content_html = _tag_body(html, "article") or _tag_body(html, "main") or html
    content = clean_text(content_html)
    return ExtractedArticle(
        url=url,
        title=title or content[:120] or url,
        description=description,
        content=content,
    )


class PlaywrightScraper:
    def __init__(self, *, timeout_ms: int = 15_000, max_articles: int = 20, retries: int = 1) -> None:
        self.timeout_ms = timeout_ms
        self.max_articles = max_articles
        self.retries = retries

    async def scrape_website(self, website: models.Website) -> ScrapeResult:
        from playwright.async_api import async_playwright

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page()
                await self._goto(page, website.base_url)
                urls = await self._discover_urls(page, website)
                articles = []
                for url in urls:
                    await self._goto(page, url)
                    articles.append(await self._extract_article(page, url, website))
                return ScrapeResult(discovered_urls=urls, articles=articles)
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
        try:
            hrefs = await page.locator(website.discovery_selector).evaluate_all(
                "(els) => els.map((el) => el.href || el.getAttribute('href')).filter(Boolean)"
            )
        except Exception:
            hrefs = []
        urls: list[str] = []
        seen: set[str] = set()
        for href in hrefs:
            absolute = normalize_url(website.base_url, href)
            if absolute and absolute not in seen and urlparse(absolute).netloc == urlparse(website.base_url).netloc:
                seen.add(absolute)
                urls.append(absolute)
                if len(urls) >= self.max_articles:
                    return urls
        return urls or discover_article_urls_from_html(
            website.base_url, await page.content(), self.max_articles
        )

    async def _extract_article(self, page, url: str, website: models.Website) -> ExtractedArticle:
        fallback = extract_article_from_html(url, await page.content())
        return ExtractedArticle(
            url=url,
            title=await self._selector_text(page, website.title_selector) or fallback.title,
            description=await self._selector_text(page, website.description_selector) or fallback.description,
            content=await self._selector_text(page, website.content_selector) or fallback.content,
        )

    async def _selector_text(self, page, selector: str | None) -> str:
        return await selector_text(page, selector)


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
        job.failure = None
    except Exception as exc:
        job.status = "failed"
        job.failure = str(exc)
        logger.exception("scrape_job_failed", extra={"job_id": job.id, "website_id": website.id})
    finally:
        job.finished_at = models.utcnow()
        session.commit()
        logger.info("scrape_job_finished", extra={"job_id": job.id, "status": job.status})
