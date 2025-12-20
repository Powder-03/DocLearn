
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@host:port/db"
    MONGODB_URL: str = "mongodb://user:password@host:port"
    ENV: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
