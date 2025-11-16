"""Command-line interface for Audio Metadata Completionist."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src import __version__
from src.config import settings
from src.core.file_processor import FileProcessor
from src.pipeline.enrichment_pipeline import EnrichmentPipeline
from src.utils.logging_config import setup_logging

app = typer.Typer(
    name="audio-metadata",
    help="Professional-grade audio metadata enrichment tool",
    add_completion=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"Audio Metadata Completionist v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Audio Metadata Completionist - Enrich your music collection."""
    pass


@app.command()
def enrich(
    path: Path = typer.Argument(
        ...,
        exists=True,
        help="Path to audio file or directory",
    ),
    recursive: bool = typer.Option(
        True,
        "--recursive/--no-recursive",
        "-r/-R",
        help="Search directories recursively",
    ),
    skip_existing: bool = typer.Option(
        False,
        "--skip-existing",
        "-s",
        help="Skip files that already have complete metadata",
    ),
    force_artwork: bool = typer.Option(
        False,
        "--force-artwork",
        "-a",
        help="Force artwork download even if it exists",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Preview changes without writing to files",
    ),
    max_concurrent: int = typer.Option(
        4,
        "--max-concurrent",
        "-c",
        min=1,
        max=32,
        help="Maximum concurrent operations",
    ),
    log_level: Optional[str] = typer.Option(
        None,
        "--log-level",
        "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
) -> None:
    """
    Enrich audio files with metadata and artwork.

    This command will:
    1. Identify songs using audio fingerprinting
    2. Fetch metadata from MusicBrainz
    3. Download album artwork from multiple sources
    4. Write enriched metadata to audio files
    """
    # Setup logging
    setup_logging(level=log_level)

    # Validate AcousticID API key
    if not settings.acoustid_api_key:
        console.print(
            "[bold red]Error:[/bold red] AcousticID API key not configured.\n"
            "Please set ACOUSTID_API_KEY in your .env file.\n"
            "Get your API key from: https://acoustid.org/api-key"
        )
        raise typer.Exit(code=1)

    console.print(f"[bold blue]Audio Metadata Completionist v{__version__}[/bold blue]\n")

    if dry_run:
        console.print("[bold yellow]DRY RUN MODE[/bold yellow] - No changes will be written\n")

    # Run enrichment
    asyncio.run(
        _enrich_async(
            path=path,
            recursive=recursive,
            skip_existing=skip_existing,
            force_artwork=force_artwork,
            dry_run=dry_run,
            max_concurrent=max_concurrent,
        )
    )


async def _enrich_async(
    path: Path,
    recursive: bool,
    skip_existing: bool,
    force_artwork: bool,
    dry_run: bool,
    max_concurrent: int,
) -> None:
    """Async enrichment workflow."""
    pipeline = EnrichmentPipeline(dry_run=dry_run)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning for audio files...", total=None)

        # Find audio files
        if path.is_file():
            audio_files = [FileProcessor.validate_path(str(path))]
            audio_files = [
                af
                for af in [
                    FileProcessor.find_audio_files(Path(str(f)), recursive=False)[0]
                    for f in audio_files
                ]
            ]
        else:
            audio_files = FileProcessor.find_audio_files(path, recursive=recursive)

        progress.update(task, description=f"Found {len(audio_files)} audio file(s)")
        progress.stop()

    # Display files
    console.print(f"\n[bold]Found {len(audio_files)} audio file(s)[/bold]")

    if not typer.confirm("Proceed with enrichment?", default=True):
        console.print("Aborted.")
        raise typer.Exit()

    # Enrich files
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Enriching files...", total=len(audio_files))

        results, stats = await pipeline.enrich_files(
            audio_files,
            skip_existing=skip_existing,
            force_artwork=force_artwork,
            max_concurrent=max_concurrent,
        )

        progress.update(task, completed=len(audio_files))

    # Display results
    _display_results(results, stats)


def _display_results(results, stats) -> None:
    """Display enrichment results in a table."""
    console.print(f"\n[bold green]Enrichment Complete![/bold green]\n")

    # Statistics
    console.print(f"[bold]Statistics:[/bold]")
    console.print(f"  Total files: {stats.total_files}")
    console.print(f"  Successful: {stats.successful} ({stats.success_rate():.1f}%)")
    console.print(f"  Identified: {stats.identified}")
    console.print(f"  Artwork added: {stats.artwork_added}")
    console.print(f"  Failed: {stats.failed}\n")

    # Detailed results table
    if results:
        table = Table(title="Detailed Results")
        table.add_column("File", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Artist", style="yellow")
        table.add_column("Album", style="magenta")
        table.add_column("Title", style="green")
        table.add_column("Artwork", justify="center")

        for result in results:
            status = "✓" if result.success else "✗"
            status_style = "green" if result.success else "red"

            artist = ""
            album = ""
            title = ""
            artwork = ""

            if result.enriched_metadata:
                if result.enriched_metadata.track.artist:
                    artist = result.enriched_metadata.track.artist.name
                if result.enriched_metadata.track.album:
                    album = result.enriched_metadata.track.album.title
                title = result.enriched_metadata.track.title
                artwork = "✓" if result.artwork_added else "✗"

            table.add_row(
                result.file_path.name,
                f"[{status_style}]{status}[/{status_style}]",
                artist[:30],
                album[:30],
                title[:30],
                artwork,
            )

        console.print(table)


@app.command()
def info(
    path: Path = typer.Argument(
        ...,
        exists=True,
        help="Path to audio file",
    ),
) -> None:
    """Display metadata information for an audio file."""
    setup_logging()

    try:
        audio_file_path = FileProcessor.validate_path(str(path))
        audio_files = FileProcessor.find_audio_files(audio_file_path, recursive=False)

        if not audio_files:
            console.print(f"[bold red]Error:[/bold red] Not a supported audio file: {path}")
            raise typer.Exit(code=1)

        audio_file = audio_files[0]

        # Read metadata
        metadata = audio_file.read_metadata()
        format_info = audio_file.get_format_info()

        # Display info
        console.print(f"\n[bold blue]File Information[/bold blue]")
        console.print(f"Path: {audio_file.file_path}")
        console.print(f"Format: {format_info.format.value.upper()}")
        console.print(f"Size: {format_info.size / 1024 / 1024:.2f} MB")

        if format_info.duration:
            console.print(f"Duration: {int(format_info.duration // 60)}:{int(format_info.duration % 60):02d}")
        if format_info.bitrate:
            console.print(f"Bitrate: {format_info.bitrate // 1000} kbps")
        if format_info.sample_rate:
            console.print(f"Sample Rate: {format_info.sample_rate} Hz")

        console.print(f"\n[bold blue]Metadata[/bold blue]")
        console.print(f"Title: {metadata.track.title}")

        if metadata.track.artist:
            console.print(f"Artist: {metadata.track.artist.name}")
        if metadata.track.album:
            console.print(f"Album: {metadata.track.album.title}")
        if metadata.track.track_number:
            console.print(f"Track: {metadata.track.track_number}")
        if metadata.track.year:
            console.print(f"Year: {metadata.track.year}")
        if metadata.track.genre:
            console.print(f"Genre: {', '.join(metadata.track.genre)}")

        console.print(f"\nMetadata Source: {metadata.source.value}")
        console.print(f"Confidence: {metadata.confidence:.2%}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def clear_cache() -> None:
    """Clear the application cache."""
    from src.utils.cache import Cache

    cache = Cache()
    cache.clear()
    console.print("[bold green]Cache cleared successfully![/bold green]")


if __name__ == "__main__":
    app()
