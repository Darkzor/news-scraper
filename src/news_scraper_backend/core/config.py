"""Runtime configuration for the FastAPI backend."""

from functools import lru_cache
from os import getenv

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings resolved at startup."""

    app_name: str = Field(default="News Scraper API")
    app_version: str = Field(default="0.1.0")
    api_prefix: str = Field(default="/api")
    database_url: str = Field(default="sqlite:///./news_scraper.db")
    scraper_timeout_ms: int = Field(default=15_000)
    scraper_max_articles: int = Field(default=20)
    scraper_retries: int = Field(default=1)


@lru_cache
def get_settings() -> Settings:
    """Return settings from environment variables with project defaults."""

    return Settings(
        app_name=getenv("NEWS_SCRAPER_APP_NAME", Settings.model_fields["app_name"].default),
        app_version=getenv(
            "NEWS_SCRAPER_APP_VERSION",
            Settings.model_fields["app_version"].default,
        ),
        api_prefix=getenv("NEWS_SCRAPER_API_PREFIX", Settings.model_fields["api_prefix"].default),
        database_url=getenv(
            "NEWS_SCRAPER_DATABASE_URL",
            Settings.model_fields["database_url"].default,
        ),
        scraper_timeout_ms=int(
            getenv(
                "NEWS_SCRAPER_TIMEOUT_MS",
                Settings.model_fields["scraper_timeout_ms"].default,
            )
        ),
        scraper_max_articles=int(
            getenv(
                "NEWS_SCRAPER_MAX_ARTICLES",
                Settings.model_fields["scraper_max_articles"].default,
            )
        ),
        scraper_retries=int(
            getenv(
                "NEWS_SCRAPER_RETRIES",
                Settings.model_fields["scraper_retries"].default,
            )
        ),
    )
