from pydantic import BaseModel


class CreateKeyRequest(BaseModel):
    username: str
    rpm_limit: int = None
    max_budget: float = None
    budget_duration: str = None

class BlockKeyRequest(BaseModel):
    username: str
    key: str

class ValidateKeyResponse(BaseModel):
    has_key: bool
    key_preview: str = None