"""iTunes Search API artwork provider."""

from typing import Optional
from urllib.parse import quote

from src.artwork.base import ArtworkProvider, ArtworkResult
from src.utils.http_client import HTTPClient
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ITunesProvider(ArtworkProvider):
    """Fetch artwork from iTunes Search API."""

    BASE_URL = "https://itunes.apple.com/search"

    def __init__(self, http_client: Optional[HTTPClient] = None) -> None:
        """
        Initialize iTunes provider.

        Args:
            http_client: HTTP client instance
        """
        self._http_client = http_client

    @property
    def name(self) -> str:
        """Provider name."""
        return "itunes"

    async def search(
        self,
        artist: str,
        album: str,
        musicbrainz_id: Optional[str] = None,
    ) -> list[ArtworkResult]:
        """
        Search for album artwork using iTunes API.

        Args:
            artist: Artist name
            album: Album name
            musicbrainz_id: Not used by this provider

        Returns:
            List of artwork results
        """
        results = []

        try:
            # Build search query
            search_term = f"{artist} {album}"
            params = {
                "term": search_term,
                "media": "music",
                "entity": "album",
                "limit": 5,
            }

            async with HTTPClient() as client:
                response = await client.get(self.BASE_URL, params=params)
                data = response.json()

                # Process results
                for item in data.get("results", []):
                    artwork_url = item.get("artworkUrl100")
                    if not artwork_url:
                        continue

                    # iTunes provides URLs in various sizes
                    # Replace size parameter to get higher resolution
                    artwork_url_high = artwork_url.replace("100x100bb", "1200x1200bb")

                    # Calculate quality score based on name match
                    album_name = item.get("collectionName", "").lower()
                    artist_name = item.get("artistName", "").lower()
                    name_match = (
                        album.lower() in album_name or album_name in album.lower()
                    ) and (artist.lower() in artist_name or artist_name in artist.lower())

                    quality_score = 0.8 if name_match else 0.5

                    results.append(
                        ArtworkResult(
                            url=artwork_url_high,
                            provider=self.name,
                            width=1200,
                            height=1200,
                            format="jpg",
                            quality_score=quality_score,
                        )
                    )

                logger.info(f"Found {len(results)} artwork(s) from iTunes for {artist} - {album}")

        except Exception as e:
            logger.warning(f"iTunes search failed for {artist} - {album}: {e}")

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
