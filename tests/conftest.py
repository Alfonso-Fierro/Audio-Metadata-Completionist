"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from src.config import settings


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    from src.core.metadata import (
        AlbumMetadata,
        ArtistMetadata,
        Metadata,
        MetadataSource,
        TrackMetadata,
    )

    artist = ArtistMetadata(name="Test Artist", musicbrainz_id="test-artist-id")
    album = AlbumMetadata(
        title="Test Album",
        artist=artist,
        musicbrainz_id="test-album-id",
    )
    track = TrackMetadata(
        title="Test Track",
        artist=artist,
        album=album,
        track_number=1,
        year=2024,
    )

    return Metadata(
        track=track,
        source=MetadataSource.MUSICBRAINZ,
        confidence=0.9,
    )


@pytest.fixture
def mock_http_client(mocker):
    """Mock HTTP client."""
    from src.utils.http_client import HTTPClient

    mock_client = mocker.MagicMock(spec=HTTPClient)
    return mock_client


@pytest.fixture
def disable_cache(monkeypatch):
    """Disable caching for tests."""
    monkeypatch.setattr(settings, "cache_enabled", False)
