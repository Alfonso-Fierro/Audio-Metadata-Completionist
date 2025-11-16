#!/usr/bin/env python3
"""
Example: Using custom artwork providers.

This example shows how to create and use custom artwork providers
in the enrichment pipeline.
"""

import asyncio
from pathlib import Path
from typing import List, Optional

from pydantic import HttpUrl

from src.artwork.aggregator import ArtworkAggregator
from src.artwork.base import ArtworkProvider, ArtworkResult
from src.core.audio_file import AudioFile
from src.pipeline.enrichment_pipeline import EnrichmentPipeline
from src.utils.http_client import HTTPClient
from src.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


class CustomArtworkProvider(ArtworkProvider):
    """
    Example custom artwork provider.

    This is a template for creating your own artwork providers.
    Replace the implementation with your own API or data source.
    """

    def __init__(self) -> None:
        """Initialize custom provider."""
        self._client: Optional[HTTPClient] = None

    @property
    def name(self) -> str:
        """Provider name."""
        return "custom_provider"

    async def search(
        self,
        artist: str,
        album: str,
        musicbrainz_id: Optional[str] = None,
    ) -> List[ArtworkResult]:
        """
        Search for album artwork.

        Args:
            artist: Artist name
            album: Album name
            musicbrainz_id: Optional MusicBrainz ID

        Returns:
            List of artwork results
        """
        results = []

        try:
            # TODO: Implement your custom search logic here
            # Example: Call your API, scrape website, etc.

            logger.info(f"Searching custom provider for {artist} - {album}")

            # Example result (replace with actual implementation)
            # results.append(
            #     ArtworkResult(
            #         url=HttpUrl("https://example.com/artwork.jpg"),
            #         provider=self.name,
            #         width=1000,
            #         height=1000,
            #         format="jpg",
            #         quality_score=0.8,
            #     )
            # )

        except Exception as e:
            logger.error(f"Custom provider search failed: {e}")

        return results

    async def download(self, artwork_result: ArtworkResult) -> Optional[bytes]:
        """
        Download artwork from URL.

        Args:
            artwork_result: Artwork result with URL

        Returns:
            Image data as bytes
        """
        try:
            async with HTTPClient() as client:
                response = await client.get(str(artwork_result.url))
                return response.content

        except Exception as e:
            logger.error(f"Failed to download artwork: {e}")
            return None


async def main() -> None:
    """Main example function."""
    setup_logging(level="INFO")

    # Create custom artwork aggregator with custom provider
    custom_provider = CustomArtworkProvider()

    # Create aggregator with custom and default providers
    artwork_aggregator = ArtworkAggregator(
        providers=[
            custom_provider,
            # Add default providers if desired
            # CoverArtArchiveProvider(),
            # ITunesProvider(),
        ]
    )

    # Create pipeline with custom aggregator
    pipeline = EnrichmentPipeline(
        artwork_aggregator=artwork_aggregator,
        dry_run=False,
    )

    # Use the pipeline
    try:
        audio_file = AudioFile(Path("path/to/your/song.mp3"))
        result = await pipeline.enrich_file(audio_file)

        if result.success:
            print(f"✓ Successfully enriched with custom provider")
        else:
            print(f"✗ Failed: {result.error}")

    except FileNotFoundError:
        print("File not found. Please update the path in this example.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
