from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

from project.keygen.config import app_settings


public_schema = MetaData(schema=app_settings.DB_SCHEMA)
Base = declarative_base(metadata=public_schema)
