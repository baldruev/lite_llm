from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker

from project.keygen.config import app_settings
from project.keygen.db.model_base import public_schema
from project.keygen.utils.logger import get_logger


logger = get_logger(__name__)


@lru_cache
def get_async_engine() -> AsyncEngine:
    dsn = (
        f"postgresql+asyncpg://"
        f"{app_settings.DB_USER}:"
        f"{app_settings.DB_PASSWORD}@"
        f"{app_settings.DB_HOST}:"
        f"{app_settings.DB_PORT}/"
        f"{app_settings.DB_NAME}"
    )
    return create_async_engine(
        dsn,
        echo=False,
        pool_pre_ping=True,
        max_overflow=10,
        pool_size=20,
        pool_recycle=3600,
    )


@lru_cache
def get_session_maker() -> sessionmaker:
    engine = get_async_engine()
    _session_maker = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    return _session_maker


async def init_database():
    try:
        async with get_async_engine().begin() as conn:
            await conn.run_sync(public_schema.create_all)
        logger.info("Инициализация базы данных прошла успешно")
    except Exception as e:
        logger.error(f"Инициализация базы данных завершилась с ошибкой: {str(e)}")
        raise
