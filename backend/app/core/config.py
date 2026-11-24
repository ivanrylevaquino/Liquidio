from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal
import os

class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables and .env file.
    Pydantic v2 BaseSettings automatically parses and validates types.
    """
    DATABASE_URL: str = Field(default="sqlite:///./liquidio.db")
    JWT_SECRET: str = Field(default="supersecret-liquidio-dost-jwt-key-2026-citu")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    STORAGE_MODE: Literal["local", "drive"] = Field(default="local")
    LOCAL_STORAGE_DIR: str = Field(default="backend/uploads/receipts")

    # Pydantic v2 configuration for loading from .env
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
