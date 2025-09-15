from dataclasses import dataclass
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError


from project.keygen.utils.exceptions import (
    KeyBlockError,
    KeyCreateError,
    KeyNotFoundError,
    KeyRepositoryError,
)
from project.keygen.models.keys import Key as KeyModel
from project.keygen.schemas.keys import Key as KeySchema
from project.keygen.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class KeyRepository:
    """Репозиторий для работы с ключами"""

    session: AsyncSession

    async def create_key(self, key_data: KeySchema) -> KeyModel:
        """Создать новый ключ"""
        try:
            obj_data = key_data.model_dump()

            db_key = KeyModel(**obj_data)

            self.session.add(db_key)
            await self.session.commit()
            await self.session.refresh(db_key)

            logger.info(f"Ключ для пользователя: {db_key.username} создан в БД")

            return db_key

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise KeyCreateError(f"Ошибка создания ключа: {str(e)}")

    async def get_key_by_username(self, username: str) -> KeyModel:
        """Получить ключ пользователя по имени пользователя, только если не заблокирован"""
        try:
            result = await self.session.execute(
                select(KeyModel).where((KeyModel.username == username) & (KeyModel.blocked == False))  # noqa: E712
            )

            key = result.scalar_one_or_none()

            if key:
                logger.info(f"Ключ найден для пользователя: {username}")
                return key
            return key

        except SQLAlchemyError as e:
            raise KeyRepositoryError(f"Ошибка получения ключа для пользователя {username}: {str(e)}")

    async def get_key_by_key_value(self, key: str) -> KeyModel:
        """Получить ключ по значению ключа"""
        try:
            result = await self.session.execute(
                select(KeyModel).where((KeyModel.key == key) & (KeyModel.blocked == False))  # noqa: E712
            )
            key_db = result.scalar_one_or_none()

            return key_db

        except SQLAlchemyError as e:
            raise KeyRepositoryError(f"Ошибка получения ключа по значению {key}: {str(e)}")

    async def delete_key(self, key: str) -> None:
        """Удалить ключ пользователя"""
        try:
            result = await self.session.execute(delete(KeyModel).where(KeyModel.key == key))  # noqa: E712

            await self.session.commit()
            logger.info(f"Ключ: {key} был удален")
            return result.rowcount

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise KeyRepositoryError(f"Ошибка удаления ключа {key}: {str(e)}")

    async def block_key(self, key: str) -> KeyModel:
        """Заблокировать один ключ по его значению и вернуть обновлённый объект"""
        try:
            db_key = await self.get_key_by_key_value(key)
            if not db_key:
                raise KeyNotFoundError(f"Ключ {key} не найден")

            db_key.blocked = True

            await self.session.commit()
            await self.session.refresh(db_key)
            logger.info(f"Ключ: {key} был заблокирован")
            return db_key

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise KeyBlockError(f"Ошибка блокировки ключа {key}: {e}")
