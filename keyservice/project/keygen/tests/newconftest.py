import asyncio
from collections.abc import AsyncGenerator, Generator
import os
from datetime import datetime
from typing import Literal
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer


os.environ["APP_PORT"] = "8000"
os.environ["LITELLM_URL"] = ""
os.environ["MASTER_KEY"] = ""
os.environ["DB_SCHEMA"] = ""
os.environ["DB_USER"] = ""
os.environ["DB_PASSWORD"] = ""
os.environ["DB_HOST"] = ""
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = ""


from project.keygen.repositories.keys import KeyRepository
from project.keygen.db.model_base import Base
from project.keygen.main import app
from project.keygen.db.session import get_async_session


@pytest_asyncio.fixture
def event_loop():
    """Создает event loop для всей сессии тестирования"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
def anyio_backend() -> Literal["asyncio"]:
    return "asyncio"


@pytest_asyncio.fixture
def postgres_container(
    anyio_backend: Literal["asyncio"],
) -> Generator[PostgresContainer, None, None]:
    with PostgresContainer("postgres:15", driver="asyncpg") as postgres:
        yield postgres


@pytest_asyncio.fixture
async def async_session(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[AsyncSession, None]:
    db_url = postgres_container.get_connection_url()
    async_engine = create_async_engine(db_url)

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        bind=async_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with async_session() as session:
        yield session

    await async_engine.dispose()


@pytest_asyncio.fixture
async def async_client(
    async_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_async_session] = lambda: async_session
    _transport = ASGITransport(app=app)

    async with AsyncClient(transport=_transport, base_url="http://test", follow_redirects=True) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def key_repository(async_session):
    """Фикстура для создания репозитория ключей"""
    return KeyRepository(session=async_session)


@pytest_asyncio.fixture
def mock_litellm_requests():
    """Мокирует запросы к LiteLLM API"""

    with patch("project.keygen.api.v1.routes.keys.generate_litellm_key", new=AsyncMock()) as mock_generate:
        mock_generate.return_value = {
            "key": "sk-test-key-123456789",
            "user_id": "test_user",
            "rpm_limit": 100,
            "max_budget": 50.0,
            "budget_duration": "monthly",
            "max_parallel_requests": 5,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        yield mock_generate


@pytest_asyncio.fixture
def mock_block_litellm():
    """Мокирует блокировку ключа LiteLLM"""
    with patch("project.keygen.api.v1.routes.keys.block_litellm_key", new=AsyncMock()) as mock_block:
        mock_block.return_value = None
        yield mock_block
