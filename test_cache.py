#!/usr/bin/env python3
"""Simple test script to verify cache functionality."""

import os
import sys

# Add the driver-assistant directory to Python path
current_dir = os.path.dirname(__file__)
driver_assistant_dir = os.path.join(current_dir, "driver-assistant")
sys.path.insert(0, driver_assistant_dir)

from utils.api_cache import get_cached_or_fetch


def dummy_fetch_function():
    """Dummy function that returns some data."""
    print("🔄 Fetching fresh data...")
    return {"message": "This is fresh data!", "timestamp": "2025-08-27"}


def main():
    print("🧪 Testing cache functionality...")

    # Test cache with a dummy function
    cache_key = "test_cache_key"

    print("\n--- First call (should fetch) ---")
    result1 = get_cached_or_fetch(cache_key, dummy_fetch_function)
    print(f"Result: {result1}")

    print("\n--- Second call (should use cache) ---")
    result2 = get_cached_or_fetch(cache_key, dummy_fetch_function)
    print(f"Result: {result2}")

    print("\n--- Checking cache directory ---")
    from config import TOOL_CACHE_DIR
    from utils.cache import DailyCache

    cache = DailyCache(TOOL_CACHE_DIR)
    cache_files = list(cache.cache_dir.glob("*.json"))
    print(f"Cache directory: {cache.cache_dir}")
    print(f"Cache files found: {len(cache_files)}")
    for file in cache_files:
        print(f"  - {file.name} ({file.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
