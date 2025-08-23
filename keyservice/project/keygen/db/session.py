from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from project.keygen.db.engine import get_session_maker


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
