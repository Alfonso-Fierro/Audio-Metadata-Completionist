"""Base classes for audio identification."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from src.core.metadata import Metadata


class IdentificationResult(BaseModel):
    """Result from audio identification service."""

    metadata: Metadata = Field(..., description="Identified metadata")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    source: str = Field(..., description="Identification source")
    fingerprint: Optional[str] = Field(None, description="Audio fingerprint")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class Identifier(ABC):
    """Base class for audio identification services."""

    @abstractmethod
    async def identify(self, audio_file_path: Path) -> List[IdentificationResult]:
        """
        Identify audio file and return possible matches.

        Args:
            audio_file_path: Path to audio file

        Returns:
            List of identification results, sorted by confidence score

        Raises:
            Exception: On identification failure
        """
        pass

    @abstractmethod
    async def identify_batch(
        self, audio_file_paths: List[Path]
    ) -> dict[Path, List[IdentificationResult]]:
        """
        Identify multiple audio files.

        Args:
            audio_file_paths: List of audio file paths

        Returns:
            Dictionary mapping file paths to identification results

        Raises:
            Exception: On identification failure
        """
        pass
