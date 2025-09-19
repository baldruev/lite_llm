from fastapi import Depends, Query, APIRouter, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from project.keygen.repositories.team import TeamRepository
from project.keygen.utils.exceptions import KeyNotFoundError, UserNotFoundError
from project.keygen.repositories.keys import KeyRepository
from project.keygen.repositories.users import UserRepository
from project.keygen.services.keygen import KeyGenerationService
from project.keygen.services.litellm import LiteLLMService
from project.keygen.schemas.keys import CreateKeyRequest, OnlyKeySchema, Key, ValidateKeyResponse
from project.keygen.db.session import get_async_session
from project.keygen.utils.logger import get_logger


logger = get_logger(__name__)
router = APIRouter(tags=["Key Generation"])


async def get_key_generation_service(db: AsyncSession = Depends(get_async_session)) -> KeyGenerationService:
    """
    Зависимость для сервиса генерации ключей.

    Args:
        db: Асинхронная сессия базы данных

    Returns:
        KeyGenerationService: Экземпляр сервиса генерации ключей
    """
    lite_llm_service = LiteLLMService()
    key_repo = KeyRepository(session=db)
    user_repo = UserRepository(session=db)
    team_repo = TeamRepository(session=db)
    return KeyGenerationService(
        key_repository=key_repo,
        user_repository=user_repo,
        team_repository=team_repo,
        lite_llm_service=lite_llm_service,
    )


@router.post(
    "/api/v1/key/generate",
    response_model=OnlyKeySchema,
    status_code=status.HTTP_201_CREATED,
    summary="Генерация нового ключа",
    description="Создает новый ключ для пользователя с заданными параметрами",
    responses={
        201: {"description": "Ключ успешно создан"},
        400: {"description": "Неверные параметры запроса"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
async def generate_key(
    request: CreateKeyRequest, service: KeyGenerationService = Depends(get_key_generation_service)
) -> OnlyKeySchema:
    """
    Endpoint для генерации нового API-ключа.

    Args:
        request: Данные для создания ключа (username, параметры лимитов)
        service: Сервис генерации ключей

    Returns:
        dict[str, str]: Словарь с новым сгенерированным ключом

    Raises:
        HTTPException: При ошибках валидации или создания ключа

    Example:
        >>> Request Body:
        {
            "username": "user123",
            "rpm_limit": 100,
            "max_budget": 50.0,
            "budget_duration": "30d",
            "max_parallel_requests": 1
        }
        >>> Response:
        {
            "key": "sk-newkey123456789abcdef"
        }
    """
    try:
        logger.info(f"Генерация ключа для пользователя: {request.username}")

        # Валидация входных данных
        if not request.username or not request.username.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username не может быть пустым")

        new_key = await service.generate_key(request)

        logger.info(f"Ключ успешно передан для пользователя: {request.username}")
        return {"key": new_key.key}

    except ValueError as e:
        logger.error(f"Ошибка валидации при генерации ключа: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ошибка валидации: {str(e)}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при генерации ключа: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка при создании ключа"
        )


@router.post(
    "/api/v1/key/update",
    response_model=dict[str, str],
    summary="Обновление ключа",
    description="Блокирует старый ключ и генерирует новый ключ пользователя",
    responses={
        200: {"description": "Ключ успешно обновлен"},
        404: {"description": "Ключ не найден"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
async def update_key(
    request: OnlyKeySchema, service: KeyGenerationService = Depends(get_key_generation_service)
) -> OnlyKeySchema:
    """
    Обновляет ключ LiteLLM пользователя, блокируя старый и генерируя новый.

    Args:
        request: Данные запроса с ключом для блокировки
        service: Сервис генерации ключей

    Returns:
        dict[str, str]: Новый сгенерированный ключ

    Raises:
        HTTPException: При ошибках поиска или обновления ключа

    Example:
        >>> Request Body:
        {
            "key": "sk-oldkey123456789",
        }
        >>> Response:
        {
            "key": "sk-newkey123456789"
        }
    """
    try:
        logger.info(f"Обновление ключа: {request.key[:10]}...")

        if not request.key or not request.key.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ключ не может быть пустым")

        updated_key = await service.update_key(request.key)

        if not updated_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ключ не найден или не может быть обновлен"
            )

        logger.info("Ключ успешно обновлен")
        return {"key": updated_key.key}

    except KeyNotFoundError as e:
        logger.error(f"Ошибка обновления ключа: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обновлении ключа: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка при обновлении ключа"
        )


@router.get(
    "/api/v1/key/validate",
    response_model=ValidateKeyResponse,
    summary="Проверка ключа",
    description="Проверяет наличие ключа у пользователя",
    responses={
        200: {"description": "Результат проверки ключа"},
        400: {"description": "Неверные параметры запроса"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
async def validate_key(
    username: str = Query(..., description="Имя пользователя для проверки", min_length=1),
    service: KeyGenerationService = Depends(get_key_generation_service),
) -> ValidateKeyResponse:
    """
    Проверяет наличие активного ключа LiteLLM у пользователя.

    Args:
        username: Имя пользователя для проверки
        service: Сервис генерации ключей

    Returns:
        ValidateKeyResponse: Результат проверки с информацией о ключе

    Raises:
        HTTPException: При ошибках валидации или проверки

    Example:
        >>> Request:
        GET /key/validate?username=user1

        >>> Response (key exists):
        {
            "has_key": true,
            "key_preview": "sk-123...456"
        }

        >>> Response (no key):
        {
            "has_key": false
        }
    """
    try:
        logger.info(f"Проверка ключа для пользователя: {username}")

        key_entry = await service.validate_key(username)

        if key_entry:
            return ValidateKeyResponse(has_key=True, key_preview=key_entry.key)

        return ValidateKeyResponse(has_key=False)

    except UserNotFoundError as e:
        logger.error(f"Ошибка проверки ключа: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при проверки ключа: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка при проверки ключа"
        )


@router.delete(
    "/api/v1/key/delete",
    response_model=dict[str, str],
    summary="Удаление ключа",
    description="Удаляет (блокирует) ключ пользователя в системе и LiteLLM",
    responses={
        200: {"description": "Ключ успешно удален"},
        400: {"description": "Неверные параметры запроса"},
        404: {"description": "Ключ не найден"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
async def delete_key(
    request: OnlyKeySchema, service: KeyGenerationService = Depends(get_key_generation_service)
) -> dict[str, str]:
    """
    Удаляет ключ LiteLLM пользователя, блокируя его в системе и LiteLLM.

    Args:
        request: Данные запроса с ключом для удаления
        service: Сервис генерации ключей

    Returns:
        dict[str, str]: Сообщение об успешном удалении

    Raises:
        HTTPException: При ошибках поиска или удаления ключа

    Example:
        >>> Request Body:
        {
            "key": "sk-key123456789"
        }
        >>> Response:
        {
            "message": "Ключ успешно удален"
        }
    """
    try:
        logger.info(f"Удаление ключа: {request.key[:10]}...")

        if not request.key or not request.key.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ключ не может быть пустым")

        blocked_key = await service.block_key(request.key)

        if blocked_key is True:
            logger.info("Ключ успешно удален")
            return {"message": "Ключ успешно удален"}
        else:
            logger.warning(f"Не удалось удалить ключ: {request.key[:10]}...")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ключ не найден или уже заблокирован")

    except KeyNotFoundError as e:
        logger.error(f"Ошибка удаления ключа: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при удалении ключа: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка при удалении ключа"
        )


@router.get(
    "/api/v1/key/info",
    response_model=Key,
    summary="Получение информации о ключе",
    description="Возвращает подробную информацию о ключе по его значению",
    responses={
        200: {"description": "Информация о ключе"},
        400: {"description": "Неверные параметры запроса"},
        404: {"description": "Ключ не найден"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
async def get_key_info(
    key: str = Query(..., description="API-ключ для получения информации", min_length=1),
    service: KeyGenerationService = Depends(get_key_generation_service),
) -> Key:
    """
    Возвращает подробную информацию о ключе по его значению.

    Args:
        key: API-ключ для получения информации
        service: Сервис генерации ключей

    Returns:
        Key: Полная информация о ключе

    Raises:
        HTTPException: При ошибках поиска ключа

    Example:
        >>> Request:
        GET /key/info?key=sk-key123456789

        >>> Response:
        {
            "username": "user123",
            "key": "sk-key123456789",
            "rpm_limit": 100,
            "max_budget": 50.0,
            "budget_duration": "30d",
            "blocked": false,
            "created_at": "2025-08-13T10:00:00Z",
            "updated_at": "2025-08-13T10:00:00Z"
        }
    """
    try:
        logger.info(f"Получение информации о ключе: {key[:10]}...")

        key_info = await service.get_key_info(key)

        logger.info("Информация о ключе получена успешно")
        return key_info

    except KeyNotFoundError as e:
        logger.error(f"Ошибка получения инфо о ключе: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении инфо о ключе: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка при получении инфо о ключе"
        )
