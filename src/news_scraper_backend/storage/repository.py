from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from news_scraper_backend.storage import models


def list_websites(session: Session) -> list[models.Website]:
    return session.query(models.Website).order_by(models.Website.name.asc()).all()


def get_website(session: Session, website_id: int) -> models.Website | None:
    return session.get(models.Website, website_id)


def create_website(session: Session, **values) -> models.Website:
    website = models.Website(**values)
    session.add(website)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ValueError("A website with this base_url already exists") from None
    session.refresh(website)
    return website


def update_website(session: Session, website: models.Website, **values) -> models.Website:
    for key, value in values.items():
        setattr(website, key, value)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ValueError("A website with this base_url already exists") from None
    session.refresh(website)
    return website


def delete_website(session: Session, website: models.Website) -> None:
    session.delete(website)
    session.commit()


def list_articles(session: Session, website_id: int | None = None) -> list[models.Article]:
    query = session.query(models.Article)
    if website_id is not None:
        query = query.filter(models.Article.website_id == website_id)
    return query.order_by(models.Article.scraped_at.desc(), models.Article.id.desc()).all()


def get_article(session: Session, article_id: int) -> models.Article | None:
    return session.get(models.Article, article_id)


def upsert_article(
    session: Session,
    *,
    website_id: int,
    url: str,
    title: str,
    description: str,
    content: str,
) -> models.Article:
    article = (
        session.query(models.Article)
        .filter(models.Article.website_id == website_id, models.Article.url == url)
        .one_or_none()
    )
    if article is None:
        article = models.Article(
            website_id=website_id,
            url=url,
            title=title,
            description=description,
            content=content,
        )
        session.add(article)
    else:
        article.title = title
        article.description = description
        article.content = content
        article.scraped_at = models.utcnow()
    session.commit()
    session.refresh(article)
    return article


def create_scrape_job(session: Session, website_id: int) -> models.ScrapeJob:
    job = models.ScrapeJob(website_id=website_id)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_scrape_job(session: Session, job_id: int) -> models.ScrapeJob | None:
    return session.get(models.ScrapeJob, job_id)


def list_scrape_jobs(session: Session, website_id: int | None = None) -> list[models.ScrapeJob]:
    query = session.query(models.ScrapeJob)
    if website_id is not None:
        query = query.filter(models.ScrapeJob.website_id == website_id)
    return query.order_by(models.ScrapeJob.created_at.desc(), models.ScrapeJob.id.desc()).all()
