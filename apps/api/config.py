import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "KrushiNeel Setu"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DEMO_MODE: bool = True
    SIMULATOR_ENABLED: bool = True
    
    DATABASE_URL: str = "sqlite:///./krushineel.db"
    
    JWT_SECRET: str = "krushineel-secret-key-production-change-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    SMS_PROVIDER: str = "mock"  # mock | twilio | fast2sms
    SMS_API_KEY: str = ""
    SMS_SENDER_ID: str = "KRUSHI"
    
    DATAGOV_API_KEY: str = ""
    ML_SERVICE_URL: str = "http://localhost:9000"
    
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ]
    
    STORAGE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "grading"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "catches"), exist_ok=True)
