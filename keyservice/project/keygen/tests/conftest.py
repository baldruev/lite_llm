import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from testcontainers.postgres import PostgresContainer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


os.environ["APP_PORT"] = "8000"
os.environ["LITELLM_URL"] = ""
os.environ["MASTER_KEY"] = ""
os.environ["DB_SCHEMA"] = ""
os.environ["DB_USER"] = ""
os.environ["DB_PASSWORD"] = ""
os.environ["DB_HOST"] = ""
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = ""


from project.keygen.repositories.team import TeamRepository
from project.keygen.repositories.users import UserRepository
from project.keygen.repositories.keys import KeyRepository
from project.keygen.db.model_base import Base
from project.keygen.main import app
from project.keygen.db.session import get_async_session
from project.keygen.config import app_settings
from project.keygen.models.keys import Key
from project.keygen.schemas.keys import Key as KeySchema


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Создает event loop для всей сессии тестирования"""
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
def postgres_container():
    """Запускает контейнер PostgreSQL для тестов"""
    with PostgresContainer("postgres:15-alpine") as container:
        container.get_connection_url()

        app_settings.DB_SCHEMA = "postgresql"
        app_settings.DB_USER = container.username
        app_settings.DB_PASSWORD = container.password
        app_settings.DB_HOST = container.get_container_host_ip()
        app_settings.DB_PORT = container.get_exposed_port(5432)
        app_settings.DB_NAME = container.dbname

        yield container


@pytest_asyncio.fixture(scope="session", autouse=True)
def create_test_database(postgres_container, event_loop):
    """Создает и удаляет таблицы в тестовой БД"""

    async def setup_database():
        async_engine = create_async_engine(
            f"postgresql+asyncpg://{postgres_container.username}:{postgres_container.password}"
            f"@{postgres_container.get_container_host_ip()}:{postgres_container.get_exposed_port(5432)}"
            f"/{postgres_container.dbname}",
            echo=True,
        )

        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        except Exception:
            raise
        finally:
            await async_engine.dispose()

    # Запускаем создание БД
    event_loop.run_until_complete(setup_database())

    yield

    async def cleanup_database():
        async_engine = create_async_engine(
            f"postgresql+asyncpg://{postgres_container.username}:{postgres_container.password}"
            f"@{postgres_container.get_container_host_ip()}:{postgres_container.get_exposed_port(5432)}"
            f"/{postgres_container.dbname}",
            echo=True,
        )

        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        finally:
            await async_engine.dispose()

    event_loop.run_until_complete(cleanup_database())


@pytest_asyncio.fixture
async def db_session(postgres_container, create_test_database):
    """Создает новую асинхронную сессию БД для каждого теста"""
    async_engine = create_async_engine(
        f"postgresql+asyncpg://{postgres_container.username}:{postgres_container.password}"
        f"@{postgres_container.get_container_host_ip()}:{postgres_container.get_exposed_port(5432)}"
        f"/{postgres_container.dbname}",
        echo=False,
    )

    # async_session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_engine.connect() as connection:
        transaction = await connection.begin()

        session = AsyncSession(bind=connection, join_transaction_mode="create_savepoint")

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()
            await connection.close()

    await async_engine.dispose()


@pytest_asyncio.fixture
async def async_client(db_session):
    """Создает асинхронный HTTP клиент с переопределенной БД"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def key_repository(db_session):
    """Фикстура для создания репозитория ключей"""
    return KeyRepository(session=db_session)


@pytest_asyncio.fixture
async def user_repository(db_session):
    """Фикстура для создания репозитория ключей"""
    return UserRepository(session=db_session)


@pytest_asyncio.fixture
async def team_repository(db_session):
    """Фикстура для создания репозитория ключей"""
    return TeamRepository(session=db_session)


# Фикстура для создания валидного ключа
@pytest_asyncio.fixture
async def valid_key_data() -> KeySchema:
    return KeySchema(
        username="test_user",
        key="sk-test-key-123456789",
        rpm_limit=100,
        max_budget=500.0,
        budget_duration="30d",
        max_parallel_requests=10,
        expiration_date=str(datetime.now() + timedelta(days=30)),
        blocked=False,
        created_at=str(datetime.now()),
        updated_at=str(datetime.now()),
    )


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


class KeyFactory:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_key(self, username="test_user", **kwargs):
        key = Key(
            username=username,
            key=f"sk-{username}-{os.urandom(4).hex()}",
            rpm_limit=kwargs.get("rpm_limit", 100),
            max_budget=kwargs.get("max_budget", 50.0),
            budget_duration=kwargs.get("budget_duration", "30d"),
            max_parallel_requests=kwargs.get("max_parallel_requests", 5),
            expiration_date=kwargs.get("expiration_date", str(datetime.now() + timedelta(30))),
            blocked=kwargs.get("blocked", False),
            created_at=kwargs.get("created_at", str(datetime.now())),
            updated_at=kwargs.get("updated_at", str(datetime.now())),
        )
        self.session.add(key)
        await self.session.commit()
        await self.session.refresh(key)
        return key

    async def get_key_by_key(self, key: str):
        """Получает ключ по значению ключа"""
        result = await self.session.execute(select(Key).where(Key.key == key))
        return result.scalars().first()


@pytest_asyncio.fixture
async def key_factory(db_session):
    """Фабрика для создания тестовых ключей в БД"""
    return KeyFactory(db_session)
