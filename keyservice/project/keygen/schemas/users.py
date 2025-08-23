from pydantic import BaseModel, Field


class User(BaseModel):
    username: str


class CreateUserRequest(BaseModel):
    username: str
    rpm_limit: int = Field(2, description="Ограничение запросов в минуту")
    max_budget: float = Field(50.0, description="Максимальный бюджет за период")
    budget_duration: str = Field("30d", description="Длительность бюджета, например, '30d'")
    max_parallel_requests: int = Field(1, description="Максимум параллельных запросов")
    team_id: str
