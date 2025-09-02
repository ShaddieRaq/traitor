import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # Application
    app_name: str = "Trading Bot"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./trader.db"
    
    # Coinbase API
    coinbase_api_key: str = ""
    coinbase_api_secret: str = ""
    
    # Redis for Celery
    redis_url: str = "redis://localhost:6379/0"
    
    # API settings
    api_v1_prefix: str = "/api/v1"
    
    class Config:
        env_file = "../.env"
        case_sensitive = False


settings = Settings()
