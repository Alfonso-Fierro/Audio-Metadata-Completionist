"""Tests for metadata models."""

import pytest
from pydantic import ValidationError

from src.core.metadata import (
    AlbumMetadata,
    ArtistMetadata,
    Metadata,
    MetadataSource,
    TrackMetadata,
)


class TestArtistMetadata:
    """Tests for ArtistMetadata model."""

    def test_create_artist(self):
        """Test creating artist metadata."""
        artist = ArtistMetadata(name="Test Artist")
        assert artist.name == "Test Artist"
        assert artist.sort_name is None
        assert artist.musicbrainz_id is None

    def test_artist_with_musicbrainz_id(self):
        """Test artist with MusicBrainz ID."""
        artist = ArtistMetadata(
            name="Test Artist",
            musicbrainz_id="12345-67890",
        )
        assert artist.musicbrainz_id == "12345-67890"

    def test_artist_str_representation(self):
        """Test string representation."""
        artist = ArtistMetadata(name="Test Artist")
        assert str(artist) == "Test Artist"


class TestAlbumMetadata:
    """Tests for AlbumMetadata model."""

    def test_create_album(self):
        """Test creating album metadata."""
        artist = ArtistMetadata(name="Test Artist")
        album = AlbumMetadata(title="Test Album", artist=artist)
        assert album.title == "Test Album"
        assert album.artist == artist

    def test_album_str_with_artist(self):
        """Test string representation with artist."""
        artist = ArtistMetadata(name="Test Artist")
        album = AlbumMetadata(title="Test Album", artist=artist)
        assert str(album) == "Test Artist - Test Album"

    def test_album_str_without_artist(self):
        """Test string representation without artist."""
        album = AlbumMetadata(title="Test Album")
        assert str(album) == "Test Album"


class TestTrackMetadata:
    """Tests for TrackMetadata model."""

    def test_create_track(self):
        """Test creating track metadata."""
        artist = ArtistMetadata(name="Test Artist")
        track = TrackMetadata(title="Test Track", artist=artist)
        assert track.title == "Test Track"
        assert track.artist == artist

    def test_track_validation(self):
        """Test track validation."""
        with pytest.raises(ValidationError):
            TrackMetadata(title="", artist=None)  # Empty title

    def test_track_number_validation(self):
        """Test track number validation."""
        with pytest.raises(ValidationError):
            TrackMetadata(title="Test", track_number=0)  # Must be >= 1

    def test_year_validation(self):
        """Test year validation."""
        with pytest.raises(ValidationError):
            TrackMetadata(title="Test", year=1800)  # Too early

        with pytest.raises(ValidationError):
            TrackMetadata(title="Test", year=2200)  # Too late


class TestMetadata:
    """Tests for Metadata model."""

    def test_create_metadata(self, sample_metadata):
        """Test creating complete metadata."""
        assert sample_metadata.track.title == "Test Track"
        assert sample_metadata.source == MetadataSource.MUSICBRAINZ
        assert sample_metadata.confidence == 0.9

    def test_merge_metadata(self):
        """Test merging metadata."""
        artist1 = ArtistMetadata(name="Artist 1")
        track1 = TrackMetadata(title="Track 1", artist=artist1)
        metadata1 = Metadata(
            track=track1,
            source=MetadataSource.ACOUSTID,
            confidence=0.7,
        )

        artist2 = ArtistMetadata(name="Artist 2")
        album2 = AlbumMetadata(title="Album 2")
        track2 = TrackMetadata(title="Track 1", album=album2, year=2024)
        metadata2 = Metadata(
            track=track2,
            source=MetadataSource.MUSICBRAINZ,
            confidence=0.9,
        )

        # Merge - prefer higher confidence
        merged = metadata1.merge_with(metadata2)
        assert merged.track.artist.name == "Artist 1"  # From metadata1
        assert merged.track.album.title == "Album 2"  # From metadata2
        assert merged.track.year == 2024  # From metadata2
        assert merged.confidence == 0.9  # Higher confidence

    def test_has_complete_info(self):
        """Test checking for complete metadata."""
        # Complete metadata
        artist = ArtistMetadata(name="Artist")
        album = AlbumMetadata(title="Album")
        track = TrackMetadata(title="Track", artist=artist, album=album)
        metadata = Metadata(track=track, source=MetadataSource.MUSICBRAINZ)
        assert metadata.has_complete_info() is True

        # Incomplete metadata
        track_incomplete = TrackMetadata(title="Track")
        metadata_incomplete = Metadata(
            track=track_incomplete, source=MetadataSource.UNKNOWN
        )
        assert metadata_incomplete.has_complete_info() is False
