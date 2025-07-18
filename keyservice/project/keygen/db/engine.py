from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker

from project.keygen.container import app_settings
from project.keygen.db.model_base import public_schema
from project.keygen.logger import get_logger


logger = get_logger(__name__)


# Кэшируем движок и сессии
_async_engine: AsyncEngine | None = None
_session_maker: sessionmaker | None = None

def get_async_engine() -> AsyncEngine:
    global _async_engine
    if not _async_engine:
        return create_async_engine(
            "postgresql+asyncpg://"
            f"{app_settings.DB_USER}:"
            f"{app_settings.DB_PASSWORD}@"
            f"{app_settings.DB_HOST}:"
            f"{app_settings.DB_PORT}/"
            f"{app_settings.DB_NAME}",
            echo=False,
            pool_pre_ping=True,
            max_overflow=10,
            pool_size=20,
            pool_recycle=3600
        )

def get_session_maker() -> sessionmaker:
    global _session_maker
    if not _session_maker:
        engine = get_async_engine()
        _session_maker = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
    return _session_maker

async def init_database():
    try:
        async with get_async_engine().begin() as conn:
            await conn.run_sync(public_schema.create_all)
        logger.info("Инициализация базы данных прошла успешно")
    except Exception as e:
        logger.error(f"Инициализация базы данных завершилась с ошибкой: {str(e)}")
        raise