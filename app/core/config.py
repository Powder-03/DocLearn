from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://user:password@host:port/db"
    MONGODB_URL: str = "mongodb://user:password@host:port"
    
    # Environment
    ENV: str = "development"
    DEBUG: bool = False
    
    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # LLM Model Configuration
    PLANNING_MODEL: str = "gemini-2.0-flash"  # Fast, cheap for planning
    TUTORING_MODEL: str = "gpt-4o"  # Powerful for tutoring
    
    # Service Configuration
    SERVICE_NAME: str = "generation_service"
    SERVICE_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
