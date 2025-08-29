# app/core/config.py
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # -------- App --------
    PROJECT_NAME: str = "ESP32 Gym API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["development", "production", "test"] = "development"

    # -------- Seguridad --------
    SECRET_KEY: str = "supersecret"  # cámbialo en producción
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 día
    ALGORITHM: str = "HS256"

    # -------- Integraciones / Infra --------
    DATABASE_URL: str  # p.ej: mysql+pymysql://user:pass@localhost:3306/gym_db?charset=utf8mb4
    ESP32_BASE_URL: str  # p.ej: http://192.168.0.50

    # Pydantic v2 settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
