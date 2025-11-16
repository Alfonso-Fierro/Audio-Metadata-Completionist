#!/usr/bin/env python3
"""
Manual test script for Swan Lake album metadata enrichment.
This demonstrates the metadata writing capability using manually created metadata.
"""
import asyncio
from pathlib import Path

from src.core.audio_file import AudioFile
from src.core.metadata import (
    Metadata,
    TrackMetadata,
    AlbumMetadata,
    ArtistMetadata,
    MetadataSource,
)
from src.utils.logging_config import setup_logging, get_logger

setup_logging(level="INFO")
logger = get_logger(__name__)


async def enrich_swan_lake_manual():
    """Enrich Swan Lake tracks with manually created metadata."""

    print("\n" + "="*70)
    print("  Audio Metadata Completionist - Swan Lake Test")
    print("="*70 + "\n")

    # Find Swan Lake files
    swan_lake_dir = Path("Swan Lake - Tchaikovsky")
    if not swan_lake_dir.exists():
        logger.error(f"Directory not found: {swan_lake_dir}")
        return

    audio_files = []
    for file_path in sorted(swan_lake_dir.glob("*.flac")):
        try:
            audio_files.append(AudioFile(file_path))
            logger.info(f"✓ Loaded: {file_path.name}")
        except Exception as e:
            logger.error(f"✗ Failed to load {file_path.name}: {e}")

    if not audio_files:
        logger.error("No audio files found!")
        return

    print(f"\n📁 Found {len(audio_files)} FLAC files")

    # Show original metadata
    print("\n" + "-"*70)
    print("BEFORE ENRICHMENT:")
    print("-"*70)
    for i, audio_file in enumerate(audio_files, 1):
        metadata = audio_file.read_metadata()
        format_info = audio_file.get_format_info()
        print(f"\n[{i}] {audio_file.file_path.name}")
        print(f"    Duration: {int(format_info.duration // 60)}:{int(format_info.duration % 60):02d}")
        print(f"    Title: {metadata.track.title}")
        print(f"    Artist: {metadata.track.artist.name if metadata.track.artist else 'None'}")
        print(f"    Album: {metadata.track.album.title if metadata.track.album else 'None'}")
        print(f"    Track #: {metadata.track.track_number}")
        print(f"    Confidence: {metadata.confidence:.0%}")

    # Manual metadata based on filename analysis
    track_info = [
        {
            "number": 1,
            "title": "Swan Lake, Op. 20, Act I: Introduction",
            "duration": 168  # 2:48
        },
        {
            "number": 2,
            "title": "Swan Lake, Op. 20, Act I: No. 1, Scene. Allegro giusto",
            "duration": 0  # Will be filled from file
        }
    ]

    album_data = {
        "title": "Tchaikovsky: Swan Lake, Op. 20",
        "artist": "Pyotr Ilyich Tchaikovsky",
        "performer": "London Symphony Orchestra",
        "conductor": "André Previn",
        "year": 1976
    }

    print(f"\n\n📝 Creating metadata for:")
    print(f"   Album: {album_data['title']}")
    print(f"   Composer: {album_data['artist']}")
    print(f"   Performer: {album_data['performer']}")
    print(f"   Conductor: {album_data['conductor']}")

    # Enrich each file
    print("\n" + "-"*70)
    print("ENRICHING FILES:")
    print("-"*70)

    for i, audio_file in enumerate(audio_files):
        if i >= len(track_info):
            logger.warning(f"No track info for file {i+1}, skipping")
            continue

        track_data = track_info[i]

        print(f"\n[{i+1}/{len(audio_files)}] {audio_file.file_path.name}")

        try:
            # Get actual duration from file
            format_info = audio_file.get_format_info()
            duration = int(format_info.duration or 0)

            # Create album metadata
            album = AlbumMetadata(
                title=album_data["title"],
                artist=ArtistMetadata(name=album_data["artist"])
            )

            # Create track metadata
            track = TrackMetadata(
                title=track_data["title"],
                artist=ArtistMetadata(name=album_data["conductor"]),
                album=album,
                track_number=track_data["number"],
                duration=duration,
                year=album_data["year"],
                genre=["Classical", "Ballet"]
            )

            # Create complete metadata
            enriched = Metadata(
                track=track,
                source=MetadataSource.MANUAL,
                confidence=1.0
            )

            print(f"    ✏️  Writing:")
            print(f"        Title: {track.title}")
            print(f"        Artist: {track.artist.name}")
            print(f"        Album: {album.title}")
            print(f"        Track: {track.track_number}")
            print(f"        Year: {track.year}")
            print(f"        Genre: {', '.join(track.genre)}")

            # Write metadata
            success = audio_file.write_metadata(enriched)

            if success:
                print(f"    ✅ Successfully enriched!")
            else:
                print(f"    ❌ Failed to write metadata")

        except Exception as e:
            print(f"    ❌ Error: {e}")
            logger.exception("Error enriching file")

    # Verify results
    print("\n" + "-"*70)
    print("AFTER ENRICHMENT (Verification):")
    print("-"*70)

    for i, audio_file in enumerate(audio_files, 1):
        try:
            # Reload the file to verify changes were written
            reloaded = AudioFile(audio_file.file_path)
            metadata = reloaded.read_metadata()
            format_info = reloaded.get_format_info()

            print(f"\n[{i}] {audio_file.file_path.name}")
            print(f"    Duration: {int(format_info.duration // 60)}:{int(format_info.duration % 60):02d}")
            print(f"    Title: {metadata.track.title}")
            print(f"    Artist: {metadata.track.artist.name if metadata.track.artist else 'None'}")
            print(f"    Album: {metadata.track.album.title if metadata.track.album else 'None'}")
            print(f"    Year: {metadata.track.year if metadata.track.year else 'None'}")
            print(f"    Track #: {metadata.track.track_number}")
            print(f"    Genre: {', '.join(metadata.track.genre) if metadata.track.genre else 'None'}")
            print(f"    Confidence: {metadata.confidence:.0%}")

        except Exception as e:
            print(f"    ❌ Error verifying: {e}")

    print("\n" + "="*70)
    print("  ✅ TEST COMPLETE!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(enrich_swan_lake_manual())
