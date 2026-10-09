from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "LiveZ"

    # --- Безопасность ---
    SECRET_KEY: str
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = Field(default=3600, ge=60)

    # --- БД ---
    DATABASE_URL: str

    # --- CORS ---
    # В .env задаётся строкой через запятую; JSON-массив тоже поддерживается.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    # --- Загрузки ---
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_MB: int = Field(default=10, ge=1, le=100)
    MAX_AVATAR_MB: int = Field(default=5, ge=1, le=100)

    # --- Прочее ---
    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Флаг Secure у cookie с токеном. Включайте только если сайт реально
    # открывается по HTTPS: при HTTP браузер не отправит cookie и вход сломается
    # (в том числе через http://localhost при DEBUG=false).
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str):
            raw = v.strip()
            # поддержка JSON-массива: ["http://a", "http://b"]
            if raw.startswith("["):
                import json

                try:
                    parsed = json.loads(raw)
                except ValueError:
                    parsed = None
                if isinstance(parsed, list):
                    return [str(s).strip() for s in parsed if str(s).strip()]
                # «полу-JSON» вида ["http://a"] без закрывающей кавычки — фолбэк
                raw = raw.strip("[]")
            return [s.strip().strip('"').strip("'") for s in raw.split(",") if s.strip()]
        return v

    @field_validator("UPLOAD_DIR", mode="before")
    @classmethod
    def resolve_upload_dir(cls, v):
        p = Path(v)
        return p if p.is_absolute() else (PROJECT_ROOT / p)

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def max_avatar_bytes(self) -> int:
        return self.MAX_AVATAR_MB * 1024 * 1024

    @property
    def avatars_dir(self) -> Path:
        return self.UPLOAD_DIR / "avatars"

    @property
    def post_images_dir(self) -> Path:
        return self.UPLOAD_DIR / "posts"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
