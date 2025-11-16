"""Core domain models and business logic."""

from .audio_file import AudioFile, AudioFormat, SupportedFormat
from .file_processor import FileProcessor
from .metadata import AlbumMetadata, ArtistMetadata, Metadata, TrackMetadata

__all__ = [
    "AudioFile",
    "AudioFormat",
    "SupportedFormat",
    "FileProcessor",
    "Metadata",
    "TrackMetadata",
    "AlbumMetadata",
    "ArtistMetadata",
]
