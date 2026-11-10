"""Database engine and session setup.

Uses SQLite locally so anyone can run the app with no setup. Set DATABASE_URL to a
Postgres URL (postgresql+psycopg://...) in deployed environments.
"""

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./paid_on_time.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields one session per request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
