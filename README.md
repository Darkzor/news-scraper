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
- `NEWS_SCRAPER_DATABASE_URL`
- `NEWS_SCRAPER_TIMEOUT_MS`
- `NEWS_SCRAPER_MAX_ARTICLES`
- `NEWS_SCRAPER_RETRIES`

## Frontend

The React admin frontend is bootstrapped as a Vite application under
`frontend`.

Local development commands:

```bash
cd frontend
npm install
npm run dev
```

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
