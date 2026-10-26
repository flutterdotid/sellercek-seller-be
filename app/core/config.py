import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PORT: int = 8008
    HOST: str = "0.0.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sellercek"
    SELLERCEK_CORE_API_URL: str = "https://api.sellercek.com"

    JWT_SECRET: str = "sellercek_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    DEFAULT_SELLER_API_KEY: str = ""

    OPENAI_API_KEY: str = ""
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
