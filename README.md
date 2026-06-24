# News Scraper

Browser-based news scraping and administration system.

## Backend

The Python backend is bootstrapped as a FastAPI application package under
`src/news_scraper_backend`.

Local development commands:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m uvicorn news_scraper_backend.main:app --reload
```

Run backend tests:

```bash
.venv/bin/python -m pytest tests/backend
```

Configuration can be provided with environment variables:

- `NEWS_SCRAPER_APP_NAME`
- `NEWS_SCRAPER_APP_VERSION`
- `NEWS_SCRAPER_API_PREFIX`
