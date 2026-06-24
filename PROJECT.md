# News Scraper Project

## Purpose

This project is a browser-based news scraping and administration system. It lets an operator configure websites, run Playwright-powered scrapes, and review extracted articles through a web admin interface.

## Target Users

- Operators who maintain a list of websites to scrape.
- Developers who extend scraping and extraction behavior.
- Reviewers who inspect extracted article title, description, and full content.

## Architecture

- Backend: FastAPI REST API.
- Scraper: Playwright Python services that load websites, discover article URLs, and extract article data from real rendered pages.
- Frontend: React admin interface.
- Persistence: database-backed storage for websites, articles, and scrape jobs.

The backend owns all persistent state and exposes APIs for the frontend and scraper workflows. The scraper should be callable from backend job endpoints and testable as a standalone service layer.

## Core Entities

- Website: a configured source site with name, base URL, scrape settings, and enabled or disabled state.
- Article: extracted content with source website, URL, title, description, full content, and scrape metadata.
- Scrape job: a tracked scrape execution with status, timestamps, discovered URLs, saved articles, and failure details.

## Expected Workflows

- An operator adds a website in the React admin UI.
- The frontend sends the request to the FastAPI backend.
- The backend validates and stores the website.
- An operator manually triggers a scrape for a website.
- The backend starts a scrape job.
- Playwright loads the configured website, discovers article pages, and extracts title, description, and full content.
- The backend persists extracted articles and scrape job results.
- The frontend shows websites, scrape job status, article lists, and article details.

## Quality Requirements

- Every behavior change must include focused tests.
- API behavior must be documented and validated with tests.
- Scraper extraction must be deterministic under test using fixtures or controlled sample pages.
- Frontend workflows must handle loading, success, empty, and error states.
- Agents must keep `TODO.md` current as implementation tasks are completed.
- Completed task branches must be merged into `staging` after validation.

## Initial Non-Goals

- User authentication.
- Paid subscription or billing features.
- Large-scale distributed crawling.
- Search indexing.
- Machine learning classification.
- Production deployment automation beyond basic staging documentation.
