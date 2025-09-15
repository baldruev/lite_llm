from dataclasses import dataclass

from project.keygen.schemas.users import CreateUserRequest
from project.keygen.repositories.team import TeamRepository
from project.keygen.utils.exceptions import KeyNotFoundError, UserNotFoundError
from project.keygen.repositories.users import UserRepository
from project.keygen.services.litellm import LiteLLMService
from project.keygen.repositories.keys import KeyRepository
from project.keygen.models.keys import Key as KeyModel
from project.keygen.schemas.keys import CreateKeyRequest, Key as KeySchema
from project.keygen.utils.logger import get_logger


logger = get_logger(__name__)


@dataclass
class KeyGenerationService:
    key_repository: KeyRepository
    user_repository: UserRepository
    team_repository: TeamRepository
    lite_llm_service: LiteLLMService

    async def _check_username(self, username: str) -> None:
        """Проверяет, существует ли пользователь с заданным username"""
        existing_user = await self.user_repository.get_user(username)
        if existing_user is None:
            logger.info(f"Пользователь {username} не найден")
            raise UserNotFoundError(f"Пользователь {username} не найден")

    async def _check_key(self, key: str) -> None:
        """Проверяет, существует ли ключ в базе"""
        existing_key = await self.key_repository.get_key_by_key_value(key)
        if existing_key is None:
            logger.info(f"Ключ {key} не найден")
            raise KeyNotFoundError(f"Ключ {key} не найден")

    async def generate_key(self, request: CreateKeyRequest) -> KeyModel:
        """Генерирует новый ключ для пользователя"""

        existing_user = await self.user_repository.get_user(request.username)
        # проверяем есть пользователь в БД, если нет создаем пользователя и ключ
        if existing_user is None:
            existing_team = await self.team_repository.get_team()
            if existing_team is None:
                new_team = await self.lite_llm_service.create_team()
                existing_team = await self.team_repository.create_team(new_team)

            user_data = CreateUserRequest(
                username=request.username,
                rpm_limit=request.rpm_limit,
                max_budget=request.max_budget,
                budget_duration=request.budget_duration,
                max_parallel_requests=request.max_parallel_requests,
                team_id=existing_team.team_id,
            )
            new_user = await self.lite_llm_service.create_user(user_data)
            existing_user = await self.user_repository.create_user(new_user)

        # проверяем есть ключ в БД, если нет создаем новый
        existing_key = await self.key_repository.get_key_by_username(existing_user.username)
        if existing_key is None:
            new_key = await self.lite_llm_service.generate_new_key(request)
            existing_key = await self.key_repository.create_key(new_key)

        return existing_key

    async def update_key(self, key: str) -> KeySchema:
        """
        Обновляет указанный ключ:
        - проверяет, существует ли он;
        - блокирует старый ключ в LiteLLM и в базе;
        - генерирует новый ключ и сохраняет его;
        Возвращает новый ключ.
        """
        await self._check_key(key)
        old_key = await self.key_repository.get_key_by_key_value(key)

        await self.lite_llm_service.block_key(old_key.key)
        await self.key_repository.block_key(old_key.key)

        new_key = await self.lite_llm_service.generate_new_key(
            CreateKeyRequest(
                username=old_key.username,
                rpm_limit=old_key.rpm_limit,
                max_budget=old_key.max_budget,
                budget_duration=old_key.budget_duration,
                max_parallel_requests=old_key.max_parallel_requests,
            )
        )

        updated_key = await self.key_repository.create_key(new_key)

        return updated_key

    async def validate_key(self, username: str) -> KeyModel | None:
        """
        Валидирует ключ по имени пользователя:
        - проверяет существование пользователя;
        - возвращает ключ пользователя, если он есть.
        """
        await self._check_username(username)
        validated_key = await self.key_repository.get_key_by_username(username)
        return validated_key

    async def block_key(self, key: str) -> bool:
        """
        Блокирует ключ:
        - проверяет существование ключа;
        - блокирует его в LiteLLM и в базе;
        - возвращает True, если блокировка успешна.
        """
        await self._check_key(key)
        await self.lite_llm_service.block_key(key)
        blocked_key = await self.key_repository.block_key(key)

        if blocked_key.blocked:
            return True

    async def get_key_info(self, key: str) -> KeyModel:
        """Возвращает подробную информацию о ключе"""
        await self._check_key(key)
        return await self.key_repository.get_key_by_key_value(key)
