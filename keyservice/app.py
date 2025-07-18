import json
from fastapi import FastAPI, HTTPException, Depends, Query, Header
from sqlalchemy import create_engine, Column, String, DateTime, Float, Boolean, Integer, JSON, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import os
import requests

# Настройка базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/keydb")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модель таблицы keys
class Key(Base):
    __tablename__ = 'keys'
    username = Column(String, primary_key=True)
    key = Column(String, unique=True)
    rpm_limit = Column(Integer)
    max_budget = Column(Float)
    budget_duration = Column(String)
    expiration_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Интеграция с LiteLLM
LITELLM_URL = "http://litellm:4000"
MASTER_KEY = "sk-1234"

def generate_litellm_key(username: str, rpm_limit: int = None, max_budget: float = None, budget_duration: str = None):
    headers = {"Authorization": f"Bearer {MASTER_KEY}"}
    data = {"user_id": username}
    if rpm_limit is not None:
        data["rpm_limit"] = rpm_limit

    if max_budget is not None:
        data["max_budget"] = max_budget
    
    if budget_duration is not None:
        data["budget_duration"] = budget_duration   

    response = requests.post(f"{LITELLM_URL}/key/generate", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=500, detail="Failed to generate key from LiteLLM")

def update_litellm_key(key: str, new_username: str):
    headers = {"Authorization": f"Bearer {MASTER_KEY}"}
    data = {"key": key, "user_id": new_username}
    response = requests.post(f"{LITELLM_URL}/key/update", headers=headers, json=data)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to update key in LiteLLM")

# FastAPI приложение
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Модели запросов и ответов
class CreateKeyRequest(BaseModel):
    username: str
    rpm_limit: int  = None
    max_budget: float  = None
    budget_duration: str  = None

class TransferKeyRequest(BaseModel):
    key: str
    new_username: str

class ValidateKeyResponse(BaseModel):
    has_key: bool
    key_preview: str = None

# Эндпоинты
@app.post("/key/generate")
def generate_key(
    request: CreateKeyRequest,
    db: Session = Depends(get_db)
):    
    # Проверка, есть ли ключ у пользователя
    existing_key = db.query(Key).filter(Key.username == request.username).first()
    if existing_key:
        raise HTTPException(status_code=400, detail="User already has a key")
    
    # Генерация ключа через LiteLLM
    litellm_data = generate_litellm_key(
        request.username, request.rpm_limit, request.max_budget, request.budget_duration
    )
    
    # Сохранение в базе
    key_entry = Key(
        username=litellm_data["user_id"],
        key=litellm_data["key"],
        rpm_limit=litellm_data["rpm_limit"],
        max_budget=litellm_data["max_budget"],
        budget_duration=litellm_data["budget_duration"],
        created_at=litellm_data["created_at"],
        updated_at=litellm_data["updated_at"]
    )
    db.add(key_entry)
    db.commit()
    return {"key": litellm_data["key"]}

@app.put("/key/transfer")
def transfer_key(request: TransferKeyRequest, db: Session = Depends(get_db)):
    # Поиск ключа
    key_entry = db.query(Key).filter(Key.key == request.key).first()
    if not key_entry:
        raise HTTPException(status_code=404, detail="Key not found")
    # Обновление в LiteLLM
    update_litellm_key(request.key, request.new_username)
    # Обновление в базе
    key_entry.username = request.new_username
    db.commit()
    return {"key": request.key}

@app.get("/key/validate")
def validate_key(username: str = Query(...), db: Session = Depends(get_db)):
    key_entry = db.query(Key).filter(Key.username == username).first()
    if key_entry:
        key_preview = f"{key_entry.key[:5]}...{key_entry.key[-5:]}"
        return {"has_key": True, "key_preview": key_preview}
    else:
        return {"has_key": False}