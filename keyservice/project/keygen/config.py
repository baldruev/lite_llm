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

    RPM_LIMIT: int = 100
    TPM_LIMIT: int = 200000
    MAX_BUDGET: float = 50.0
    BUDGET_DURATION: str = "30d"
    MAX_PARALLEL_REQUESTS: int = 2
    MODELS: list = ["general-models"]
    KEY_TYPE: str = "llm_api"

    TEAM_ALIAS: str = "default"


app_settings = Settings()
