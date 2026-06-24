"""Runtime configuration for the FastAPI backend."""

from functools import lru_cache
from os import getenv

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings resolved at startup."""

    app_name: str = Field(default="News Scraper API")
    app_version: str = Field(default="0.1.0")
    api_prefix: str = Field(default="/api")


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
    )
