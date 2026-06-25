# Backend API

The FastAPI backend serves routes under `/api` by default.

## Health

- `GET /api/health` returns `{ "status": "ok" }`.
- `GET /api/ready` verifies database connectivity and returns `{ "status": "ready" }`.

## Websites

`POST /api/websites`

```json
{
  "name": "Example News",
  "base_url": "https://example.test",
  "enabled": true,
  "discovery_selector": "a",
  "title_selector": "h1",
  "description_selector": "meta[name='description']",
  "content_selector": "article",
  "target_topics": "politics, science, AI",
  "scrape_frequency_minutes": 60
}
```

Returns `201` with the stored website. Duplicate `base_url` values return `409`.

- `GET /api/websites` lists websites.
- `GET /api/websites/{website_id}` returns one website or `404`.
- `PATCH /api/websites/{website_id}` updates any subset of website fields.
- `DELETE /api/websites/{website_id}` deletes the website and dependent records.

When `target_topics` is set, scrape jobs use the configured Ollama/Qwen
connection to classify discovered article candidates from their title and short
description before opening each article URL. Candidates related to any configured
topic are crawled. Candidates Qwen marks unrelated, or candidates that cannot be
classified because Qwen fails or returns invalid JSON, are skipped. Blank
`target_topics` preserves the default behavior and crawls all discovered
articles.

## Selector Suggestions

`POST /api/selector-suggestions`

```json
{
  "base_url": "https://example.test"
}
```

Returns validated selectors that can be reviewed and saved on a website:

```json
{
  "discovery_selector": "main a.article-link",
  "title_selector": "h1",
  "description_selector": "meta[name='description']",
  "content_selector": "article"
}
```

Ollama or model failures return `502`. Generated selectors that do not extract
usable rendered content return `422`.

Scrape jobs can also use the configured Ollama/Qwen connection as an advisory
article-content quality filter. Content QA removes only text blocks that Qwen
explicitly marks as unrelated; model failures are logged and ignored so scrape
jobs continue.

## Articles

- `GET /api/articles` lists extracted articles, newest first. Optional query: `website_id`.
- `GET /api/articles/{article_id}` returns title, description, full content, URL, source website id, and timestamps.

## Scrape Jobs

`POST /api/scrape-jobs`

```json
{
  "website_id": 1
}
```

Returns `202` with the created job. The admin UI also uses `POST /api/websites/{website_id}/scrape`.

- `GET /api/scrape-jobs` lists job history. Optional query: `website_id`.
- `GET /api/scrape-jobs/{job_id}` returns job status, discovered URLs, saved article count, skipped article count, and failure details.

Scrape job responses include `skipped_articles`:

```json
{
  "id": 1,
  "website_id": 1,
  "status": "succeeded",
  "started_at": "2026-06-25T10:00:00Z",
  "finished_at": "2026-06-25T10:00:10Z",
  "discovered_urls": ["https://example.test/news/alpha"],
  "saved_articles": 1,
  "skipped_articles": 3,
  "failure": null,
  "created_at": "2026-06-25T10:00:00Z"
}
```
