from pydantic import BaseModel, Field


class CreateKeyRequest(BaseModel):
    username: str
    rpm_limit: int = Field(2, description="Ограничение запросов в минуту")
    max_budget: float = Field(50.0, description="Максимальный бюджет за период")
    budget_duration: str = Field("30d", description="Длительность бюджета, например, '30d'")
    max_parallel_requests: int = Field(1, description="Максимум параллельных запросов")


class OnlyKeySchema(BaseModel):
    key: str


class ValidateKeyResponse(BaseModel):
    has_key: bool
    key_preview: str | None = None


class Key(BaseModel):
    username: str
    key: str
    rpm_limit: int = None
    max_budget: float = None
    budget_duration: str = None
    max_parallel_requests: int | None = None
    expiration_date: str | None = None
    blocked: bool
    created_at: str
    updated_at: str
