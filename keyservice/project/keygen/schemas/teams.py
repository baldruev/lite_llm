from pydantic import BaseModel


class TeamRequest(BaseModel):
    team_alias: str | None = None


class TeamSchema(BaseModel):
    team_alias: str
    team_id: str
    created_at: str
    updated_at: str
