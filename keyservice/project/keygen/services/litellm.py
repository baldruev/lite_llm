import httpx
import json

from fastapi import HTTPException

from project.keygen.schemas.teams import TeamRequest, TeamSchema
from project.keygen.schemas.users import CreateUserRequest, User
from project.keygen.schemas.keys import CreateKeyRequest, Key
from project.keygen.config import app_settings
from project.keygen.utils.logger import get_logger


logger = get_logger(__name__)


class LiteLLMService:
    async def create_user(
        self,
        request: CreateUserRequest,
    ) -> User:
        headers = {"Authorization": f"Bearer {app_settings.MASTER_KEY}"}
        data = {"user_id": request.username, "auto_create_key": False, "user_email": request.username + "@megafon.ru"}

        if request.team_id is not None:
            data["team_id"] = request.team_id

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{app_settings.LITELLM_URL}/user/new", headers=headers, json=data)
                response.raise_for_status()
                response_data = response.json()
                logger.info(f"Пользователь {response_data.get('user_id', 'unknown')} создан в LiteLLM")
                return User(username=response_data.get("user_id"))
            except httpx.HTTPStatusError as e:
                logger.error(f"Ошибка LiteLLM: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=500, detail=f"Ошибка LiteLLM: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Сетевая ошибка: {e}")
                raise HTTPException(status_code=500, detail="Ошибка сети при запросе к LiteLLM")
            except json.JSONDecodeError:
                logger.error("Некорректный JSON в ответе от LiteLLM")
                raise HTTPException(status_code=500, detail="Некорректный ответ от LiteLLM")

    async def create_team(
        self,
        request: TeamRequest,
    ) -> TeamSchema:
        headers = {"Authorization": f"Bearer {app_settings.MASTER_KEY}"}
        data = {"team_alias": request.team_alias}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{app_settings.LITELLM_URL}/team/new", headers=headers, json=data)
                response.raise_for_status()
                response_data = response.json()
                logger.info(f"Команда {response_data.get('team_alias')} создана в LiteLLM")
                return TeamSchema(
                    team_alias=response_data.get("team_alias"),
                    team_id=response_data.get("team_id"),
                    blocked=response_data.get("blocked"),
                    created_at=response_data.get("created_at"),
                    updated_at=response_data.get("updated_at"),
                )
            except httpx.HTTPStatusError as e:
                logger.error(f"Ошибка LiteLLM: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=500, detail=f"Ошибка LiteLLM: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Сетевая ошибка: {e}")
                raise HTTPException(status_code=500, detail="Ошибка сети при запросе к LiteLLM")
            except json.JSONDecodeError:
                logger.error("Некорректный JSON в ответе от LiteLLM")
                raise HTTPException(status_code=500, detail="Некорректный ответ от LiteLLM")

    async def generate_new_key(
        self,
        request: CreateKeyRequest,
    ) -> Key:
        headers = {"Authorization": f"Bearer {app_settings.MASTER_KEY}"}

        # Формируем models как список, чтобы не получился вложенный список
        if isinstance(request.models, list):
            models_value = request.models
        else:
            models_value = [request.models] if request.models is not None else []

        data = {
            "user_id": request.username,
            "key_type": request.key_type,
            "models": models_value,
        }
        if request.rpm_limit is not None:
            data["rpm_limit"] = request.rpm_limit
        if request.tpm_limit is not None:
            data["tpm_limit"] = request.tpm_limit
        if request.max_budget is not None:
            data["max_budget"] = request.max_budget
        if request.budget_duration is not None:
            data["budget_duration"] = request.budget_duration
        if request.max_parallel_requests is not None:
            data["max_parallel_requests"] = request.max_parallel_requests

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{app_settings.LITELLM_URL}/key/generate", headers=headers, json=data)
                response.raise_for_status()
                response_data = response.json()
                logger.info(f"Ключ сгенерирован в LiteLLM пользователю: {response_data.get('user_id', 'unknown')}")
                return Key(
                    username=response_data.get("user_id"),
                    key=response_data.get("key"),
                    rpm_limit=response_data.get("rpm_limit"),
                    tpm_limit=response_data.get("tpm_limit"),
                    max_budget=response_data.get("max_budget"),
                    budget_duration=response_data.get("budget_duration"),
                    max_parallel_requests=response_data.get("max_parallel_requests"),
                    expiration_date=response_data.get("expiration_date"),
                    models=response_data.get("models"),
                    key_type=response_data.get("key_type"),
                    blocked=False,
                    created_at=response_data.get("created_at"),
                    updated_at=response_data.get("updated_at"),
                )
            except httpx.HTTPStatusError as e:
                logger.error(f"Ошибка LiteLLM: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=500, detail=f"Ошибка LiteLLM: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Сетевая ошибка: {e}")
                raise HTTPException(status_code=500, detail="Ошибка сети при запросе к LiteLLM")
            except json.JSONDecodeError:
                logger.error("Некорректный JSON в ответе от LiteLLM")
                raise HTTPException(status_code=500, detail="Некорректный ответ от LiteLLM")

    async def block_key(self, key: str) -> dict:
        headers = {"Authorization": f"Bearer {app_settings.MASTER_KEY}"}
        data = {"key": key}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{app_settings.LITELLM_URL}/key/block", headers=headers, json=data)
                response_data = response.json()
                logger.info(f"Ключ {response_data.get('key')} заблокирован в LiteLLM")
                return response_data
            except httpx.HTTPStatusError as e:
                logger.error(f"Ошибка LiteLLM: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=500, detail=f"Ошибка LiteLLM: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Сетевая ошибка: {e}")
                raise HTTPException(status_code=500, detail="Ошибка сети при запросе к LiteLLM")
