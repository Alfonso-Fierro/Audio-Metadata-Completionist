"""Tests for configuration."""

import pytest
from pydantic import ValidationError

from src.config import Settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        assert settings.log_level == "INFO"
        assert settings.cache_enabled is True
        assert settings.max_workers == 4

    def test_settings_validation(self):
        """Test settings validation."""
        # Valid settings
        settings = Settings(http_timeout=30)
        assert settings.http_timeout == 30

        # Invalid timeout (too high)
        with pytest.raises(ValidationError):
            Settings(http_timeout=500)

        # Invalid max_workers (too low)
        with pytest.raises(ValidationError):
            Settings(max_workers=0)

    def test_validate_acoustid_key(self):
        """Test AcousticID key validation."""
        settings = Settings(acoustid_api_key="test_key")
        assert settings.validate_acoustid_key() is True

        settings_no_key = Settings(acoustid_api_key="")
        assert settings_no_key.validate_acoustid_key() is False

    def test_artwork_config(self):
        """Test artwork configuration."""
        settings = Settings(
            artwork_min_size=500,
            artwork_max_size=2000,
            artwork_format="jpg",
        )
        assert settings.artwork_min_size == 500
        assert settings.artwork_max_size == 2000
        assert settings.artwork_format == "jpg"
