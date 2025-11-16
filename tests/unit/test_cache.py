"""Tests for caching functionality."""

import time

import pytest

from src.utils.cache import Cache


class TestCache:
    """Tests for Cache class."""

    def test_cache_enabled(self, temp_dir):
        """Test cache with enabled state."""
        cache = Cache(cache_dir=temp_dir / "cache", enabled=True, ttl=10)
        assert cache.enabled is True

    def test_cache_disabled(self, temp_dir):
        """Test cache with disabled state."""
        cache = Cache(cache_dir=temp_dir / "cache", enabled=False)
        assert cache.enabled is False

        # Set and get should not work when disabled
        cache.set("key", "value")
        assert cache.get("key") is None

    def test_cache_set_and_get(self, temp_dir):
        """Test setting and getting cache values."""
        cache = Cache(cache_dir=temp_dir / "cache", enabled=True, ttl=10)

        cache.set("test_key", {"data": "test_value"})
        result = cache.get("test_key")

        assert result == {"data": "test_value"}

    def test_cache_expiration(self, temp_dir):
        """Test cache TTL expiration."""
        cache = Cache(cache_dir=temp_dir / "cache", enabled=True, ttl=1)

        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

        # Wait for expiration
        time.sleep(2)
        assert cache.get("test_key") is None

    def test_cache_clear(self, temp_dir):
        """Test clearing cache."""
        cache = Cache(cache_dir=temp_dir / "cache", enabled=True)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_invalidate(self, temp_dir):
        """Test invalidating specific cache entry."""
        cache = Cache(cache_dir=temp_dir / "cache", enabled=True)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.invalidate("key1")

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_cache_nonexistent_key(self, temp_dir):
        """Test getting nonexistent key."""
        cache = Cache(cache_dir=temp_dir / "cache", enabled=True)
        assert cache.get("nonexistent") is None
