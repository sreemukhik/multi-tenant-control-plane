from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://urumi:urumi@platform-db:5432/urumi"
    MAX_STORES_PER_USER: int = 5
    PROVISIONING_TIMEOUT_MINUTES: int = 10
    RATE_LIMIT_CREATES_PER_MINUTE: int = 5
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "local"
    
    # Optional Auth
    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
