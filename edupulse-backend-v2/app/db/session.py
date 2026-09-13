"""
Async SQLAlchemy engine and session factory.
Uses asyncpg driver for PostgreSQL with connection pooling.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

_db_url = settings.async_database_url   # converts postgresql:// → postgresql+asyncpg://
_is_sqlite = _db_url.startswith("sqlite")

_pool_kwargs: dict = {}
if not _is_sqlite:
    _pool_kwargs = {
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "pool_pre_ping": True,
    }

engine = create_async_engine(
    _db_url,
    echo=settings.app_env == "development",
    **_pool_kwargs,
)

if _is_sqlite:
    from sqlalchemy import event

    @event.listens_for(engine.sync_engine, "connect")
    def _attach_sqlite_schemas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("ATTACH DATABASE 'edupulse_v2_registry.db' AS registry")
            cursor.execute("ATTACH DATABASE 'edupulse_v2_feedback.db' AS feedback")
        except Exception:
            pass
        finally:
            cursor.close()


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async DB session, always closed on exit."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager version for use outside FastAPI request context (e.g. tasks)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
