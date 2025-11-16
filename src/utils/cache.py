"""Simple file-based caching system."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

from src.config import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class Cache:
    """File-based cache with TTL support."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        """
        Initialize cache.

        Args:
            cache_dir: Cache directory (defaults to settings.cache_dir)
            ttl: Time-to-live in seconds (defaults to settings.cache_ttl)
            enabled: Enable caching (defaults to settings.cache_enabled)
        """
        self.cache_dir = cache_dir or settings.cache_dir
        self.ttl = ttl or settings.cache_ttl
        self.enabled = enabled if enabled is not None else settings.cache_enabled

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """
        Generate cache file path from key.

        Args:
            key: Cache key

        Returns:
            Path to cache file
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None

        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # Check TTL
            if self.ttl > 0:
                timestamp = cache_data.get("timestamp", 0)
                if time.time() - timestamp > self.ttl:
                    logger.debug(f"Cache expired for key: {key}")
                    cache_path.unlink()
                    return None

            logger.debug(f"Cache hit for key: {key}")
            return cache_data.get("value")
        except Exception as e:
            logger.warning(f"Error reading cache for key {key}: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        if not self.enabled:
            return

        cache_path = self._get_cache_path(key)
        cache_data = {
            "timestamp": time.time(),
            "value": value,
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f)
            logger.debug(f"Cached value for key: {key}")
        except Exception as e:
            logger.warning(f"Error writing cache for key {key}: {e}")

    def clear(self) -> None:
        """Clear all cached data."""
        if not self.enabled or not self.cache_dir.exists():
            return

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Error deleting cache file {cache_file}: {e}")

        logger.info("Cache cleared")

    def invalidate(self, key: str) -> None:
        """
        Invalidate specific cache entry.

        Args:
            key: Cache key to invalidate
        """
        if not self.enabled:
            return

        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"Invalidated cache for key: {key}")
