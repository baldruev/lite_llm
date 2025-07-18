from datetime import datetime
from typing import Optional
from fastapi import HTTPException, Depends, Query, APIRouter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from project.keygen.db.orm_models import Key
from project.keygen.integrations.litellm import generate_litellm_key, block_litellm_key
from project.keygen.api.v1.schemas.schema import CreateKeyRequest, BlockKeyRequest
from project.keygen.db.session import get_async_session
from project.keygen.logger import get_logger


logger = get_logger(__name__)
router = APIRouter(tags=["Key Generation"])
# header_scheme = APIKeyHeader(name="X-Api-Key")


@router.post("/key/generate", summary="Генерация нового ключа", description="Создает новый ключ для пользователя с заданными параметрами")
async def generate_key(
    request: CreateKeyRequest,
    db: AsyncSession = Depends(get_async_session)
)-> dict[str, str]:
    """
    Генерирует новый ключ LiteLLM для указанного пользователя.

    Если пользователь уже имеет ключ, возвращает существующий ключ.

    Args:
        request (CreateKeyRequest): Запрос на создание ключа.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        Dict[str, str]: Сгенерированный ключ.

    Raises:
        HTTPException: 500 при ошибках генерации ключа или работы с БД.

    Examples:
        >>> Request
        {
            "username": "user1",
            "rpm_limit": 10,
            "max_budget": 1000,
            "budget_duration": "30d"
        }
        >>> Response
        {
            "key": "sk-1234567890abcdef"
        }
    """
    logger.info(f"Генерация ключа для пользователя: {request.username}")
    result = await db.execute(select(Key).where(Key.username == request.username))
    existing_key = result.scalars().first()
    if existing_key:
        return {"key": existing_key.key}

    litellm_data = await generate_litellm_key(
        username=request.username,
        rpm_limit=request.rpm_limit,
        max_budget=request.max_budget,
        budget_duration=request.budget_duration
    )

    try:
        key_entry = Key(
            username=litellm_data["user_id"],
            key=litellm_data["key"],
            rpm_limit=litellm_data["rpm_limit"],
            max_budget=litellm_data["max_budget"],
            budget_duration=litellm_data["budget_duration"],
            created_at=litellm_data["created_at"],
            updated_at=litellm_data["updated_at"]
        )
        db.add(key_entry)
        await db.commit()
        logger.info(f"Ключ успешно сгенерирован для пользователя: {request.username}")
        return {"key": litellm_data["key"]}
    except KeyError as e:
        logger.error(f"Отсутствует поле в ответе LiteLLM: {e}")
        raise HTTPException(status_code=500, detail="Некорректный ответ от LiteLLM")
    except ValueError as e:
        logger.error(f"Ошибка формата даты: {e}")
        raise HTTPException(status_code=500, detail="Ошибка формата даты от LiteLLM")

@router.post("/key/update", summary="Обновление ключа", description="Блокирует старый ключ и генерирует новый ключ пользователя")
async def update_key(
    request: BlockKeyRequest,
    db: AsyncSession = Depends(get_async_session)
) -> dict[str, str]:
    """
    Обновляет ключ LiteLLM пользователя, блокируя старый и генерируя новый.

    Args:
        request (BlockKeyRequest): Запрос на обновление ключа.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        Dict[str, str]: Новый сгенерированный ключ.

    Raises:
        HTTPException: 404 если ключ не найден.
        HTTPException: 500 при ошибках обновления ключа.

    Examples:
        >>> Request
        {
            "key": "sk-oldkey123456789",
            "username": "user1"
        }
        >>> Response
        {
            "key": "sk-newkey123456789"
        }
    """
    logger.info(f"Генерация нового ключа: {request.key} пользователю: {request.username}")
    result = await db.execute(select(Key).where(Key.key == request.key))
    key_entry = result.scalars().first()
    if not key_entry:
        raise HTTPException(status_code=404, detail="Ключ не найден")
    
    key_entry.blocked = True
    db.add(key_entry)

    await block_litellm_key(request.key)

    litellm_data = await generate_litellm_key(
        username=key_entry.username,
        rpm_limit=key_entry.rpm_limit,
        max_budget=key_entry.max_budget,
        budget_duration=key_entry.budget_duration
    )
    try:
        new_key_entry = Key(
            username=litellm_data["user_id"],
            key=litellm_data["key"],
            rpm_limit=litellm_data["rpm_limit"],
            max_budget=litellm_data["max_budget"],
            budget_duration=litellm_data["budget_duration"],
            created_at=litellm_data["created_at"],
            updated_at=litellm_data["updated_at"]
        )
        db.add(new_key_entry)
        
        await db.commit()
        logger.info(f"Ключ успешно передан пользователю: {request.username}")
        return {"key": litellm_data["key"]}
    except KeyError as e:
        logger.error(f"Отсутствует поле в ответе LiteLLM: {e}")
        raise HTTPException(status_code=500, detail="Некорректный ответ от LiteLLM")
    except ValueError as e:
        logger.error(f"Ошибка формата даты: {e}")
        raise HTTPException(status_code=500, detail="Ошибка формата даты от LiteLLM")

@router.get("/key/validate", summary="Проверка ключа", description="Проверяет наличие ключа у пользователя")
async def validate_key(
    username: str = Query(..., description="Длинная учетка пользователя для проверки"),
    db: AsyncSession = Depends(get_async_session)
) -> dict[str, Optional[str]]:
    """
    Проверяет наличие активного ключа LiteLLM у пользователя.

    Args:
        username (str): Имя пользователя для проверки.
        db (AsyncSession): Асинхронная сессия БД.

    Returns:
        Dict[str, Optional[str]]: Результат проверки.

    Examples:
        >>> Request
        GET /key/validate?username=user1

        >>> Response (key exists)
        {
            "has_key": True,
            "key_preview": "sk-123...456"
        }

        >>> Response (no key)
        {
            "has_key": False
        }
    """
    logger.info(f"Проверка ключа для пользователя: {username}")
    result = await db.execute(select(Key).where(Key.username == username))
    key_entry = result.scalars().first()
    if key_entry:
        key_preview = f"{key_entry.key[:5]}...{key_entry.key[-5:]}"
        return {"has_key": True, "key_preview": key_preview}
    return {"has_key": False}
