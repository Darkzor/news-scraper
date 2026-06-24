from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from news_scraper_backend.core.config import Settings
from news_scraper_backend.main import create_app


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    app = create_app(Settings(database_url=database_url))
    with TestClient(app) as test_client:
        yield test_client
