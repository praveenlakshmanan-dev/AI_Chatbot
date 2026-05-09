from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = Field(default="amzur-ai-chat")
    ENVIRONMENT: str = Field(default="development")
    DATABASE_URL: str
    SECRET_KEY: str = Field(default="change-me")
    JWT_EXPIRE_MINUTES: int = Field(default=480)
    COOKIE_NAME: str = Field(default="access_token")
    EMPLOYEE_EMAIL_DOMAIN: Optional[str] = Field(default="amzur.com")

    LITELLM_PROXY_URL: str
    LITELLM_API_KEY: str
    LLM_MODEL: str = Field(default="gemini/gemini-2.5-flash")
    LITELLM_EMBEDDING_MODEL: str = Field(default="text-embedding-3-large")
    FRONTEND_URL: Optional[str] = Field(default="http://localhost:5173")

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = Field(default="http://localhost:8000/api/auth/google/callback")

    DEFAULT_USER_EMAIL: str = Field(default="system@amzur.local")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
