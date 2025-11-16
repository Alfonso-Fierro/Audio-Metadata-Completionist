"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level for the application",
    )
    log_file: Path = Field(
        default=Path("logs/audio_metadata.log"),
        description="Path to the log file",
    )

    # AcousticID Configuration
    acoustid_api_key: str = Field(
        default="",
        description="AcousticID API key for audio fingerprinting",
    )

    # MusicBrainz Configuration
    musicbrainz_contact_email: str = Field(
        default="user@example.com",
        description="Contact email for MusicBrainz API",
    )
    musicbrainz_app_name: str = Field(
        default="AudioMetadataCompletionist",
        description="Application name for MusicBrainz",
    )
    musicbrainz_app_version: str = Field(
        default="1.0.0",
        description="Application version for MusicBrainz",
    )

    # HTTP Configuration
    http_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="HTTP request timeout in seconds",
    )
    http_max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of HTTP retries",
    )
    http_retry_delay: int = Field(
        default=1,
        ge=0,
        le=60,
        description="Delay between HTTP retries in seconds",
    )

    # Cache Configuration
    cache_enabled: bool = Field(
        default=True,
        description="Enable caching for API responses",
    )
    cache_dir: Path = Field(
        default=Path(".cache"),
        description="Directory for cache storage",
    )
    cache_ttl: int = Field(
        default=86400,
        ge=0,
        description="Cache time-to-live in seconds",
    )

    # Artwork Configuration
    artwork_min_size: int = Field(
        default=500,
        ge=100,
        le=5000,
        description="Minimum artwork size in pixels",
    )
    artwork_max_size: int = Field(
        default=2000,
        ge=100,
        le=10000,
        description="Maximum artwork size in pixels",
    )
    artwork_format: Literal["jpg", "png"] = Field(
        default="jpg",
        description="Preferred artwork format",
    )

    # Processing Configuration
    max_workers: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Maximum number of worker threads",
    )
    batch_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Batch size for processing multiple files",
    )

    @field_validator("log_file", "cache_dir")
    @classmethod
    def ensure_parent_dir_exists(cls, v: Path) -> Path:
        """Ensure parent directory exists for file paths."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v

    def validate_acoustid_key(self) -> bool:
        """Check if AcousticID API key is configured."""
        return bool(self.acoustid_api_key and self.acoustid_api_key != "")


# Global settings instance
settings = Settings()
