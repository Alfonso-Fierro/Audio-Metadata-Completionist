"""Metadata models using Pydantic for validation."""

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class MetadataSource(str, Enum):
    """Source of metadata."""

    ACOUSTID = "acoustid"
    MUSICBRAINZ = "musicbrainz"
    MANUAL = "manual"
    EXISTING = "existing"
    UNKNOWN = "unknown"


class ArtistMetadata(BaseModel):
    """Artist information."""

    name: str = Field(..., min_length=1, description="Artist name")
    sort_name: Optional[str] = Field(None, description="Artist sort name")
    musicbrainz_id: Optional[str] = Field(None, description="MusicBrainz artist ID")

    def __str__(self) -> str:
        """String representation."""
        return self.name


class AlbumMetadata(BaseModel):
    """Album information."""

    title: str = Field(..., min_length=1, description="Album title")
    artist: Optional[ArtistMetadata] = Field(None, description="Album artist")
    release_date: Optional[date] = Field(None, description="Release date")
    total_tracks: Optional[int] = Field(None, ge=1, description="Total tracks in album")
    musicbrainz_id: Optional[str] = Field(None, description="MusicBrainz release ID")
    artwork_url: Optional[HttpUrl] = Field(None, description="Album artwork URL")
    artwork_data: Optional[bytes] = Field(None, description="Album artwork binary data")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True

    def __str__(self) -> str:
        """String representation."""
        if self.artist:
            return f"{self.artist.name} - {self.title}"
        return self.title


class TrackMetadata(BaseModel):
    """Track-specific information."""

    title: str = Field(..., min_length=1, description="Track title")
    artist: Optional[ArtistMetadata] = Field(None, description="Track artist")
    album: Optional[AlbumMetadata] = Field(None, description="Album information")
    track_number: Optional[int] = Field(None, ge=1, description="Track number")
    disc_number: Optional[int] = Field(None, ge=1, description="Disc number")
    duration: Optional[int] = Field(None, ge=0, description="Duration in seconds")
    genre: Optional[List[str]] = Field(default_factory=list, description="Genre tags")
    year: Optional[int] = Field(None, ge=1900, le=2100, description="Release year")
    musicbrainz_recording_id: Optional[str] = Field(
        None, description="MusicBrainz recording ID"
    )
    musicbrainz_track_id: Optional[str] = Field(None, description="MusicBrainz track ID")

    def __str__(self) -> str:
        """String representation."""
        parts = []
        if self.artist:
            parts.append(self.artist.name)
        parts.append(self.title)
        if self.album:
            parts.append(f"({self.album.title})")
        return " - ".join(parts)


class Metadata(BaseModel):
    """Complete metadata for an audio file."""

    track: TrackMetadata = Field(..., description="Track metadata")
    source: MetadataSource = Field(
        default=MetadataSource.UNKNOWN,
        description="Source of metadata",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for metadata accuracy",
    )

    def merge_with(self, other: "Metadata", prefer_higher_confidence: bool = True) -> "Metadata":
        """
        Merge this metadata with another, preferring non-null values.

        Args:
            other: Other metadata to merge
            prefer_higher_confidence: If True, prefer metadata with higher confidence

        Returns:
            Merged metadata
        """
        if prefer_higher_confidence and other.confidence > self.confidence:
            base, overlay = other, self
        else:
            base, overlay = self, other

        # Deep copy base track
        merged_track_data = base.track.model_dump()

        # Overlay non-null values
        for field, value in overlay.track.model_dump().items():
            if value is not None and (
                merged_track_data.get(field) is None or not merged_track_data.get(field)
            ):
                merged_track_data[field] = value

        merged_track = TrackMetadata(**merged_track_data)

        return Metadata(
            track=merged_track,
            source=base.source if base.confidence >= overlay.confidence else overlay.source,
            confidence=max(base.confidence, overlay.confidence),
        )

    def has_complete_info(self) -> bool:
        """
        Check if metadata has essential information.

        Returns:
            True if track has title, artist, and album
        """
        return bool(
            self.track.title
            and self.track.artist
            and self.track.artist.name
            and self.track.album
            and self.track.album.title
        )

    def __str__(self) -> str:
        """String representation."""
        return f"Metadata({self.track}, source={self.source.value}, confidence={self.confidence:.2f})"
