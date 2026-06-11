from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    SECRET_KEY: str
    # DATABASE_URL: str
    # DEBUG: bool = False
    
    model_config = SettingsConfigDict(
        # env_file="app/.env",
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

# class Settings(BaseSettings):
#     model_config = SettingsConfigDict(
#         env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
#         env_file_encoding="utf-8",
#         extra="ignore",
#     )

#     SECRET_KEY: str
    
settings = Settings()
