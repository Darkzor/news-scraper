# News Scraper

Browser-based news scraping and administration system.

## Stack

- Backend: FastAPI, SQLAlchemy, SQLite by default.
- Scraper: Playwright Python with deterministic HTML extraction helpers for tests.
- Frontend: React and Vite.

## Backend

The Python backend is bootstrapped as a FastAPI application package under
`src/news_scraper_backend`.

Local development commands:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
cp .env.example .env
.venv/bin/python scripts/run_backend.py
```

Run backend tests:

```bash
.venv/bin/python -m pytest tests/backend
```

Configuration can be provided with environment variables or a local `.env` file
copied from `.env.example`. Values from the process environment override values
from `.env`.

- `NEWS_SCRAPER_APP_NAME`
- `NEWS_SCRAPER_APP_VERSION`
- `NEWS_SCRAPER_API_PREFIX`
- `NEWS_SCRAPER_BACKEND_HOST`
- `NEWS_SCRAPER_BACKEND_PORT`
- `NEWS_SCRAPER_FRONTEND_PORT`
- `NEWS_SCRAPER_DATABASE_URL`
- `NEWS_SCRAPER_TIMEOUT_MS`
- `NEWS_SCRAPER_MAX_ARTICLES`
- `NEWS_SCRAPER_RETRIES`
- `NEWS_SCRAPER_OLLAMA_BASE_URL`
- `NEWS_SCRAPER_OLLAMA_MODEL`
- `NEWS_SCRAPER_OLLAMA_TIMEOUT_MS`
- `NEWS_SCRAPER_OLLAMA_AUTH_HEADER`
- `NEWS_SCRAPER_SELECTOR_INFERENCE_MAX_HTML_CHARS`
- `NEWS_SCRAPER_CONTENT_QA_ENABLED`
- `NEWS_SCRAPER_CONTENT_QA_MAX_BLOCKS`
- `NEWS_SCRAPER_CONTENT_QA_MIN_BLOCK_CHARS`

Selector inference uses the configured Ollama endpoint to ask Qwen for CSS
selectors, then validates those selectors against rendered pages before the
admin UI fills the form. The default local example points at
`http://172.16.15.201:11434` with model `qwen3.6:35b-a3b`.

When content QA is enabled, article extraction uses the same Ollama/Qwen
configuration as an advisory filter for unrelated embedded text blocks. Qwen
failures are logged and do not fail scrape jobs.

Websites can also define `target_topics`, such as `politics, science, AI`.
When topics are present, scrape jobs ask Qwen to classify each discovered
article candidate from the index-page title and short description before opening
the article URL. Candidates are crawled when they match any configured topic;
Qwen failures fail closed for those candidates and increment the skipped count.

## Frontend

The React admin frontend is bootstrapped as a Vite application under
`frontend`.

Local development commands:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server reads `NEWS_SCRAPER_FRONTEND_PORT`,
`NEWS_SCRAPER_BACKEND_HOST`, and `NEWS_SCRAPER_BACKEND_PORT` from the repository
root `.env` file.

Run frontend checks:

```bash
cd frontend
npm test
npm run build
```

## Test Runner

Run both automated test suites from the repository root:

```bash
.venv/bin/python scripts/run_tests.py
```

Run one suite by passing a target:

```bash
.venv/bin/python scripts/run_tests.py backend
.venv/bin/python scripts/run_tests.py frontend
```

The same workflow is available through `make`:

```bash
make install
make test
```

## API And Operations

- API shapes are documented in [docs/API.md](docs/API.md).
- Scraping policy and rate-limit guidance are documented in [docs/SCRAPING_POLICY.md](docs/SCRAPING_POLICY.md).
- Staging deployment notes are documented in [docs/STAGING_DEPLOYMENT.md](docs/STAGING_DEPLOYMENT.md).
