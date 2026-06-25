from __future__ import annotations

from fastapi.testclient import TestClient

from news_scraper_backend.scraper.selector_inference import (
    OllamaSelectorError,
    SelectorSuggestion,
    SelectorValidationError,
)
from news_scraper_backend.storage import repository


def website_payload(**overrides):
    payload = {
        "name": "Example News",
        "base_url": "https://example.test",
        "enabled": True,
        "discovery_selector": "a",
        "scrape_frequency_minutes": 60,
    }
    payload.update(overrides)
    return payload


def test_health_and_readiness(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/ready").json() == {"status": "ready"}


def test_website_crud_workflow(client: TestClient) -> None:
    created = client.post(
        "/api/websites",
        json=website_payload(target_topics="politics, science, AI"),
    ).json()
    website_id = created["id"]

    assert created["name"] == "Example News"
    assert created["target_topics"] == "politics, science, AI"
    assert client.get("/api/websites").json()[0]["id"] == website_id
    assert client.get(f"/api/websites/{website_id}").json()["base_url"] == "https://example.test/"

    updated = client.patch(
        f"/api/websites/{website_id}",
        json={"name": "Example Daily", "target_topics": "local government"},
    ).json()
    assert updated["name"] == "Example Daily"
    assert updated["target_topics"] == "local government"

    response = client.delete(f"/api/websites/{website_id}")
    assert response.status_code == 204
    assert client.get(f"/api/websites/{website_id}").status_code == 404


def test_website_target_topics_are_optional(client: TestClient) -> None:
    created = client.post("/api/websites", json=website_payload()).json()

    assert created["target_topics"] is None


def test_validation_duplicate_and_not_found_errors(client: TestClient) -> None:
    assert client.post("/api/websites", json=website_payload(base_url="not-a-url")).status_code == 422
    assert client.post("/api/websites", json=website_payload()).status_code == 201

    duplicate = client.post("/api/websites", json=website_payload(name="Duplicate"))
    assert duplicate.status_code == 409
    assert "already exists" in duplicate.json()["detail"]
    assert client.get("/api/articles", params={"website_id": 404}).status_code == 404


def test_article_list_detail_and_duplicate_upsert(client: TestClient) -> None:
    website = client.post("/api/websites", json=website_payload()).json()
    session = client.app.state.session_factory()
    try:
        article = repository.upsert_article(
            session,
            website_id=website["id"],
            url="https://example.test/news/alpha",
            title="Alpha",
            description="Alpha summary",
            content="Alpha content",
        )
        repository.upsert_article(
            session,
            website_id=website["id"],
            url="https://example.test/news/alpha",
            title="Alpha updated",
            description="Updated summary",
            content="Updated content",
        )
    finally:
        session.close()

    listing = client.get("/api/articles").json()
    assert len(listing) == 1
    assert listing[0]["title"] == "Alpha updated"
    assert client.get(f"/api/articles/{article.id}").json()["content"] == "Updated content"


def test_scrape_job_create_list_and_status(client: TestClient, monkeypatch) -> None:
    website = client.post("/api/websites", json=website_payload()).json()

    def fake_run_scrape_job(session, job, scraper):
        job.status = "succeeded"
        job.discovered_urls = ["https://example.test/news/alpha"]
        job.saved_articles = 1
        job.skipped_articles = 2
        session.commit()

    monkeypatch.setattr("news_scraper_backend.api.router.run_scrape_job", fake_run_scrape_job)
    created = client.post("/api/scrape-jobs", json={"website_id": website["id"]})

    assert created.status_code == 202
    job = client.get(f"/api/scrape-jobs/{created.json()['id']}").json()
    assert job["status"] == "succeeded"
    assert job["saved_articles"] == 1
    assert job["skipped_articles"] == 2
    assert client.get("/api/scrape-jobs").json()[0]["id"] == created.json()["id"]


def test_selector_suggestion_api_returns_validated_selectors(client: TestClient, monkeypatch) -> None:
    class FakeSelectorInferenceService:
        def __init__(self, **kwargs) -> None:
            pass

        async def suggest_selectors(self, base_url: str) -> SelectorSuggestion:
            assert base_url == "https://example.test/"
            return SelectorSuggestion(
                discovery_selector="main a.article-link",
                title_selector="h1",
                description_selector="meta[name='description']",
                content_selector="article",
            )

    monkeypatch.setattr(
        "news_scraper_backend.api.router.SelectorInferenceService",
        FakeSelectorInferenceService,
    )

    response = client.post("/api/selector-suggestions", json={"base_url": "https://example.test"})

    assert response.status_code == 200
    assert response.json() == {
        "discovery_selector": "main a.article-link",
        "title_selector": "h1",
        "description_selector": "meta[name='description']",
        "content_selector": "article",
    }


def test_selector_suggestion_api_maps_validation_errors(client: TestClient, monkeypatch) -> None:
    class FakeSelectorInferenceService:
        def __init__(self, **kwargs) -> None:
            pass

        async def suggest_selectors(self, base_url: str) -> SelectorSuggestion:
            raise SelectorValidationError("content selector did not extract text")

    monkeypatch.setattr(
        "news_scraper_backend.api.router.SelectorInferenceService",
        FakeSelectorInferenceService,
    )

    response = client.post("/api/selector-suggestions", json={"base_url": "https://example.test"})

    assert response.status_code == 422
    assert response.json()["detail"] == "content selector did not extract text"


def test_selector_suggestion_api_maps_ollama_errors(client: TestClient, monkeypatch) -> None:
    class FakeSelectorInferenceService:
        def __init__(self, **kwargs) -> None:
            pass

        async def suggest_selectors(self, base_url: str) -> SelectorSuggestion:
            raise OllamaSelectorError("ollama HTTP 404 for model qwen-test")

    monkeypatch.setattr(
        "news_scraper_backend.api.router.SelectorInferenceService",
        FakeSelectorInferenceService,
    )

    response = client.post("/api/selector-suggestions", json={"base_url": "https://example.test"})

    assert response.status_code == 502
    assert response.json()["detail"] == "ollama HTTP 404 for model qwen-test"
