from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from project.keygen.utils.exceptions import TeamCreateError
from project.keygen.utils.logger import get_logger
from project.keygen.schemas.teams import TeamRequest
from project.keygen.models.teams import Team as TeamModel


logger = get_logger(__name__)


@dataclass
class TeamRepository:
    """Репозиторий для работы с ключами"""

    session: AsyncSession

    async def create_team(self, key_data: TeamRequest) -> TeamModel:
        """Создать новую команду"""
        try:
            obj_data = key_data.model_dump()

            db_key = TeamModel(**obj_data)

            self.session.add(db_key)
            await self.session.commit()
            await self.session.refresh(db_key)

            logger.info(f"Команда {db_key.team_alias} создана в БД")

            return db_key

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise TeamCreateError(f"Ошибка создания команды: {str(e)}")

    async def get_team(self, team_request: TeamRequest = TeamRequest()) -> TeamModel | None:
        """Получить команду по названию"""
        try:
            result = await self.session.execute(
                select(TeamModel).where(TeamModel.team_alias == team_request.team_alias)
            )
            team = result.scalar_one_or_none()
            return team
        except SQLAlchemyError as e:
            raise TeamCreateError(f"Ошибка поиска пользователя: {str(e)}")
