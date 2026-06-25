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
    monkeypatch.setenv("NEWS_SCRAPER_BACKEND_HOST", "0.0.0.0")
    monkeypatch.setenv("NEWS_SCRAPER_BACKEND_PORT", "9000")
    monkeypatch.setenv("NEWS_SCRAPER_FRONTEND_PORT", "5174")
    monkeypatch.setenv("NEWS_SCRAPER_DATABASE_URL", "sqlite:///env.db")
    monkeypatch.setenv("NEWS_SCRAPER_TIMEOUT_MS", "1234")
    monkeypatch.setenv("NEWS_SCRAPER_MAX_ARTICLES", "7")
    monkeypatch.setenv("NEWS_SCRAPER_RETRIES", "2")
    monkeypatch.setenv("NEWS_SCRAPER_OLLAMA_BASE_URL", "http://ollama.test:11434")
    monkeypatch.setenv("NEWS_SCRAPER_OLLAMA_MODEL", "qwen-test")
    monkeypatch.setenv("NEWS_SCRAPER_OLLAMA_TIMEOUT_MS", "5000")
    monkeypatch.setenv("NEWS_SCRAPER_OLLAMA_AUTH_HEADER", "Bearer token")
    monkeypatch.setenv("NEWS_SCRAPER_SELECTOR_INFERENCE_MAX_HTML_CHARS", "12345")

    settings = get_settings()

    assert settings == Settings(
        app_name="Env News API",
        app_version="1.2.3",
        api_prefix="/env-api",
        backend_host="0.0.0.0",
        backend_port=9000,
        frontend_port=5174,
        database_url="sqlite:///env.db",
        scraper_timeout_ms=1234,
        scraper_max_articles=7,
        scraper_retries=2,
        ollama_base_url="http://ollama.test:11434",
        ollama_model="qwen-test",
        ollama_timeout_ms=5000,
        ollama_auth_header="Bearer token",
        selector_inference_max_html_chars=12345,
    )
    get_settings.cache_clear()


def test_get_settings_reads_dotenv_file(tmp_path, monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath(".env").write_text(
        "\n".join(
            [
                "# local backend settings",
                "NEWS_SCRAPER_APP_NAME='Dotenv News API'",
                "NEWS_SCRAPER_APP_VERSION=2.0.0",
                "NEWS_SCRAPER_API_PREFIX=/dotenv-api",
                "NEWS_SCRAPER_BACKEND_HOST=0.0.0.0",
                "NEWS_SCRAPER_BACKEND_PORT=9100",
                "NEWS_SCRAPER_FRONTEND_PORT=5175",
                "NEWS_SCRAPER_DATABASE_URL=sqlite:///dotenv.db",
                "NEWS_SCRAPER_TIMEOUT_MS=4321",
                "NEWS_SCRAPER_MAX_ARTICLES=11",
                "export NEWS_SCRAPER_RETRIES=3",
                "NEWS_SCRAPER_OLLAMA_BASE_URL=http://dotenv-ollama.test:11434",
                "NEWS_SCRAPER_OLLAMA_MODEL=qwen-dotenv",
                "NEWS_SCRAPER_OLLAMA_TIMEOUT_MS=6000",
                "NEWS_SCRAPER_OLLAMA_AUTH_HEADER='Bearer dotenv'",
                "NEWS_SCRAPER_SELECTOR_INFERENCE_MAX_HTML_CHARS=23456",
            ]
        ),
        encoding="utf-8",
    )

    settings = get_settings()

    assert settings == Settings(
        app_name="Dotenv News API",
        app_version="2.0.0",
        api_prefix="/dotenv-api",
        backend_host="0.0.0.0",
        backend_port=9100,
        frontend_port=5175,
        database_url="sqlite:///dotenv.db",
        scraper_timeout_ms=4321,
        scraper_max_articles=11,
        scraper_retries=3,
        ollama_base_url="http://dotenv-ollama.test:11434",
        ollama_model="qwen-dotenv",
        ollama_timeout_ms=6000,
        ollama_auth_header="Bearer dotenv",
        selector_inference_max_html_chars=23456,
    )
    get_settings.cache_clear()


def test_get_settings_environment_overrides_dotenv_file(tmp_path, monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath(".env").write_text(
        "NEWS_SCRAPER_APP_NAME=Dotenv News API\n"
        "NEWS_SCRAPER_MAX_ARTICLES=5\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NEWS_SCRAPER_APP_NAME", "Process Env News API")

    settings = get_settings()

    assert settings.app_name == "Process Env News API"
    assert settings.scraper_max_articles == 5
    get_settings.cache_clear()
