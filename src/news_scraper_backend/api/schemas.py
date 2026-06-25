from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ErrorResponse(BaseModel):
    detail: str


class WebsiteBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    base_url: HttpUrl
    enabled: bool = True
    discovery_selector: str = Field(default="a", min_length=1, max_length=512)
    title_selector: str | None = Field(default=None, max_length=512)
    description_selector: str | None = Field(default=None, max_length=512)
    content_selector: str | None = Field(default=None, max_length=512)
    scrape_frequency_minutes: int | None = Field(default=None, ge=1, le=10080)


class WebsiteCreate(WebsiteBase):
    pass


class WebsiteUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    base_url: HttpUrl | None = None
    enabled: bool | None = None
    discovery_selector: str | None = Field(default=None, min_length=1, max_length=512)
    title_selector: str | None = Field(default=None, max_length=512)
    description_selector: str | None = Field(default=None, max_length=512)
    content_selector: str | None = Field(default=None, max_length=512)
    scrape_frequency_minutes: int | None = Field(default=None, ge=1, le=10080)


class WebsiteRead(WebsiteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    base_url: str
    created_at: datetime
    updated_at: datetime


class SelectorSuggestionRequest(BaseModel):
    base_url: HttpUrl


class SelectorSuggestionRead(BaseModel):
    discovery_selector: str = Field(min_length=1, max_length=512)
    title_selector: str = Field(min_length=1, max_length=512)
    description_selector: str = Field(min_length=1, max_length=512)
    content_selector: str = Field(min_length=1, max_length=512)


class ArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    website_id: int
    url: str
    title: str
    description: str
    content: str
    scraped_at: datetime
    created_at: datetime
    updated_at: datetime


class ScrapeJobCreate(BaseModel):
    website_id: int


class ScrapeJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    website_id: int
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    discovered_urls: list[str]
    saved_articles: int
    failure: str | None
    created_at: datetime
