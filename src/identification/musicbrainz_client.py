"""MusicBrainz API client for metadata enrichment."""

import asyncio
from typing import Any, Dict, Optional

import musicbrainzngs as mb

from src.config import settings
from src.utils.cache import Cache
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class MusicBrainzClient:
    """Client for MusicBrainz API."""

    def __init__(self, cache: Optional[Cache] = None) -> None:
        """
        Initialize MusicBrainz client.

        Args:
            cache: Cache instance for API responses
        """
        self.cache = cache or Cache()

        # Configure musicbrainzngs
        mb.set_useragent(
            app=settings.musicbrainz_app_name,
            version=settings.musicbrainz_app_version,
            contact=settings.musicbrainz_contact_email,
        )
        mb.set_rate_limit(limit_or_interval=1.0)  # 1 request per second

        logger.debug("MusicBrainz client initialized")

    async def get_recording(self, recording_id: str) -> Optional[Dict[str, Any]]:
        """
        Get recording information from MusicBrainz.

        Args:
            recording_id: MusicBrainz recording ID

        Returns:
            Recording data dictionary or None
        """
        cache_key = f"mb:recording:{recording_id}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Using cached MusicBrainz recording: {recording_id}")
            return cached

        try:
            logger.debug(f"Fetching MusicBrainz recording: {recording_id}")

            # Run in thread pool (blocking I/O)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: mb.get_recording_by_id(
                    recording_id,
                    includes=["artists", "releases", "artist-credits"],
                ),
            )

            recording_data = result.get("recording")
            if recording_data:
                self.cache.set(cache_key, recording_data)

            return recording_data

        except mb.WebServiceError as e:
            logger.warning(f"MusicBrainz API error for recording {recording_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching recording {recording_id}: {e}")
            return None

    async def get_release(self, release_id: str) -> Optional[Dict[str, Any]]:
        """
        Get release (album) information from MusicBrainz.

        Args:
            release_id: MusicBrainz release ID

        Returns:
            Release data dictionary or None
        """
        cache_key = f"mb:release:{release_id}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Using cached MusicBrainz release: {release_id}")
            return cached

        try:
            logger.debug(f"Fetching MusicBrainz release: {release_id}")

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: mb.get_release_by_id(
                    release_id,
                    includes=["artists", "artist-credits", "recordings"],
                ),
            )

            release_data = result.get("release")
            if release_data:
                self.cache.set(cache_key, release_data)

            return release_data

        except mb.WebServiceError as e:
            logger.warning(f"MusicBrainz API error for release {release_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching release {release_id}: {e}")
            return None

    async def search_release(
        self,
        artist: str,
        album: str,
        limit: int = 5,
    ) -> list[Dict[str, Any]]:
        """
        Search for releases by artist and album name.

        Args:
            artist: Artist name
            album: Album name
            limit: Maximum number of results

        Returns:
            List of release data dictionaries
        """
        cache_key = f"mb:search:release:{artist}:{album}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Using cached MusicBrainz search: {artist} - {album}")
            return cached

        try:
            logger.debug(f"Searching MusicBrainz for: {artist} - {album}")

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: mb.search_releases(
                    artist=artist,
                    release=album,
                    limit=limit,
                ),
            )

            releases = result.get("release-list", [])
            if releases:
                self.cache.set(cache_key, releases)

            return releases

        except mb.WebServiceError as e:
            logger.warning(f"MusicBrainz search error for {artist} - {album}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching {artist} - {album}: {e}")
            return []
