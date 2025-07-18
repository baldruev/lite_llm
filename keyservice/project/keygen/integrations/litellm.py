import httpx
import json
from fastapi import HTTPException
from project.keygen.container import app_settings
from project.keygen.logger import get_logger


logger = get_logger(__name__)

async def generate_litellm_key(
    username: str,
    rpm_limit: int = None,
    max_budget: float = None,
    budget_duration: str = None
) -> dict:
    headers = {"Authorization": f"Bearer {app_settings.MASTER_KEY}"}
    data = {"user_id": username}
    if rpm_limit is not None:
        data["rpm_limit"] = rpm_limit
    if max_budget is not None:
        data["max_budget"] = max_budget
    if budget_duration is not None:
        data["budget_duration"] = budget_duration

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{app_settings.LITELLM_URL}/key/generate",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Ошибка LiteLLM: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=500, detail=f"Ошибка LiteLLM: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Сетевая ошибка: {e}")
            raise HTTPException(status_code=500, detail="Ошибка сети при запросе к LiteLLM")
        except json.JSONDecodeError:
            logger.error("Некорректный JSON в ответе от LiteLLM")
            raise HTTPException(status_code=500, detail="Некорректный ответ от LiteLLM")

async def block_litellm_key(key: str) -> dict:
    headers = {"Authorization": f"Bearer {app_settings.MASTER_KEY}"}
    data = {"key": key}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{app_settings.LITELLM_URL}/key/block",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Ошибка LiteLLM: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=500, detail=f"Ошибка LiteLLM: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Сетевая ошибка: {e}")
            raise HTTPException(status_code=500, detail="Ошибка сети при запросе к LiteLLM")