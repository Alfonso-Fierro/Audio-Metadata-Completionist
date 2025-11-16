#!/usr/bin/env python3
"""
Example: Basic usage of Audio Metadata Completionist.

This example demonstrates how to use the pipeline to enrich audio files
programmatically.
"""

import asyncio
from pathlib import Path

from src.core.audio_file import AudioFile
from src.pipeline.enrichment_pipeline import EnrichmentPipeline
from src.utils.logging_config import setup_logging


async def main() -> None:
    """Main example function."""
    # Setup logging
    setup_logging(level="INFO")

    # Initialize the enrichment pipeline
    print("Initializing enrichment pipeline...")
    pipeline = EnrichmentPipeline(dry_run=False)

    # Example 1: Enrich a single file
    print("\n=== Example 1: Single File ===")
    try:
        audio_file = AudioFile(Path("path/to/your/song.mp3"))
        result = await pipeline.enrich_file(
            audio_file,
            skip_existing=False,
            force_artwork=True,
        )

        if result.success:
            print(f"✓ Successfully enriched: {result.file_path.name}")
            if result.enriched_metadata:
                meta = result.enriched_metadata.track
                print(f"  Artist: {meta.artist.name if meta.artist else 'Unknown'}")
                print(f"  Album: {meta.album.title if meta.album else 'Unknown'}")
                print(f"  Title: {meta.title}")
                print(f"  Artwork: {'Added' if result.artwork_added else 'Not found'}")
        else:
            print(f"✗ Failed to enrich: {result.error}")

    except FileNotFoundError:
        print("File not found. Please update the path in this example.")
    except Exception as e:
        print(f"Error: {e}")

    # Example 2: Enrich a directory
    print("\n=== Example 2: Directory Processing ===")
    try:
        music_dir = Path("path/to/your/music/folder")

        results, stats = await pipeline.enrich_directory(
            music_dir,
            recursive=True,
            skip_existing=True,
            force_artwork=False,
            max_concurrent=4,
        )

        print(f"\nProcessing complete!")
        print(f"  Total files: {stats.total_files}")
        print(f"  Successful: {stats.successful} ({stats.success_rate():.1f}%)")
        print(f"  Identified: {stats.identified}")
        print(f"  Artwork added: {stats.artwork_added}")
        print(f"  Failed: {stats.failed}")

        # Show detailed results
        print("\nDetailed results:")
        for result in results[:5]:  # Show first 5
            status = "✓" if result.success else "✗"
            print(f"  {status} {result.file_path.name}")

    except FileNotFoundError:
        print("Directory not found. Please update the path in this example.")
    except Exception as e:
        print(f"Error: {e}")

    # Example 3: Read metadata without enriching
    print("\n=== Example 3: Read Existing Metadata ===")
    try:
        audio_file = AudioFile(Path("path/to/your/song.mp3"))
        metadata = audio_file.read_metadata()

        print(f"Existing metadata:")
        print(f"  Title: {metadata.track.title}")
        print(f"  Artist: {metadata.track.artist.name if metadata.track.artist else 'Unknown'}")
        print(f"  Album: {metadata.track.album.title if metadata.track.album else 'Unknown'}")
        print(f"  Source: {metadata.source.value}")
        print(f"  Confidence: {metadata.confidence:.2%}")
        print(f"  Complete: {metadata.has_complete_info()}")

        # Get format info
        format_info = audio_file.get_format_info()
        print(f"\nFormat information:")
        print(f"  Format: {format_info.format.value.upper()}")
        print(f"  Bitrate: {format_info.bitrate // 1000 if format_info.bitrate else 'N/A'} kbps")
        print(f"  Duration: {int(format_info.duration or 0)} seconds")
        print(f"  Lossless: {format_info.is_lossless()}")

    except FileNotFoundError:
        print("File not found. Please update the path in this example.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
