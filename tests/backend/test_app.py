from news_scraper_backend.core.config import Settings, get_settings
from news_scraper_backend.main import create_app


def test_create_app_exposes_configured_openapi_metadata() -> None:
    app = create_app(
        Settings(
            app_name="Test News API",
            app_version="9.9.9",
            api_prefix="/test-api",
        )
    )

    schema = app.openapi()

    assert schema["info"]["title"] == "Test News API"
    assert schema["info"]["version"] == "9.9.9"


def test_create_app_stores_resolved_settings() -> None:
    settings = Settings(api_prefix="/backend")

    app = create_app(settings)

    assert app.state.settings is settings


def test_get_settings_reads_environment(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("NEWS_SCRAPER_APP_NAME", "Env News API")
    monkeypatch.setenv("NEWS_SCRAPER_APP_VERSION", "1.2.3")
    monkeypatch.setenv("NEWS_SCRAPER_API_PREFIX", "/env-api")
    monkeypatch.setenv("NEWS_SCRAPER_DATABASE_URL", "sqlite:///env.db")
    monkeypatch.setenv("NEWS_SCRAPER_TIMEOUT_MS", "1234")
    monkeypatch.setenv("NEWS_SCRAPER_MAX_ARTICLES", "7")
    monkeypatch.setenv("NEWS_SCRAPER_RETRIES", "2")

    settings = get_settings()

    assert settings == Settings(
        app_name="Env News API",
        app_version="1.2.3",
        api_prefix="/env-api",
        database_url="sqlite:///env.db",
        scraper_timeout_ms=1234,
        scraper_max_articles=7,
        scraper_retries=2,
    )
    get_settings.cache_clear()
