from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def init_database(database_url: str) -> sessionmaker[Session]:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args)
    Base.metadata.create_all(bind=engine)
    _upgrade_schema(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _upgrade_schema(engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "websites" in tables:
        website_columns = {column["name"] for column in inspector.get_columns("websites")}
        if "target_topics" not in website_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE websites ADD COLUMN target_topics TEXT"))
    if "scrape_jobs" in tables:
        job_columns = {column["name"] for column in inspector.get_columns("scrape_jobs")}
        if "skipped_articles" not in job_columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE scrape_jobs ADD COLUMN skipped_articles INTEGER NOT NULL DEFAULT 0")
                )


def get_session(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
