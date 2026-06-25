# TODO

This checklist is the implementation backlog for the news scraper. Agents should work these items in order unless the user explicitly changes the priority. Each completed item must be marked `[x]` only after implementation and verification.

## Foundation

- [x] Bootstrap Python FastAPI backend project structure
- [x] Bootstrap React frontend project structure
- [x] Add shared local development commands and documentation
- [x] Add automated test runners for backend and frontend
- [x] Add persistent storage model for websites articles and scrape jobs

## Backend API

- [x] Implement backend health and readiness endpoints
- [x] Implement website create API endpoint
- [x] Implement website list API endpoint
- [x] Implement website detail API endpoint
- [x] Implement website update API endpoint
- [x] Implement website delete API endpoint
- [x] Implement article list and detail API endpoints
- [x] Implement scrape job create and status API endpoints
- [x] Add backend validation and error response tests
- [x] Document backend API request and response shapes

## Playwright Scraping

- [x] Add Playwright Python browser runtime setup
- [x] Implement configured website loading with Playwright
- [x] Implement article URL discovery for configured websites
- [x] Implement article title extraction with Playwright
- [x] Implement article description extraction with Playwright
- [x] Implement full article content extraction with Playwright
- [x] Persist extracted article data from scraper runs
- [x] Add scraper retry timeout and failure handling
- [x] Add scraper tests with deterministic HTML fixtures
- [x] Add an end-to-end scrape smoke test for one controlled sample site

## Frontend Admin

- [x] Implement frontend application shell and routing
- [x] Implement website list admin view
- [x] Implement website create form
- [x] Implement website edit form
- [x] Implement website delete action
- [x] Implement manual scrape trigger action
- [x] Implement article list admin view
- [x] Implement article detail view with title description and full content
- [x] Add frontend API client error handling
- [x] Add frontend interaction tests for website CRUD workflows

## Integration And Staging

- [x] Connect frontend website CRUD screens to backend APIs
- [x] Connect frontend scrape trigger to backend scrape job API
- [x] Connect frontend article screens to backend article APIs
- [x] Add full local development startup instructions
- [x] Add CI workflow for backend and frontend tests
- [x] Run full backend frontend and scraper validation
- [x] Merge validated implementation branch into staging

## Hardening

- [x] Add structured logging for scrape jobs
- [x] Add scrape job history and failure visibility in the admin UI
- [x] Add robots and rate limit policy documentation
- [x] Add configurable scrape frequency per website
- [x] Add duplicate article detection
- [x] Add deployment documentation for staging
- [x] Add .env file loading for backend configuration
- [x] Make backend and frontend ports configurable in .env
- [x] Add Qwen powered selector inference workflow
