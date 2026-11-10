"""Shared pytest fixtures for service-layer tests.

Runs against a dedicated ``milkshake_test`` database in the same Postgres
container as dev. To avoid pytest-asyncio event-loop scoping issues with
asyncpg's connection pool, the engine is recreated per test and uses
``NullPool``. Schema is dropped and rebuilt for full isolation — slow but
deterministic.
"""

from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.models import admin, drink, drink_image, item_master, order  # noqa: F401
from app.db import get_db
from app.main import app
from app.models.admin import Admin
from app.models.base import Base
from app.realtime import InMemoryBroadcaster, set_broadcaster
from app.utils.security import create_access_token, hash_password

TEST_DB_NAME = "milkshake_test"


def _make_test_url() -> str:
    s = get_settings()
    return (
        f"postgresql+asyncpg://{s.POSTGRES_USER}:{s.POSTGRES_PASSWORD}"
        f"@{s.POSTGRES_SERVER}:{s.POSTGRES_PORT}/{TEST_DB_NAME}"
    )


async def _ensure_test_database() -> None:
    """Create ``milkshake_test`` once if it does not exist (idempotent)."""
    s = get_settings()
    admin_url = (
        f"postgresql+asyncpg://{s.POSTGRES_USER}:{s.POSTGRES_PASSWORD}"
        f"@{s.POSTGRES_SERVER}:{s.POSTGRES_PORT}/postgres"
    )
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as conn:
            try:
                await conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
            except ProgrammingError:
                pass
    finally:
        await engine.dispose()


@pytest.fixture(autouse=True)
def in_memory_broadcaster() -> Iterator[InMemoryBroadcaster]:
    """Tests never touch Redis, even when the container sets REDIS_URL."""
    broadcaster = InMemoryBroadcaster()
    set_broadcaster(broadcaster)
    yield broadcaster
    set_broadcaster(None)


@pytest_asyncio.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Fresh schema per test. Hands out a factory so a test can open several
    independent sessions, which is what the concurrency tests need."""
    await _ensure_test_database()
    engine = create_async_engine(_make_test_url(), poolclass=NullPool)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.execute(text("DROP TYPE IF EXISTS drink_type"))
            await conn.execute(text("DROP TYPE IF EXISTS order_status"))
        await engine.dispose()


@pytest_asyncio.fixture
async def session(session_factory) -> AsyncIterator[AsyncSession]:
    async with session_factory() as s:
        yield s


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    """HTTP client against the real app, wired to the test database."""

    async def _test_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = _test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_headers(session) -> dict[str, str]:
    admin = Admin(
        email="staff@example.com",
        password_hash=hash_password("Password123"),
        is_active=True,
    )
    session.add(admin)
    await session.commit()
    token, _ = create_access_token(admin.id)
    return {"Authorization": f"Bearer {token}"}
