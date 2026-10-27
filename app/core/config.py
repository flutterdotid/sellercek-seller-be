import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PORT: int = 8008
    HOST: str = "0.0.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # Core SellerCek API Gateway (Seller BE berkomunikasi via API Core, bukan direct DB)
    SELLERCEK_CORE_API_URL: str = os.getenv("SELLERCEK_CORE_API_URL", "https://api.sellercek.com")
    SELLERCEK_CORE_TIMEOUT: float = 30.0

    # Default Seller API Key / Fallback Token
    DEFAULT_SELLER_API_KEY: str = ""

    OPENAI_API_KEY: str = ""
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
