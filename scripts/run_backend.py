"""Run the backend development server with repository configuration."""

from __future__ import annotations

import uvicorn

from news_scraper_backend.core.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "news_scraper_backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
