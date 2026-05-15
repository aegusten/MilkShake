"""Shared pytest fixtures for service-layer tests.

Runs against a dedicated ``milkshake_test`` database in the same Postgres
container as dev. To avoid pytest-asyncio event-loop scoping issues with
asyncpg's connection pool, the engine is recreated per test and uses
``NullPool``. Schema is dropped and rebuilt for full isolation — slow but
deterministic.
"""

from collections.abc import AsyncIterator

import pytest_asyncio
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
from app.models.base import Base

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


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    await _ensure_test_database()
    engine = create_async_engine(_make_test_url(), poolclass=NullPool)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as s:
            yield s
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.execute(text("DROP TYPE IF EXISTS drink_type"))
        await engine.dispose()
