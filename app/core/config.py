from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database (MongoDB only - PostgreSQL removed)
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "doclearn"
    
    # Environment
    ENV: str = "development"
    DEBUG: bool = False
    
    # JWT Authentication (Simple)
    # Generate a strong secret for production: python -c "import secrets; print(secrets.token_urlsafe(32))"
    JWT_SECRET: str = "change-this-secret-in-production"
    
    # LLM API Keys (Gemini only)
    GOOGLE_API_KEY: Optional[str] = None
    
    # LLM Model Configuration (All Gemini)
    PLANNING_MODEL: str = "gemini-2.5-pro"
    TUTORING_MODEL: str = "gemini-2.5-flash"
    
    # Streaming Configuration
    STREAMING_TOKEN_THRESHOLD: int = 100
    
    # Memory Buffer Configuration
    MEMORY_BUFFER_SIZE: int = 10
    
    # Service Configuration
    SERVICE_NAME: str = "generation_service"
    SERVICE_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
