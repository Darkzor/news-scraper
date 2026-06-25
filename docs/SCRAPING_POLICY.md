# Scraping Policy

Use this scraper only for operator-configured sites where automated access and content extraction are allowed.

## Robots And Terms

- Review each target site's `robots.txt`, terms of service, and publisher policies before enabling it.
- Do not configure sources that prohibit automated page loading or article extraction.
- Keep selectors narrow and specific to allowed article pages.
- Treat Qwen selector inference as an operator aid, not permission to scrape a site.
  Review inferred selectors before saving and enabling automated runs.

## Rate Limits

- Use `scrape_frequency_minutes` to keep automated runs low volume.
- Avoid concurrent runs against the same website.
- Keep `NEWS_SCRAPER_MAX_ARTICLES`, `NEWS_SCRAPER_TIMEOUT_MS`, and `NEWS_SCRAPER_RETRIES` conservative.
- Treat repeated timeout or failure jobs as a signal to disable the source until selectors and permissions are reviewed.

## Duplicate Detection

Articles are unique by website and URL. Re-scraping the same URL updates the existing record instead of inserting duplicates.

## Failure Visibility

Each scrape run records a scrape job with status, timestamps, discovered URLs, saved article count, and failure details. The admin UI shows this job history.
