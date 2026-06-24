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
