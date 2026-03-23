"""
Application settings and configuration
Loads from environment variables
"""

from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Server
    APP_NAME: str = "Mars Rover AI Simulator API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Host
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # API
    API_V1_STR: str = "/api/v1"
    OPENAPI_URL: str = "/openapi.json"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1",
    ]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # Dataset Configuration
    DATASETS_CACHE_DIR: str = "./datasets/cache"
    DATASETS_PDS_API: str = "https://pds-geosciences.wustl.edu/mro/mro-m-hirise-3-dtm-v1/"
    
    # Terrain Data URLs
    TERRAIN_MOLA_URL: str = "https://pds-geosciences.wustl.edu/mro/"
    TERRAIN_HIRISE_URL: str = "https://www.uahirise.org/dtm/"
    TERRAIN_CTX_URL: str = "https://pds-geosciences.wustl.edu/mro/mro-m-ctx-3/"
    
    # Rover Configuration
    ROVER_MAX_SPEED: float = 0.5  # m/s
    ROVER_MAX_SLOPE: float = 30.0  # degrees
    ROVER_WHEEL_SIZE: float = 0.25  # meters
    ROVER_SAFETY_MARGIN: float = 1.0  # meters
    
    # Logging
    LOG_LEVEL: str = "info"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
