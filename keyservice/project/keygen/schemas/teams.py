from pydantic import BaseModel, Field


class TeamRequest(BaseModel):
    team_alias: str = Field("default")


class TeamSchema(BaseModel):
    team_alias: str
    team_id: str
    created_at: str
    updated_at: str
