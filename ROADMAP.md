# Roadmap

The project will be delivered in phases so each branch can provide a testable improvement and be merged into `staging` after validation.

## Phase 1: MVP Foundation

- Create the FastAPI backend structure.
- Create the React frontend structure.
- Add local development commands.
- Add backend and frontend test runners.
- Define persistence for websites, articles, and scrape jobs.

## Phase 2: Website Administration

- Provide backend CRUD APIs for websites to be scraped.
- Build frontend views for listing, adding, editing, and deleting websites.
- Validate website inputs before they reach scraping logic.
- Cover the website workflow with backend and frontend tests.

## Phase 3: Playwright Article Extraction

- Use Playwright Python to load configured websites in a real browser context.
- Discover article URLs from configured websites.
- Extract article title, description, and full content from article pages.
- Persist extracted articles and scrape-job outcomes.
- Add deterministic fixture-backed tests for extraction behavior.

## Phase 4: Admin Operations

- Add frontend controls to trigger scrape jobs manually.
- Show scrape job status, recent failures, and extracted article lists.
- Add article detail pages that expose title, description, full content, source website, and scrape metadata.
- Improve API error handling and user-facing failure states.

## Phase 5: Reliability And Scale

- Add duplicate detection for repeated articles.
- Add configurable scrape frequency and scheduling.
- Add structured logging and operational documentation.
- Document robots, rate-limit, and site-specific compliance expectations.
- Prepare deployment instructions for the `staging` environment.

## Future Enhancements

- Multi-user admin authentication.
- Site-specific extraction rules.
- Content classification and tagging.
- Search over extracted articles.
- Export feeds or API integrations for downstream consumers.
