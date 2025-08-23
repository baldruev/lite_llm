from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from project.keygen.api.v1.routes.keys import router
from project.keygen.db.engine import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - инициализация базы данных
    await init_database()
    yield


app = FastAPI(
    title="Сервис генерации ключей LiteLLM",
    description="API для генерации, передачи и проверки ключей с интеграцией LiteLLM",
    version="1.0.0",
    lifespan=lifespan,
    # root_path=app_settings.ROOT_PATH
)

app.include_router(router)


@app.get("/manage/health")
async def health_check():
    return JSONResponse(content={"status": "ok"}, status_code=200)
