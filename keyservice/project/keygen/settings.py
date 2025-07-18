from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ROOT_PATH: str = None
    APP_PORT: int

    LITELLM_URL: str
    MASTER_KEY: str

    DB_SCHEMA: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str