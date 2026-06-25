from news_scraper_backend.core.config import Settings
from scripts import run_backend


def test_run_backend_uses_configured_host_and_port(monkeypatch) -> None:
    calls = []

    monkeypatch.setattr(
        run_backend,
        "get_settings",
        lambda: Settings(backend_host="0.0.0.0", backend_port=9123),
    )

    def fake_uvicorn_run(app, **kwargs):
        calls.append((app, kwargs))

    monkeypatch.setattr(run_backend.uvicorn, "run", fake_uvicorn_run)

    run_backend.main()

    assert calls == [
        (
            "news_scraper_backend.main:app",
            {"host": "0.0.0.0", "port": 9123, "reload": True},
        )
    ]
