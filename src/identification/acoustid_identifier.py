"""AcousticID-based audio identification using chromaprint fingerprinting."""

import asyncio
from pathlib import Path
from typing import List, Optional

import acoustid

from src.config import settings
from src.core.metadata import (
    AlbumMetadata,
    ArtistMetadata,
    Metadata,
    MetadataSource,
    TrackMetadata,
)
from src.identification.base import IdentificationResult, Identifier
from src.identification.musicbrainz_client import MusicBrainzClient
from src.utils.cache import Cache
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class AcoustIDIdentifier(Identifier):
    """Identify audio files using AcousticID fingerprinting."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache: Optional[Cache] = None,
        musicbrainz_client: Optional[MusicBrainzClient] = None,
    ) -> None:
        """
        Initialize AcousticID identifier.

        Args:
            api_key: AcousticID API key (defaults to settings.acoustid_api_key)
            cache: Cache instance
            musicbrainz_client: MusicBrainz client for additional metadata
        """
        self.api_key = api_key or settings.acoustid_api_key
        if not self.api_key:
            raise ValueError(
                "AcousticID API key required. Set ACOUSTID_API_KEY in .env or pass to constructor."
            )

        self.cache = cache or Cache()
        self.mb_client = musicbrainz_client or MusicBrainzClient(cache=self.cache)

    async def identify(self, audio_file_path: Path) -> List[IdentificationResult]:
        """
        Identify audio file using AcousticID.

        Args:
            audio_file_path: Path to audio file

        Returns:
            List of identification results, sorted by score

        Raises:
            Exception: On identification failure
        """
        if not audio_file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        # Check cache
        cache_key = f"acoustid:{audio_file_path}:{audio_file_path.stat().st_mtime}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Using cached AcousticID result for {audio_file_path.name}")
            return [IdentificationResult(**r) for r in cached]

        logger.info(f"Identifying {audio_file_path.name} with AcousticID...")

        try:
            # Run fingerprinting in thread pool (blocking I/O)
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._fingerprint_and_match,
                str(audio_file_path),
            )

            # Process results
            identification_results: List[IdentificationResult] = []

            for score, recording_id, title, artist in results:
                # Get additional metadata from MusicBrainz
                metadata = await self._build_metadata_from_recording(
                    recording_id, title, artist
                )

                if metadata:
                    identification_results.append(
                        IdentificationResult(
                            metadata=metadata,
                            score=score,
                            source="acoustid",
                            fingerprint=recording_id,
                        )
                    )

            # Sort by score descending
            identification_results.sort(key=lambda x: x.score, reverse=True)

            # Cache results
            if identification_results:
                self.cache.set(
                    cache_key,
                    [r.model_dump(mode="json") for r in identification_results],
                )

            logger.info(
                f"Found {len(identification_results)} match(es) for {audio_file_path.name}"
            )
            return identification_results

        except Exception as e:
            logger.error(f"AcousticID identification failed for {audio_file_path.name}: {e}")
            return []

    def _fingerprint_and_match(self, file_path: str) -> List[tuple]:
        """
        Generate fingerprint and match against AcousticID database.

        Args:
            file_path: Path to audio file

        Returns:
            List of (score, recording_id, title, artist) tuples
        """
        results = []

        try:
            # Match using acoustid library
            for score, recording_id, title, artist in acoustid.match(self.api_key, file_path):
                results.append((score, recording_id, title, artist))

                # Limit to top 5 matches
                if len(results) >= 5:
                    break

        except acoustid.NoBackendError:
            logger.error(
                "Chromaprint/fpcalc not found. Install with: apt-get install libchromaprint-tools"
            )
            raise
        except Exception as e:
            logger.error(f"Fingerprinting error: {e}")
            raise

        return results

    async def _build_metadata_from_recording(
        self,
        recording_id: str,
        title: Optional[str],
        artist: Optional[str],
    ) -> Optional[Metadata]:
        """
        Build metadata from MusicBrainz recording.

        Args:
            recording_id: MusicBrainz recording ID
            title: Track title from AcousticID
            artist: Artist name from AcousticID

        Returns:
            Metadata object or None
        """
        try:
            # Get detailed info from MusicBrainz
            recording_data = await self.mb_client.get_recording(recording_id)

            if not recording_data:
                # Fallback to basic info from AcousticID
                track = TrackMetadata(
                    title=title or "Unknown",
                    artist=ArtistMetadata(name=artist) if artist else None,
                    musicbrainz_recording_id=recording_id,
                )
                return Metadata(
                    track=track,
                    source=MetadataSource.ACOUSTID,
                    confidence=0.5,
                )

            # Build comprehensive metadata from MusicBrainz
            track = TrackMetadata(
                title=recording_data.get("title", title or "Unknown"),
                artist=(
                    ArtistMetadata(
                        name=recording_data.get("artist-credit-phrase", artist or "Unknown"),
                        musicbrainz_id=recording_data.get("artist-credit", [{}])[0].get("artist", {}).get("id"),
                    )
                    if recording_data.get("artist-credit-phrase") or artist
                    else None
                ),
                album=(
                    AlbumMetadata(
                        title=recording_data.get("release", {}).get("title", "Unknown"),
                        musicbrainz_id=recording_data.get("release", {}).get("id"),
                    )
                    if recording_data.get("release")
                    else None
                ),
                duration=recording_data.get("length", 0) // 1000 if recording_data.get("length") else None,
                musicbrainz_recording_id=recording_id,
            )

            return Metadata(
                track=track,
                source=MetadataSource.MUSICBRAINZ,
                confidence=0.85,
            )

        except Exception as e:
            logger.warning(f"Could not fetch MusicBrainz data for {recording_id}: {e}")
            return None

    async def identify_batch(
        self, audio_file_paths: List[Path]
    ) -> dict[Path, List[IdentificationResult]]:
        """
        Identify multiple audio files concurrently.

        Args:
            audio_file_paths: List of audio file paths

        Returns:
            Dictionary mapping file paths to identification results
        """
        tasks = [self.identify(path) for path in audio_file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for path, result in zip(audio_file_paths, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to identify {path.name}: {result}")
                output[path] = []
            else:
                output[path] = result

        return output
