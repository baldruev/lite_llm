import asyncio
import uvicorn

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from project.keygen.api.v1.routers.keygen import router
from project.keygen.db.engine import init_database
from project.keygen.container import app_settings

app = FastAPI(
    title="Сервис управления ключами",
    description="API для генерации, передачи и проверки ключей с интеграцией LiteLLM",
    version="1.0.0"
)

app.include_router(router)

@app.get("/manage/health")
async def health_check():
    return JSONResponse(content={"status": "ok"},
    status_code=200)

def main():
    asyncio.run(init_database())
    uvicorn.run("project.keygen.api.app:app", host="0.0.0.0", port=app_settings.APP_PORT)