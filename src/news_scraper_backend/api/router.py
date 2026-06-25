"""Top-level API router."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from news_scraper_backend.api import schemas
from news_scraper_backend.scraper.content_quality import ContentQualityService
from news_scraper_backend.scraper.selector_inference import (
    OllamaSelectorClient,
    OllamaSelectorError,
    SelectorInferenceService,
    SelectorValidationError,
)
from news_scraper_backend.scraper.service import PlaywrightScraper, run_scrape_job
from news_scraper_backend.scraper.topic_relevance import TopicRelevanceService
from news_scraper_backend.storage import repository
from news_scraper_backend.storage.database import get_session

api_router = APIRouter()


@api_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@api_router.get("/ready")
def readiness(session: Session = Depends(get_session)) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"status": "ready"}


@api_router.post(
    "/websites",
    response_model=schemas.WebsiteRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": schemas.ErrorResponse}},
)
def create_website(payload: schemas.WebsiteCreate, session: Session = Depends(get_session)):
    try:
        return repository.create_website(session, **payload.model_dump(mode="json"))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@api_router.get("/websites", response_model=list[schemas.WebsiteRead])
def list_websites(session: Session = Depends(get_session)):
    return repository.list_websites(session)


@api_router.get("/websites/{website_id}", response_model=schemas.WebsiteRead)
def get_website(website_id: int, session: Session = Depends(get_session)):
    website = repository.get_website(session, website_id)
    if website is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
    return website


@api_router.patch("/websites/{website_id}", response_model=schemas.WebsiteRead)
def update_website(
    website_id: int,
    payload: schemas.WebsiteUpdate,
    session: Session = Depends(get_session),
):
    website = repository.get_website(session, website_id)
    if website is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
    try:
        return repository.update_website(
            session,
            website,
            **payload.model_dump(exclude_unset=True, mode="json"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@api_router.delete("/websites/{website_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_website(website_id: int, session: Session = Depends(get_session)):
    website = repository.get_website(session, website_id)
    if website is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
    repository.delete_website(session, website)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api_router.post(
    "/selector-suggestions",
    response_model=schemas.SelectorSuggestionRead,
    responses={
        422: {"model": schemas.ErrorResponse},
        502: {"model": schemas.ErrorResponse},
    },
)
async def suggest_selectors(payload: schemas.SelectorSuggestionRequest, request: Request):
    settings = request.app.state.settings
    ollama = OllamaSelectorClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_ms=settings.ollama_timeout_ms,
        auth_header=settings.ollama_auth_header,
    )
    service = SelectorInferenceService(
        ollama=ollama,
        timeout_ms=settings.scraper_timeout_ms,
        max_html_chars=settings.selector_inference_max_html_chars,
    )
    try:
        return await service.suggest_selectors(str(payload.base_url))
    except SelectorValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OllamaSelectorError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@api_router.get("/articles", response_model=list[schemas.ArticleRead])
def list_articles(website_id: int | None = None, session: Session = Depends(get_session)):
    if website_id is not None and repository.get_website(session, website_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
    return repository.list_articles(session, website_id=website_id)


@api_router.get("/articles/{article_id}", response_model=schemas.ArticleRead)
def get_article(article_id: int, session: Session = Depends(get_session)):
    article = repository.get_article(session, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return article


def _create_scrape_job(
    website_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    session: Session,
):
    if repository.get_website(session, website_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
    job = repository.create_scrape_job(session, website_id)
    settings = request.app.state.settings
    ollama = OllamaSelectorClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_ms=settings.ollama_timeout_ms,
        auth_header=settings.ollama_auth_header,
    )
    topic_relevance = TopicRelevanceService(ollama=ollama)
    content_quality = None
    if settings.content_qa_enabled:
        content_quality = ContentQualityService(
            ollama=ollama,
            max_blocks=settings.content_qa_max_blocks,
            min_block_chars=settings.content_qa_min_block_chars,
        )
    scraper = PlaywrightScraper(
        timeout_ms=settings.scraper_timeout_ms,
        max_articles=settings.scraper_max_articles,
        retries=settings.scraper_retries,
        content_quality=content_quality,
        topic_relevance=topic_relevance,
    )
    background_tasks.add_task(run_scrape_job, session, job, scraper)
    return job


@api_router.post(
    "/scrape-jobs",
    response_model=schemas.ScrapeJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_scrape_job(
    payload: schemas.ScrapeJobCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    return _create_scrape_job(payload.website_id, request, background_tasks, session)


@api_router.post(
    "/websites/{website_id}/scrape",
    response_model=schemas.ScrapeJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def scrape_website(
    website_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    return _create_scrape_job(website_id, request, background_tasks, session)


@api_router.get("/scrape-jobs", response_model=list[schemas.ScrapeJobRead])
def list_scrape_jobs(website_id: int | None = None, session: Session = Depends(get_session)):
    if website_id is not None and repository.get_website(session, website_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
    return repository.list_scrape_jobs(session, website_id=website_id)


@api_router.get("/scrape-jobs/{job_id}", response_model=schemas.ScrapeJobRead)
def get_scrape_job(job_id: int, session: Session = Depends(get_session)):
    job = repository.get_scrape_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scrape job not found")
    return job
