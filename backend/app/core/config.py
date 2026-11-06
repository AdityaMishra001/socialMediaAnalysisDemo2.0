from __future__ import annotations
import json
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FeedbackAI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    
    # Social Media API Keys
    YOUTUBE_API_KEY: Optional[str] = None
    
    # Database Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./feedback_ai.db"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    
    # Input Limits
    MAX_TEXT_LENGTH: int = 100_000
    MAX_ITEMS: int = 2_000

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
