"""Runtime configuration for the FastAPI backend."""

from functools import lru_cache
from os import environ
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings resolved at startup."""

    app_name: str = Field(default="News Scraper API")
    app_version: str = Field(default="0.1.0")
    api_prefix: str = Field(default="/api")
    backend_host: str = Field(default="127.0.0.1")
    backend_port: int = Field(default=8000)
    frontend_port: int = Field(default=5173)
    database_url: str = Field(default="sqlite:///./news_scraper.db")
    scraper_timeout_ms: int = Field(default=15_000)
    scraper_max_articles: int = Field(default=20)
    scraper_retries: int = Field(default=1)
    ollama_base_url: str = Field(default="http://172.16.15.201:11434")
    ollama_model: str = Field(default="qwen3.6:35b-a3b")
    ollama_timeout_ms: int = Field(default=60_000)
    ollama_auth_header: str | None = Field(default=None)
    selector_inference_max_html_chars: int = Field(default=30_000)
    content_qa_enabled: bool = Field(default=True)
    content_qa_max_blocks: int = Field(default=80)
    content_qa_min_block_chars: int = Field(default=40)


_ENV_TO_FIELD = {
    "NEWS_SCRAPER_APP_NAME": "app_name",
    "NEWS_SCRAPER_APP_VERSION": "app_version",
    "NEWS_SCRAPER_API_PREFIX": "api_prefix",
    "NEWS_SCRAPER_BACKEND_HOST": "backend_host",
    "NEWS_SCRAPER_BACKEND_PORT": "backend_port",
    "NEWS_SCRAPER_FRONTEND_PORT": "frontend_port",
    "NEWS_SCRAPER_DATABASE_URL": "database_url",
    "NEWS_SCRAPER_TIMEOUT_MS": "scraper_timeout_ms",
    "NEWS_SCRAPER_MAX_ARTICLES": "scraper_max_articles",
    "NEWS_SCRAPER_RETRIES": "scraper_retries",
    "NEWS_SCRAPER_OLLAMA_BASE_URL": "ollama_base_url",
    "NEWS_SCRAPER_OLLAMA_MODEL": "ollama_model",
    "NEWS_SCRAPER_OLLAMA_TIMEOUT_MS": "ollama_timeout_ms",
    "NEWS_SCRAPER_OLLAMA_AUTH_HEADER": "ollama_auth_header",
    "NEWS_SCRAPER_SELECTOR_INFERENCE_MAX_HTML_CHARS": "selector_inference_max_html_chars",
    "NEWS_SCRAPER_CONTENT_QA_ENABLED": "content_qa_enabled",
    "NEWS_SCRAPER_CONTENT_QA_MAX_BLOCKS": "content_qa_max_blocks",
    "NEWS_SCRAPER_CONTENT_QA_MIN_BLOCK_CHARS": "content_qa_min_block_chars",
}

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _default_env_files() -> tuple[Path, ...]:
    """Return supported .env locations in increasing precedence order."""

    paths = (_PROJECT_ROOT / ".env", Path.cwd() / ".env")
    return tuple(dict.fromkeys(paths))


def _parse_env_value(raw_value: str) -> str:
    value = raw_value.strip()
    if not value:
        return value
    if value[0] in {"'", '"'} and value[-1:] == value[0]:
        return value[1:-1]
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    return value


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue

        key, raw_value = line.split("=", 1)
        key = key.strip()
        if key:
            values[key] = _parse_env_value(raw_value)

    return values


def _settings_environment() -> dict[str, str]:
    values: dict[str, str] = {}
    for path in _default_env_files():
        values.update(_read_env_file(path))
    values.update(environ)
    return values


@lru_cache
def get_settings() -> Settings:
    """Return settings from .env files and environment variables."""

    environment = _settings_environment()
    return Settings(
        **{
            field_name: environment[env_name]
            for env_name, field_name in _ENV_TO_FIELD.items()
            if env_name in environment
        }
    )
