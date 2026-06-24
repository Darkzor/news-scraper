.PHONY: install install-backend install-frontend dev-backend dev-frontend test test-backend test-frontend build-frontend

install: install-backend install-frontend

install-backend:
	python3 -m venv .venv
	.venv/bin/python -m pip install -e ".[dev]"

install-frontend:
	npm --prefix frontend install

dev-backend:
	.venv/bin/python -m uvicorn news_scraper_backend.main:app --reload --host 127.0.0.1 --port 8000

dev-frontend:
	npm --prefix frontend run dev

test: test-backend test-frontend build-frontend

test-backend:
	.venv/bin/python -m pytest tests/backend

test-frontend:
	npm --prefix frontend test

build-frontend:
	npm --prefix frontend run build
