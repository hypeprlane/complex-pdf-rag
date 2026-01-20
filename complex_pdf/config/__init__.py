from pathlib import Path
from typing import Any, ClassVar, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent.parent

    BASE_HOST: str | None = None
    ALLOWED_HOSTS: str | None = None
    DEBUG: Any = False

    OPENAI_API_KEY: str | None = None

    GEMINI_API_KEY: str | None = None

    ANTHROPIC_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"
        env_file_encoding = "utf-8"


settings = Settings()
