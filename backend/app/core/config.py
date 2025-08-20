from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List   # <-- add this
import os

class Settings(BaseSettings):
    APP_NAME: str = "legal-intel"
    API_PREFIX: str = "/api/v1"
    ENV: str = Field(default="dev", description="dev|staging|prod")
    DEBUG: bool = False

    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./app.db")
    DATA_DIR: str = Field(default="./data")
    STORAGE_BACKEND: str = Field(default="local")

    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    MAX_UPLOAD_MB: int = 20
    REQUEST_TIMEOUT_S: int = 25
    RATE_LIMIT_WINDOW_S: int = Field(default=60, description="Sliding window in seconds")
    RATE_LIMIT_MAX_REQUESTS: int = Field(default=120, description="Max requests per window per IP")
    SHUTDOWN_GRACE_PERIOD_S: int = Field(default=10, description="Max seconds to wait for in-flight requests to finish on shutdown")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
os.makedirs(settings.DATA_DIR, exist_ok=True)
