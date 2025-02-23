from pydantic_settings import BaseSettings
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import os

load_dotenv()

class DatabaseSettings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    RESET_TOKEN_EXPIRE_MINUTES: int = 15
    FRONTEND_URL: str

class RedisSettings(BaseSettings):
    REDIS_PASSWORD: Optional[str] = None
    REDIS_HOST: str
    REDIS_PORT: int

    @property
    def redis_url(self) -> str:
        """Генерує URL підключення до Redis."""
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/0"

class CelerySettings(BaseSettings):
    CELERY_BROKER_URL: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.CELERY_BROKER_URL:
            redis_settings = RedisSettings()
            self.CELERY_BROKER_URL = redis_settings.redis_url

class SecuritySettings(BaseSettings):
    SECRET_LIBRARIAN_CODE: str  # 🆕 Код для реєстрації бібліотекаря

class EmailSettings(BaseSettings):
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str  # 🆕 Адреса відправника email

class AppSettings(DatabaseSettings, RedisSettings, CelerySettings, SecuritySettings, EmailSettings):
    class Config:
        env_file = "./.env"
        env_file_encoding = "utf-8"  # ✅ Додано для підтримки кирилиці
        extra = "allow"

class LogConfig(BaseSettings):
    LOGGER_NAME: str = "app"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "DEBUG"

    version: int = 1
    disable_existing_loggers: bool = False
    formatters: Dict[str, Any] = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: Dict[str, Any] = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers: Dict[str, Any] = {
        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
    }

settings = AppSettings()
