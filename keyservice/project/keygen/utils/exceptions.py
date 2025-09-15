class KeyRepositoryError(Exception):
    """Базовое исключение для ошибок репозитория"""


class KeyNotFoundError(KeyRepositoryError):
    """Ключ не найден"""


class KeyUpdateError(KeyRepositoryError):
    """Ошибка обновления ключа"""


class KeyCreateError(KeyRepositoryError):
    """Ошибка создания ключа"""


class KeyBlockError(KeyRepositoryError):
    """Ошибка блокировки ключа"""


class UserRepositoryError(Exception):
    """Базовое исключение для ошибок репозитория"""


class UserCreateError(UserRepositoryError):
    """Ошибка создания пользователя"""


class UserNotFoundError(UserRepositoryError):
    """Ошибка создания пользователя"""


class TeamRepositoryError(Exception):
    """Базовое исключение для ошибок репозитория"""


class TeamCreateError(TeamRepositoryError):
    """Ошибка создания пользователя"""
