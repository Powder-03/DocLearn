from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database (MongoDB only)
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "doclearn"
    
    # Environment
    ENV: str = "development"
    DEBUG: bool = False
    
    # JWT Authentication
    # Generate a strong secret: python -c "import secrets; print(secrets.token_urlsafe(32))"
    JWT_SECRET: str = "change-this-secret-in-production"
    JWT_EXPIRATION_HOURS: int = 168  # 7 days
    
    # Email Configuration (SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None  # Gmail App Password
    EMAIL_FROM_NAME: str = "DocLearn"
    EMAIL_FROM_ADDRESS: Optional[str] = None
    
    # Frontend URL (for email verification links)
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Token Expiry
    EMAIL_VERIFICATION_EXPIRY_HOURS: int = 24
    PASSWORD_RESET_EXPIRY_HOURS: int = 1
    
    # LLM API Keys (Gemini only)
    GOOGLE_API_KEY: Optional[str] = None
    
    # LLM Model Configuration (All Gemini)
    PLANNING_MODEL: str = "gemini-2.5-pro"
    TUTORING_MODEL: str = "gemini-2.5-flash"
    DSA_MODEL: str = "gemini-2.5-pro"
    DSA_HEAVY_MODEL: str = "gemini-3.0-pro"
    
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
