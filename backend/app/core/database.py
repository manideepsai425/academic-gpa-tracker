"""
SQLAlchemy engine, session factory, and the declarative base every
model inherits from.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# pool_pre_ping guards against Render's Postgres (and free-tier instances
# generally) silently closing idle connections — without this, the first
# query after a period of inactivity would raise a stale-connection error
# instead of transparently reconnecting.
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a database session and guarantees
    it's closed after the request, even if an exception is raised."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
