from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/doctordb"
    REDIS_URL: str = "redis://redis:6379"
    SECRET_KEY: str = "supersecretkey-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    APP_NAME: str = "Smart Doctor Booking"
    DEBUG: bool = False
    NVIDIA_API_KEY: str = ""
    NVIDIA_API_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "nvidia/nemotron-content-safety-reasoning-4b"

    class Config:
        env_file = ".env"


settings = Settings()
