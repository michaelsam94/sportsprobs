"""Application configuration management."""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Sports Analytics API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")

    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/sports_analytics"
    )
    DATABASE_ECHO: bool = Field(default=False)

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_PER_HOUR: int = Field(default=1000)

    # API
    API_V1_PREFIX: str = Field(default="/api/v1")
    API_TITLE: str = Field(default="Sports Analytics API")
    API_DESCRIPTION: str = Field(
        default="Backend API for sports analytics mobile application"
    )

    # Security
    SECRET_KEY: str = Field(default="change-me-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )

    # External Services
    SPORTS_DATA_API_KEY: str = Field(default="")
    SPORTS_DATA_API_URL: str = Field(default="https://api.sportsdata.io/v3")

    # Proxy/Cache Settings
    CACHE_ENABLED: bool = Field(default=True)
    CACHE_DEFAULT_TTL: int = Field(default=300)  # 5 minutes
    PROXY_RETRY_MAX_ATTEMPTS: int = Field(default=3)
    PROXY_RETRY_DELAY: float = Field(default=1.0)

    # Admin Settings
    ADMIN_TOKEN: Optional[str] = Field(default=None, description="Admin token for protected endpoints")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

