"""Main enrichment pipeline orchestrating identification, artwork, and metadata writing."""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel

from src.artwork.aggregator import ArtworkAggregator
from src.core.audio_file import AudioFile
from src.core.metadata import AlbumMetadata, Metadata
from src.identification.acoustid_identifier import AcoustIDIdentifier
from src.utils.cache import Cache
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class EnrichmentResult(BaseModel):
    """Result of enriching a single audio file."""

    file_path: Path
    success: bool
    original_metadata: Optional[Metadata] = None
    enriched_metadata: Optional[Metadata] = None
    artwork_added: bool = False
    error: Optional[str] = None

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True

    def __str__(self) -> str:
        """String representation."""
        status = "✓" if self.success else "✗"
        return f"{status} {self.file_path.name}"


@dataclass
class ProcessingStats:
    """Statistics for batch processing."""

    total_files: int = 0
    successful: int = 0
    failed: int = 0
    identified: int = 0
    artwork_added: int = 0
    skipped: int = 0

    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_files == 0:
            return 0.0
        return (self.successful / self.total_files) * 100

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Stats: {self.successful}/{self.total_files} successful "
            f"({self.success_rate():.1f}%), "
            f"{self.identified} identified, "
            f"{self.artwork_added} with artwork, "
            f"{self.failed} failed"
        )


class EnrichmentPipeline:
    """Orchestrate audio metadata enrichment workflow."""

    def __init__(
        self,
        identifier: Optional[AcoustIDIdentifier] = None,
        artwork_aggregator: Optional[ArtworkAggregator] = None,
        cache: Optional[Cache] = None,
        dry_run: bool = False,
    ) -> None:
        """
        Initialize enrichment pipeline.

        Args:
            identifier: Audio identifier (defaults to AcoustIDIdentifier)
            artwork_aggregator: Artwork aggregator (defaults to ArtworkAggregator)
            cache: Cache instance
            dry_run: If True, don't write metadata to files
        """
        self.cache = cache or Cache()
        self.identifier = identifier or AcoustIDIdentifier(cache=self.cache)
        self.artwork_aggregator = artwork_aggregator or ArtworkAggregator()
        self.dry_run = dry_run

        logger.info(f"Enrichment pipeline initialized (dry_run={dry_run})")

    async def enrich_file(
        self,
        audio_file: AudioFile,
        skip_existing: bool = False,
        force_artwork: bool = False,
    ) -> EnrichmentResult:
        """
        Enrich a single audio file with metadata and artwork.

        Args:
            audio_file: Audio file to enrich
            skip_existing: Skip files that already have metadata
            force_artwork: Force artwork download even if exists

        Returns:
            Enrichment result
        """
        logger.info(f"Processing: {audio_file.file_path.name}")

        try:
            # Read existing metadata
            original_metadata = audio_file.read_metadata()

            # Check if we should skip
            if skip_existing and original_metadata.has_complete_info():
                logger.info(f"Skipping (already has metadata): {audio_file.file_path.name}")
                return EnrichmentResult(
                    file_path=audio_file.file_path,
                    success=True,
                    original_metadata=original_metadata,
                    enriched_metadata=original_metadata,
                )

            # Step 1: Identify audio file
            identification_results = await self.identifier.identify(audio_file.file_path)

            if not identification_results:
                logger.warning(f"Could not identify: {audio_file.file_path.name}")
                return EnrichmentResult(
                    file_path=audio_file.file_path,
                    success=False,
                    original_metadata=original_metadata,
                    error="No identification results",
                )

            # Get best match
            best_match = identification_results[0]
            enriched_metadata = best_match.metadata

            # Merge with existing metadata (prefer identified data)
            enriched_metadata = enriched_metadata.merge_with(
                original_metadata, prefer_higher_confidence=True
            )

            # Step 2: Fetch artwork if needed
            artwork_added = False
            if (
                enriched_metadata.track.album
                and enriched_metadata.track.album.title
                and enriched_metadata.track.artist
            ):
                # Check if artwork already exists
                needs_artwork = (
                    force_artwork or not enriched_metadata.track.album.artwork_data
                )

                if needs_artwork:
                    artwork_data = await self.artwork_aggregator.download_best(
                        artist=enriched_metadata.track.artist.name,
                        album=enriched_metadata.track.album.title,
                        musicbrainz_id=enriched_metadata.track.album.musicbrainz_id,
                    )

                    if artwork_data:
                        # Update album metadata with artwork
                        album_data = enriched_metadata.track.album.model_dump()
                        album_data["artwork_data"] = artwork_data
                        enriched_metadata.track.album = AlbumMetadata(**album_data)
                        artwork_added = True
                        logger.info(f"Added artwork to: {audio_file.file_path.name}")

            # Step 3: Write metadata to file
            if not self.dry_run:
                write_success = audio_file.write_metadata(enriched_metadata)
                if not write_success:
                    return EnrichmentResult(
                        file_path=audio_file.file_path,
                        success=False,
                        original_metadata=original_metadata,
                        enriched_metadata=enriched_metadata,
                        error="Failed to write metadata",
                    )

            logger.info(f"Successfully enriched: {audio_file.file_path.name}")
            return EnrichmentResult(
                file_path=audio_file.file_path,
                success=True,
                original_metadata=original_metadata,
                enriched_metadata=enriched_metadata,
                artwork_added=artwork_added,
            )

        except Exception as e:
            logger.error(f"Error processing {audio_file.file_path.name}: {e}", exc_info=True)
            return EnrichmentResult(
                file_path=audio_file.file_path,
                success=False,
                error=str(e),
            )

    async def enrich_files(
        self,
        audio_files: List[AudioFile],
        skip_existing: bool = False,
        force_artwork: bool = False,
        max_concurrent: int = 4,
    ) -> tuple[List[EnrichmentResult], ProcessingStats]:
        """
        Enrich multiple audio files concurrently.

        Args:
            audio_files: List of audio files to enrich
            skip_existing: Skip files that already have metadata
            force_artwork: Force artwork download even if exists
            max_concurrent: Maximum concurrent operations

        Returns:
            Tuple of (results list, processing stats)
        """
        logger.info(f"Starting batch enrichment of {len(audio_files)} file(s)")

        stats = ProcessingStats(total_files=len(audio_files))
        results: List[EnrichmentResult] = []

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(audio_file: AudioFile) -> EnrichmentResult:
            async with semaphore:
                return await self.enrich_file(
                    audio_file,
                    skip_existing=skip_existing,
                    force_artwork=force_artwork,
                )

        # Process files concurrently
        tasks = [process_with_semaphore(af) for af in audio_files]
        results = await asyncio.gather(*tasks)

        # Calculate statistics
        for result in results:
            if result.success:
                stats.successful += 1
                if result.enriched_metadata and result.enriched_metadata != result.original_metadata:
                    stats.identified += 1
                if result.artwork_added:
                    stats.artwork_added += 1
            else:
                stats.failed += 1

        logger.info(f"Batch enrichment complete: {stats}")
        return results, stats

    async def enrich_directory(
        self,
        directory: Path,
        recursive: bool = True,
        skip_existing: bool = False,
        force_artwork: bool = False,
        max_concurrent: int = 4,
    ) -> tuple[List[EnrichmentResult], ProcessingStats]:
        """
        Enrich all audio files in a directory.

        Args:
            directory: Directory path
            recursive: Search recursively
            skip_existing: Skip files with existing metadata
            force_artwork: Force artwork download
            max_concurrent: Maximum concurrent operations

        Returns:
            Tuple of (results list, processing stats)
        """
        from src.core.file_processor import FileProcessor

        logger.info(f"Scanning directory: {directory}")

        # Find all audio files
        audio_files = FileProcessor.find_audio_files(directory, recursive=recursive)

        # Enrich files
        return await self.enrich_files(
            audio_files,
            skip_existing=skip_existing,
            force_artwork=force_artwork,
            max_concurrent=max_concurrent,
        )
