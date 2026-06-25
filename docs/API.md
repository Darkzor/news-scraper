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
  "scrape_frequency_minutes": 60
}
```

Returns `201` with the stored website. Duplicate `base_url` values return `409`.

- `GET /api/websites` lists websites.
- `GET /api/websites/{website_id}` returns one website or `404`.
- `PATCH /api/websites/{website_id}` updates any subset of website fields.
- `DELETE /api/websites/{website_id}` deletes the website and dependent records.

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
- `GET /api/scrape-jobs/{job_id}` returns job status, discovered URLs, saved article count, and failure details.
