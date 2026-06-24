# TODO

This checklist is the implementation backlog for the news scraper. Agents should work these items in order unless the user explicitly changes the priority. Each completed item must be marked `[x]` only after implementation and verification.

## Foundation

- [x] Bootstrap Python FastAPI backend project structure
- [x] Bootstrap React frontend project structure
- [ ] Add shared local development commands and documentation
- [x] Add automated test runners for backend and frontend
- [ ] Add persistent storage model for websites articles and scrape jobs

## Backend API

- [ ] Implement backend health and readiness endpoints
- [ ] Implement website create API endpoint
- [ ] Implement website list API endpoint
- [ ] Implement website detail API endpoint
- [ ] Implement website update API endpoint
- [ ] Implement website delete API endpoint
- [ ] Implement article list and detail API endpoints
- [ ] Implement scrape job create and status API endpoints
- [ ] Add backend validation and error response tests
- [ ] Document backend API request and response shapes

## Playwright Scraping

- [ ] Add Playwright Python browser runtime setup
- [ ] Implement configured website loading with Playwright
- [ ] Implement article URL discovery for configured websites
- [ ] Implement article title extraction with Playwright
- [ ] Implement article description extraction with Playwright
- [ ] Implement full article content extraction with Playwright
- [ ] Persist extracted article data from scraper runs
- [ ] Add scraper retry timeout and failure handling
- [ ] Add scraper tests with deterministic HTML fixtures
- [ ] Add an end-to-end scrape smoke test for one controlled sample site

## Frontend Admin

- [ ] Implement frontend application shell and routing
- [ ] Implement website list admin view
- [ ] Implement website create form
- [ ] Implement website edit form
- [ ] Implement website delete action
- [ ] Implement manual scrape trigger action
- [ ] Implement article list admin view
- [ ] Implement article detail view with title description and full content
- [ ] Add frontend API client error handling
- [ ] Add frontend interaction tests for website CRUD workflows

## Integration And Staging

- [ ] Connect frontend website CRUD screens to backend APIs
- [ ] Connect frontend scrape trigger to backend scrape job API
- [ ] Connect frontend article screens to backend article APIs
- [ ] Add full local development startup instructions
- [ ] Add CI workflow for backend and frontend tests
- [ ] Run full backend frontend and scraper validation
- [ ] Merge validated implementation branch into staging

## Hardening

- [ ] Add structured logging for scrape jobs
- [ ] Add scrape job history and failure visibility in the admin UI
- [ ] Add robots and rate limit policy documentation
- [ ] Add configurable scrape frequency per website
- [ ] Add duplicate article detection
- [ ] Add deployment documentation for staging
