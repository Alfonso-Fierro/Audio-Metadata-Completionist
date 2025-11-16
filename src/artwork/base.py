"""Base classes for artwork providers."""

from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ArtworkResult(BaseModel):
    """Result from artwork provider."""

    url: HttpUrl = Field(..., description="Artwork URL")
    provider: str = Field(..., description="Provider name")
    width: Optional[int] = Field(None, description="Image width in pixels")
    height: Optional[int] = Field(None, description="Image height in pixels")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")
    format: Optional[str] = Field(None, description="Image format (jpg, png)")
    quality_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Quality score (higher is better)",
    )

    def get_dimensions(self) -> tuple[int, int]:
        """Get image dimensions."""
        return (self.width or 0, self.height or 0)

    def is_suitable(self, min_size: int = 500, max_size: int = 2000) -> bool:
        """
        Check if artwork meets size requirements.

        Args:
            min_size: Minimum dimension in pixels
            max_size: Maximum dimension in pixels

        Returns:
            True if artwork is suitable
        """
        if not self.width or not self.height:
            return True  # Unknown size, assume suitable

        return (
            min(self.width, self.height) >= min_size
            and max(self.width, self.height) <= max_size
        )


class ArtworkProvider(ABC):
    """Base class for artwork providers."""

    @abstractmethod
    async def search(
        self,
        artist: str,
        album: str,
        musicbrainz_id: Optional[str] = None,
    ) -> list[ArtworkResult]:
        """
        Search for album artwork.

        Args:
            artist: Artist name
            album: Album name
            musicbrainz_id: Optional MusicBrainz release ID for better matching

        Returns:
            List of artwork results, sorted by quality score

        Raises:
            Exception: On search failure
        """
        pass

    @abstractmethod
    async def download(self, artwork_result: ArtworkResult) -> Optional[bytes]:
        """
        Download artwork from URL.

        Args:
            artwork_result: Artwork result containing URL

        Returns:
            Image data as bytes or None on failure
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
