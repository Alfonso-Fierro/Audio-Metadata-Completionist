"""File and folder processing utilities."""

from pathlib import Path
from typing import Iterator, List, Optional

from src.core.audio_file import AudioFile
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class FileProcessor:
    """Process audio files and folders."""

    @staticmethod
    def find_audio_files(
        path: Path,
        recursive: bool = True,
    ) -> List[AudioFile]:
        """
        Find all supported audio files in a directory or return single file.

        Args:
            path: File or directory path
            recursive: Search recursively in subdirectories

        Returns:
            List of AudioFile objects

        Raises:
            FileNotFoundError: If path doesn't exist
            ValueError: If no audio files found
        """
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        audio_files: List[AudioFile] = []

        if path.is_file():
            if AudioFile.is_supported_format(path):
                try:
                    audio_files.append(AudioFile(path))
                except Exception as e:
                    logger.warning(f"Could not load {path}: {e}")
            else:
                raise ValueError(f"Unsupported file format: {path}")

        elif path.is_dir():
            pattern = "**/*" if recursive else "*"
            for file_path in path.glob(pattern):
                if file_path.is_file() and AudioFile.is_supported_format(file_path):
                    try:
                        audio_files.append(AudioFile(file_path))
                    except Exception as e:
                        logger.warning(f"Could not load {file_path}: {e}")

        if not audio_files:
            raise ValueError(f"No supported audio files found in: {path}")

        logger.info(f"Found {len(audio_files)} audio file(s) in {path}")
        return audio_files

    @staticmethod
    def group_by_album(audio_files: List[AudioFile]) -> dict[str, List[AudioFile]]:
        """
        Group audio files by album (typically by directory).

        Args:
            audio_files: List of audio files

        Returns:
            Dictionary mapping album path to list of files
        """
        albums: dict[str, List[AudioFile]] = {}

        for audio_file in audio_files:
            album_key = str(audio_file.file_path.parent)
            if album_key not in albums:
                albums[album_key] = []
            albums[album_key].append(audio_file)

        logger.debug(f"Grouped {len(audio_files)} files into {len(albums)} album(s)")
        return albums

    @staticmethod
    def iter_audio_files(
        path: Path,
        recursive: bool = True,
    ) -> Iterator[AudioFile]:
        """
        Iterate over audio files without loading all into memory.

        Args:
            path: File or directory path
            recursive: Search recursively

        Yields:
            AudioFile objects
        """
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        if path.is_file():
            if AudioFile.is_supported_format(path):
                try:
                    yield AudioFile(path)
                except Exception as e:
                    logger.warning(f"Could not load {path}: {e}")
        else:
            pattern = "**/*" if recursive else "*"
            for file_path in path.glob(pattern):
                if file_path.is_file() and AudioFile.is_supported_format(file_path):
                    try:
                        yield AudioFile(file_path)
                    except Exception as e:
                        logger.warning(f"Could not load {file_path}: {e}")

    @staticmethod
    def validate_path(path_str: str) -> Path:
        """
        Validate and convert path string to Path object.

        Args:
            path_str: Path as string

        Returns:
            Validated Path object

        Raises:
            ValueError: If path is invalid
        """
        try:
            path = Path(path_str).expanduser().resolve()
            if not path.exists():
                raise ValueError(f"Path does not exist: {path}")
            return path
        except Exception as e:
            raise ValueError(f"Invalid path: {path_str}") from e
