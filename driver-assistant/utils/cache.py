"""Simple file-based caching utility for API responses."""

import json
from datetime import date
from pathlib import Path
from typing import Any, Optional
import hashlib


class DailyCache:
    """A simple file-based cache that refreshes daily."""

    def __init__(self, cache_dir: str):
        """
        Initialize the cache.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, key: str) -> str:
        """Generate a safe filename from the cache key."""
        # Use MD5 hash to ensure safe filenames
        return hashlib.md5(key.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """Get the full path for a cache file."""
        safe_key = self._get_cache_key(key)
        return self.cache_dir / f"{safe_key}.json"

    def _get_cache_file_path(self, key: str) -> str:
        """Get the full path for a cache file as string (for external use)."""
        return str(self._get_cache_path(key))

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache if it's from today.

        Args:
            key: Cache key

        Returns:
            Cached value if exists and is from today, None otherwise
        """
        cache_path = self._get_cache_path(key)
        print(f"🔍 [CACHE GET] Looking for cache file: {cache_path}")

        if not cache_path.exists():
            print(f"❌ [CACHE GET] Cache file does not exist: {cache_path}")
            return None

        print(f"✅ [CACHE GET] Cache file exists: {cache_path}")

        try:
            with open(cache_path, "r") as f:
                cache_data = json.load(f)

            # Check if cache is from today
            cached_date = cache_data.get("date")
            today_str = str(date.today())
            print(f"🔍 [CACHE GET] Cached date: {cached_date}, Today: {today_str}")

            if cached_date != today_str:
                print(f"❌ [CACHE GET] Cache is outdated, removing file: {cache_path}")
                # Remove outdated cache file
                cache_path.unlink(missing_ok=True)
                return None

            print("✅ [CACHE GET] Cache is fresh, returning data")
            return cache_data.get("data")

        except (json.JSONDecodeError, KeyError, OSError) as e:
            print(f"❌ [CACHE GET] Error reading cache file: {e}")
            # If there's any issue reading the cache, remove the file
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in cache with today's date.

        Args:
            key: Cache key
            value: Value to cache
        """
        cache_path = self._get_cache_path(key)
        today_str = str(date.today())

        print(f"💾 [CACHE SET] Saving to cache file: {cache_path}")
        print(f"💾 [CACHE SET] Cache directory: {self.cache_dir}")
        print(f"💾 [CACHE SET] Date: {today_str}")

        cache_data = {"data": value, "date": today_str}

        try:
            # Ensure cache directory exists
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"💾 [CACHE SET] Cache directory created/exists: {self.cache_dir}")

            with open(cache_path, "w") as f:
                json.dump(cache_data, f, indent=2, default=str)

            print(f"✅ [CACHE SET] Successfully saved cache file: {cache_path}")

            # Verify the file was written
            if cache_path.exists():
                file_size = cache_path.stat().st_size
                print(f"✅ [CACHE SET] Cache file verified, size: {file_size} bytes")
            else:
                print("❌ [CACHE SET] Cache file was not created!")

        except OSError as e:
            print(f"❌ [CACHE SET] Error writing cache file: {e}")
            # If we can't write to cache, just continue without caching
            pass

    def delete(self, key: str) -> None:
        """Delete a cache entry."""
        cache_path = self._get_cache_path(key)
        cache_path.unlink(missing_ok=True)

    def clear(self) -> None:
        """Clear all cache entries."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink(missing_ok=True)

    def cleanup_old(self) -> int:
        """
        Remove all cache entries that are not from today.

        Returns:
            Number of old entries removed
        """
        removed_count = 0
        today_str = str(date.today())

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                if cache_data.get("date") != today_str:
                    cache_file.unlink()
                    removed_count += 1

            except (json.JSONDecodeError, KeyError, OSError):
                # Remove corrupted cache files
                cache_file.unlink(missing_ok=True)
                removed_count += 1

        return removed_count
