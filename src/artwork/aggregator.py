"""Aggregator for multiple artwork providers."""

from typing import List, Optional

from PIL import Image
from io import BytesIO

from src.artwork.base import ArtworkProvider, ArtworkResult
from src.artwork.coverartarchive import CoverArtArchiveProvider
from src.artwork.itunes import ITunesProvider
from src.config import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ArtworkAggregator:
    """Aggregate results from multiple artwork providers."""

    def __init__(
        self,
        providers: Optional[List[ArtworkProvider]] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
    ) -> None:
        """
        Initialize artwork aggregator.

        Args:
            providers: List of artwork providers (defaults to all available)
            min_size: Minimum artwork size in pixels
            max_size: Maximum artwork size in pixels
        """
        self.providers = providers or [
            CoverArtArchiveProvider(),
            ITunesProvider(),
        ]
        self.min_size = min_size or settings.artwork_min_size
        self.max_size = max_size or settings.artwork_max_size

    async def search(
        self,
        artist: str,
        album: str,
        musicbrainz_id: Optional[str] = None,
    ) -> List[ArtworkResult]:
        """
        Search all providers for artwork.

        Args:
            artist: Artist name
            album: Album name
            musicbrainz_id: Optional MusicBrainz release ID

        Returns:
            Aggregated and sorted list of artwork results
        """
        all_results: List[ArtworkResult] = []

        logger.info(f"Searching for artwork: {artist} - {album}")

        for provider in self.providers:
            try:
                results = await provider.search(artist, album, musicbrainz_id)
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                continue

        # Filter by size requirements
        suitable_results = [
            r for r in all_results if r.is_suitable(self.min_size, self.max_size)
        ]

        # Sort by quality score
        suitable_results.sort(key=lambda x: x.quality_score, reverse=True)

        logger.info(
            f"Found {len(suitable_results)} suitable artwork(s) from {len(self.providers)} providers"
        )

        return suitable_results

    async def download_best(
        self,
        artist: str,
        album: str,
        musicbrainz_id: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Search and download the best artwork.

        Args:
            artist: Artist name
            album: Album name
            musicbrainz_id: Optional MusicBrainz release ID

        Returns:
            Image data as bytes or None
        """
        results = await self.search(artist, album, musicbrainz_id)

        if not results:
            logger.warning(f"No artwork found for {artist} - {album}")
            return None

        # Try downloading from best results
        for result in results[:3]:  # Try top 3
            provider = next(
                (p for p in self.providers if p.name == result.provider), None
            )
            if not provider:
                continue

            try:
                artwork_data = await provider.download(result)
                if artwork_data:
                    # Validate and optionally resize
                    processed_data = self._process_image(artwork_data)
                    if processed_data:
                        logger.info(
                            f"Successfully downloaded artwork from {result.provider}"
                        )
                        return processed_data
            except Exception as e:
                logger.warning(f"Failed to download from {result.provider}: {e}")
                continue

        logger.error(f"Could not download any artwork for {artist} - {album}")
        return None

    def _process_image(self, image_data: bytes) -> Optional[bytes]:
        """
        Process and validate image.

        Args:
            image_data: Raw image bytes

        Returns:
            Processed image bytes or None
        """
        try:
            # Open image
            img = Image.open(BytesIO(image_data))

            # Validate format
            if img.format not in ("JPEG", "PNG"):
                logger.debug(f"Converting image from {img.format} to JPEG")
                img = img.convert("RGB")

            # Check dimensions
            width, height = img.size
            min_dim = min(width, height)
            max_dim = max(width, height)

            # Resize if needed
            if max_dim > self.max_size:
                ratio = self.max_size / max_dim
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.debug(f"Resized image from {width}x{height} to {new_size}")

            # Convert to bytes
            output = BytesIO()
            img.save(output, format="JPEG", quality=90, optimize=True)
            return output.getvalue()

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return None
