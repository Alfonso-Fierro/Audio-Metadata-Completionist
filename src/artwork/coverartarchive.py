"""Cover Art Archive provider (official MusicBrainz artwork database)."""

from typing import Optional

from src.artwork.base import ArtworkProvider, ArtworkResult
from src.utils.http_client import HTTPClient
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class CoverArtArchiveProvider(ArtworkProvider):
    """Fetch artwork from Cover Art Archive (MusicBrainz)."""

    BASE_URL = "https://coverartarchive.org"

    def __init__(self, http_client: Optional[HTTPClient] = None) -> None:
        """
        Initialize Cover Art Archive provider.

        Args:
            http_client: HTTP client instance
        """
        self._http_client = http_client

    @property
    def name(self) -> str:
        """Provider name."""
        return "coverartarchive"

    async def search(
        self,
        artist: str,
        album: str,
        musicbrainz_id: Optional[str] = None,
    ) -> list[ArtworkResult]:
        """
        Search for album artwork using MusicBrainz ID.

        Args:
            artist: Artist name (not used, MusicBrainz ID preferred)
            album: Album name (not used, MusicBrainz ID preferred)
            musicbrainz_id: MusicBrainz release ID (required for this provider)

        Returns:
            List of artwork results
        """
        if not musicbrainz_id:
            logger.debug("CoverArtArchive requires MusicBrainz ID")
            return []

        results = []

        try:
            async with HTTPClient() as client:
                url = f"{self.BASE_URL}/release/{musicbrainz_id}"
                response = await client.get(url)
                data = response.json()

                # Process images
                for image in data.get("images", []):
                    # Prefer front cover
                    is_front = image.get("front", False)
                    quality_score = 0.9 if is_front else 0.6

                    # Get best quality image URL
                    image_url = image.get("image")
                    if not image_url:
                        continue

                    results.append(
                        ArtworkResult(
                            url=image_url,
                            provider=self.name,
                            width=None,  # Not provided by API
                            height=None,
                            format="jpg",
                            quality_score=quality_score,
                        )
                    )

                logger.info(
                    f"Found {len(results)} artwork(s) from Cover Art Archive for {artist} - {album}"
                )

        except Exception as e:
            logger.warning(f"Cover Art Archive search failed for {artist} - {album}: {e}")

        return sorted(results, key=lambda x: x.quality_score, reverse=True)

    async def download(self, artwork_result: ArtworkResult) -> Optional[bytes]:
        """
        Download artwork from URL.

        Args:
            artwork_result: Artwork result containing URL

        Returns:
            Image data as bytes
        """
        try:
            async with HTTPClient() as client:
                response = await client.get(str(artwork_result.url))
                return response.content

        except Exception as e:
            logger.error(f"Failed to download artwork from {artwork_result.url}: {e}")
            return None
