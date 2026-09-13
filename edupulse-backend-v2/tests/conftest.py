"""
Pytest configuration.
Sets mandatory environment variables before any app module is imported.
"""
import os
# Set required env vars before importing app modules
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-minimum-32-characters-ok")
os.environ.setdefault("HMAC_SECRET", "test-hmac-secret-minimum16")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("LLM_ENABLED", "false")
os.environ.setdefault("APP_ENV", "test")

import asyncio
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import create_app
from app.db.session import Base, get_db
from app.core.security import hash_password
from app.models.user import User
from app.models.faculty import FacultyProfile

# ── Test database (SQLite in-memory) ─────────────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.execute(text("ATTACH DATABASE ':memory:' AS registry"))
        await conn.execute(text("ATTACH DATABASE ':memory:' AS feedback"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(test_engine):
    """AsyncClient with overridden DB dependency."""
    session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def student_user(db_session: AsyncSession):
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        role="student",
        name="Test Student",
        email=f"student-{uid[:8]}@test.com",
        hashed_password=hash_password("TestPass@123"),
        is_active=True,
        dept="Computer Science",
        college="Test College",
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def faculty_user(db_session: AsyncSession):
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        role="faculty",
        name="Test Faculty",
        email=f"faculty-{uid[:8]}@test.com",
        hashed_password=hash_password("TestPass@123"),
        is_active=True,
        dept="Computer Science",
        college="Test College",
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def faculty_profile(db_session: AsyncSession, faculty_user: User):
    pid = str(uuid.uuid4())
    profile = FacultyProfile(
        id=pid,
        user_id=faculty_user.id,
        faculty_code=f"FAC-{pid[:6]}",
        name=faculty_user.name,
        dept="Computer Science",
        subject="Data Structures",
        college="Test College",
        university="KTU",
        response_count=0,
        dimension_scores_json="{}",
        score_trend_json="[]",
    )
    db_session.add(profile)
    await db_session.commit()
    return profile
