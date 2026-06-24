"""FastAPI application entrypoint."""

from fastapi import FastAPI

from news_scraper_backend.api.router import api_router
from news_scraper_backend.core.config import Settings, get_settings
from news_scraper_backend.storage.database import init_database


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    resolved_settings = settings or get_settings()
    app = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
    )
    app.state.settings = resolved_settings
    app.state.session_factory = init_database(resolved_settings.database_url)
    app.include_router(api_router, prefix=resolved_settings.api_prefix)
    return app


app = create_app()
