from pydantic import BaseModel


class User(BaseModel):
    username: str


class CreateUserRequest(BaseModel):
    username: str
    team_id: str
