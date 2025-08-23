from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from project.keygen.utils.logger import get_logger
from project.keygen.utils.exceptions import UserCreateError
from project.keygen.models.users import User as UserModel
from project.keygen.schemas.users import User as UserSchema


logger = get_logger(__name__)


@dataclass
class UserRepository:
    """Репозиторий для работы с пользователями"""

    session: AsyncSession

    async def get_user(self, username: str) -> UserModel | None:
        """Получить пользователя по имени пользователя"""
        try:
            result = await self.session.execute(select(UserModel).where(UserModel.username == username).limit(1))
            user = result.scalar_one_or_none()
            return user
        except SQLAlchemyError as e:
            raise UserCreateError(f"Ошибка поиска пользователя: {str(e)}")

    async def create_user(self, user_data: UserSchema) -> UserModel:
        """Создать нового пользователя"""
        try:
            existing_user = await self.get_user(user_data.username)
            if existing_user:
                logger.info(f"Пользователь {existing_user.username} найден в БД")
                return existing_user

            obj_data = user_data.model_dump()

            db_user = UserModel(**obj_data)

            self.session.add(db_user)
            await self.session.commit()
            await self.session.refresh(db_user)

            logger.info(f"Пользователь {db_user.username} создан в БД")

            return db_user

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise UserCreateError(f"Ошибка создания ключа: {str(e)}")
