# Staging Deployment

Run the backend and frontend as separate services in staging.

## Backend

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
cp .env.example .env
.venv/bin/python scripts/run_backend.py
```

Install Playwright's Chromium runtime before live browser scraping:

```bash
.venv/bin/python -m playwright install chromium
```

## Frontend

```bash
npm --prefix frontend install
npm --prefix frontend run build
```

Serve `frontend/dist` from the staging web server and proxy `/api` to the backend service.

## Validation

```bash
make test
```
