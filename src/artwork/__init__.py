"""Album artwork providers."""

from .aggregator import ArtworkAggregator
from .base import ArtworkProvider, ArtworkResult
from .coverartarchive import CoverArtArchiveProvider
from .itunes import ITunesProvider

__all__ = [
    "ArtworkProvider",
    "ArtworkResult",
    "CoverArtArchiveProvider",
    "ITunesProvider",
    "ArtworkAggregator",
]
