from pydantic import BaseModel


class CreateKeyRequest(BaseModel):
    username: str
    rpm_limit: int | None = None
    tpm_limit: int | None = None
    max_budget: float | None = None
    budget_duration: str | None = None
    max_parallel_requests: int | None = None
    models: list[str] | None = None
    key_type: str | None = None


class OnlyKeySchema(BaseModel):
    key: str


class ValidateKeyResponse(BaseModel):
    has_key: bool
    key_preview: str | None = None


class Key(BaseModel):
    username: str
    key: str
    rpm_limit: int | None = None
    tpm_limit: int | None = None
    max_budget: float = None
    budget_duration: str = None
    max_parallel_requests: int | None = None
    models: list | None = None
    key_type: str | None = None
    expiration_date: str | None = None
    blocked: bool
    created_at: str
    updated_at: str
