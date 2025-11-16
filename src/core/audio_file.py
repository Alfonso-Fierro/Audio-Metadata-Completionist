"""Audio file abstraction and handling."""

from enum import Enum
from pathlib import Path
from typing import Optional

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.id3 import APIC, ID3
from mutagen.mp3 import MP3
from pydantic import BaseModel, Field

from src.core.metadata import (
    AlbumMetadata,
    ArtistMetadata,
    Metadata,
    MetadataSource,
    TrackMetadata,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class SupportedFormat(str, Enum):
    """Supported audio formats."""

    MP3 = "mp3"
    FLAC = "flac"
    M4A = "m4a"
    OGG = "ogg"
    WAV = "wav"
    WMA = "wma"


class AudioFormat(BaseModel):
    """Audio format information."""

    format: SupportedFormat = Field(..., description="Audio format")
    bitrate: Optional[int] = Field(None, description="Bitrate in bps")
    sample_rate: Optional[int] = Field(None, description="Sample rate in Hz")
    channels: Optional[int] = Field(None, description="Number of audio channels")
    duration: Optional[float] = Field(None, description="Duration in seconds")
    size: int = Field(..., description="File size in bytes")

    def is_lossless(self) -> bool:
        """Check if format is lossless."""
        return self.format in {SupportedFormat.FLAC, SupportedFormat.WAV}


class AudioFile:
    """Represents an audio file with metadata capabilities."""

    SUPPORTED_EXTENSIONS = {ext.value for ext in SupportedFormat}

    def __init__(self, file_path: Path) -> None:
        """
        Initialize audio file.

        Args:
            file_path: Path to audio file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        self.file_path = file_path.resolve()

        if not self.file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        if not self.is_supported_format(self.file_path):
            raise ValueError(f"Unsupported audio format: {file_path.suffix}")

        self._mutagen_file: Optional[mutagen.FileType] = None
        self._load_file()

    @classmethod
    def is_supported_format(cls, file_path: Path) -> bool:
        """
        Check if file format is supported.

        Args:
            file_path: Path to check

        Returns:
            True if format is supported
        """
        return file_path.suffix.lstrip(".").lower() in cls.SUPPORTED_EXTENSIONS

    def _load_file(self) -> None:
        """Load audio file with mutagen."""
        try:
            self._mutagen_file = mutagen.File(self.file_path, easy=True)
            if self._mutagen_file is None:
                raise ValueError(f"Could not load audio file: {self.file_path}")
        except Exception as e:
            logger.error(f"Error loading audio file {self.file_path}: {e}")
            raise

    def get_format_info(self) -> AudioFormat:
        """
        Get audio format information.

        Returns:
            Audio format details
        """
        if self._mutagen_file is None:
            raise RuntimeError("Audio file not loaded")

        info = self._mutagen_file.info
        format_name = self.file_path.suffix.lstrip(".").lower()

        return AudioFormat(
            format=SupportedFormat(format_name),
            bitrate=getattr(info, "bitrate", None),
            sample_rate=getattr(info, "sample_rate", None),
            channels=getattr(info, "channels", None),
            duration=getattr(info, "length", None),
            size=self.file_path.stat().st_size,
        )

    def read_metadata(self) -> Metadata:
        """
        Read existing metadata from file.

        Returns:
            Metadata object with existing tags
        """
        if self._mutagen_file is None:
            raise RuntimeError("Audio file not loaded")

        # Extract basic tags
        tags = self._mutagen_file.tags or {}

        # Build track metadata
        track_data = {
            "title": self._get_tag(tags, "title") or self.file_path.stem,
            "artist": None,
            "album": None,
            "track_number": self._parse_int(self._get_tag(tags, "tracknumber")),
            "disc_number": self._parse_int(self._get_tag(tags, "discnumber")),
            "genre": self._get_tag(tags, "genre", multiple=True),
            "year": self._parse_int(self._get_tag(tags, "date")),
            "duration": int(self.get_format_info().duration or 0),
        }

        # Artist
        artist_name = self._get_tag(tags, "artist")
        if artist_name:
            track_data["artist"] = ArtistMetadata(name=artist_name)

        # Album
        album_title = self._get_tag(tags, "album")
        if album_title:
            album_artist_name = self._get_tag(tags, "albumartist") or artist_name
            album_data = {"title": album_title}
            if album_artist_name:
                album_data["artist"] = ArtistMetadata(name=album_artist_name)
            track_data["album"] = AlbumMetadata(**album_data)

        track = TrackMetadata(**track_data)

        return Metadata(
            track=track,
            source=MetadataSource.EXISTING,
            confidence=0.5 if track.title and track.artist else 0.1,
        )

    def write_metadata(self, metadata: Metadata) -> bool:
        """
        Write metadata to audio file.

        Args:
            metadata: Metadata to write

        Returns:
            True if successful

        Raises:
            RuntimeError: If write fails
        """
        if self._mutagen_file is None:
            raise RuntimeError("Audio file not loaded")

        try:
            # Reload file with appropriate handler
            format_type = self.get_format_info().format

            if format_type == SupportedFormat.MP3:
                self._write_mp3_metadata(metadata)
            elif format_type == SupportedFormat.FLAC:
                self._write_flac_metadata(metadata)
            else:
                self._write_generic_metadata(metadata)

            logger.info(f"Successfully wrote metadata to {self.file_path.name}")
            return True

        except Exception as e:
            logger.error(f"Error writing metadata to {self.file_path}: {e}")
            raise RuntimeError(f"Failed to write metadata: {e}") from e

    def _write_mp3_metadata(self, metadata: Metadata) -> None:
        """Write metadata to MP3 file."""
        audio = EasyID3(self.file_path)

        # Basic tags
        if metadata.track.title:
            audio["title"] = metadata.track.title
        if metadata.track.artist:
            audio["artist"] = metadata.track.artist.name
        if metadata.track.album:
            audio["album"] = metadata.track.album.title
            if metadata.track.album.artist:
                audio["albumartist"] = metadata.track.album.artist.name
        if metadata.track.track_number:
            audio["tracknumber"] = str(metadata.track.track_number)
        if metadata.track.disc_number:
            audio["discnumber"] = str(metadata.track.disc_number)
        if metadata.track.year:
            audio["date"] = str(metadata.track.year)
        if metadata.track.genre:
            audio["genre"] = metadata.track.genre

        audio.save()

        # Add artwork if available
        if metadata.track.album and metadata.track.album.artwork_data:
            audio_id3 = ID3(self.file_path)
            audio_id3.delall("APIC")  # Remove existing artwork
            audio_id3.add(
                APIC(
                    encoding=3,  # UTF-8
                    mime="image/jpeg",
                    type=3,  # Cover (front)
                    desc="Cover",
                    data=metadata.track.album.artwork_data,
                )
            )
            audio_id3.save()

    def _write_flac_metadata(self, metadata: Metadata) -> None:
        """Write metadata to FLAC file."""
        audio = FLAC(self.file_path)

        # Basic tags
        if metadata.track.title:
            audio["title"] = metadata.track.title
        if metadata.track.artist:
            audio["artist"] = metadata.track.artist.name
        if metadata.track.album:
            audio["album"] = metadata.track.album.title
            if metadata.track.album.artist:
                audio["albumartist"] = metadata.track.album.artist.name
        if metadata.track.track_number:
            audio["tracknumber"] = str(metadata.track.track_number)
        if metadata.track.disc_number:
            audio["discnumber"] = str(metadata.track.disc_number)
        if metadata.track.year:
            audio["date"] = str(metadata.track.year)
        if metadata.track.genre:
            audio["genre"] = metadata.track.genre

        # Add artwork if available
        if metadata.track.album and metadata.track.album.artwork_data:
            audio.clear_pictures()
            picture = mutagen.flac.Picture()
            picture.type = 3  # Cover (front)
            picture.mime = "image/jpeg"
            picture.desc = "Cover"
            picture.data = metadata.track.album.artwork_data
            audio.add_picture(picture)

        audio.save()

    def _write_generic_metadata(self, metadata: Metadata) -> None:
        """Write metadata using generic mutagen interface."""
        if not self._mutagen_file:
            return

        # Reload with easy interface
        audio = mutagen.File(self.file_path, easy=True)
        if not audio:
            raise RuntimeError("Could not load file for writing")

        if metadata.track.title:
            audio["title"] = metadata.track.title
        if metadata.track.artist:
            audio["artist"] = metadata.track.artist.name
        if metadata.track.album:
            audio["album"] = metadata.track.album.title

        audio.save()

    @staticmethod
    def _get_tag(tags: dict, key: str, multiple: bool = False) -> Optional[str | list]:
        """Extract tag value from mutagen tags."""
        if key not in tags:
            return [] if multiple else None

        value = tags[key]
        if isinstance(value, list):
            return value if multiple else (value[0] if value else None)
        return [str(value)] if multiple else str(value)

    @staticmethod
    def _parse_int(value: Optional[str]) -> Optional[int]:
        """Parse integer from string, handling track numbers like '1/12'."""
        if not value:
            return None
        try:
            # Handle "1/12" format
            if "/" in str(value):
                value = str(value).split("/")[0]
            return int(str(value))
        except (ValueError, AttributeError):
            return None

    def __str__(self) -> str:
        """String representation."""
        return f"AudioFile({self.file_path.name})"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"AudioFile(file_path={self.file_path})"
