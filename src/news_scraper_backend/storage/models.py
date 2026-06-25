from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from news_scraper_backend.storage.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Website(Base):
    __tablename__ = "websites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    base_url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    discovery_selector: Mapped[str] = mapped_column(String(512), nullable=False, default="a")
    title_selector: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description_selector: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content_selector: Mapped[str | None] = mapped_column(String(512), nullable=True)
    target_topics: Mapped[str | None] = mapped_column(Text, nullable=True)
    scrape_frequency_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    articles: Mapped[list["Article"]] = relationship(
        back_populates="website", cascade="all, delete-orphan"
    )
    scrape_jobs: Mapped[list["ScrapeJob"]] = relationship(
        back_populates="website", cascade="all, delete-orphan"
    )


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("website_id", "url", name="uq_article_website_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    website: Mapped[Website] = relationship(back_populates="articles")


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_urls: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    saved_articles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_articles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    website: Mapped[Website] = relationship(back_populates="scrape_jobs")
