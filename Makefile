.PHONY: install install-backend install-frontend dev-backend dev-frontend test test-backend test-frontend build-frontend

install: install-backend install-frontend

install-backend:
	python3 -m venv .venv
	.venv/bin/python -m pip install -e ".[dev]"

install-frontend:
	npm --prefix frontend install

dev-backend:
	.venv/bin/python scripts/run_backend.py

dev-frontend:
	npm --prefix frontend run dev

test: test-backend test-frontend build-frontend

test-backend:
	.venv/bin/python -m pytest tests/backend

test-frontend:
	npm --prefix frontend test

build-frontend:
	npm --prefix frontend run build
