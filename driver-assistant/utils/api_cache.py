"""Generic API cache utilities for all tools."""

import os
import sys

# Add the parent directory to Python path for module resolution
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    # Try relative imports first (when imported as module)
    from .cache import DailyCache
    from ..config import TOOL_CACHE_DIR
except ImportError:
    # Fall back to absolute imports (when run directly)
    from utils.cache import DailyCache
    from config import TOOL_CACHE_DIR

# Shared cache instance for all tools
api_cache = DailyCache(TOOL_CACHE_DIR)


from google.adk.agents.invocation_context import InvocationContext


def before_agent_cache(callback_context: InvocationContext):
    """
    Before agent cache callback to check for cached data.

    Args:
        callback_context (CallbackContext): The context for the callback.
    """
    pass


def after_agent_cache(callback_context: InvocationContext):
    """
    After agent cache callback to store fetched data.

    Args:
        callback_context (CallbackContext): The context for the callback.
    """
    pass


def get_cached(cache_key: str):
    """
    Get cached data if available.

    Args:
        cache_key: Unique key for caching this data

    Returns:
        Cached data if available, otherwise None
    """
    try:
        if os.path.exists(api_cache.cache_dir):
            cache_files = os.listdir(api_cache.cache_dir)
            print(f"🔍 [CACHE DEBUG] Cache files found: {cache_files}")
        else:
            print("🔍 [CACHE DEBUG] Cache directory does not exist yet")
    except Exception as e:
        print(f"🔍 [CACHE DEBUG] Error listing cache directory: {e}")

    # Try cache first
    cached_data = api_cache.get(cache_key)
    if cached_data is not None:
        print(f"✅ [CACHE HIT] Found cached data for key: {cache_key}")
    else:
        print(f"❌ [CACHE MISS] No cached data found for key: {cache_key}")
    return cached_data


def set_cached(cache_key: str, data: any):
    """
    Set cached data.

    Args:
        cache_key: Unique key for caching this data
        data: Data to cache
    """
    # Cache the result
    print(f"💾 [CACHE SAVE] Saving data to cache with key: {cache_key}")
    api_cache.set(cache_key, data)

    # Verify the cache was written
    try:
        cache_file_path = api_cache._get_cache_file_path(cache_key)
        print(f"💾 [CACHE SAVE] Cache file path: {cache_file_path}")
        print(
            f"💾 [CACHE SAVE] Cache file exists after write: {os.path.exists(cache_file_path)}"
        )
        if os.path.exists(cache_file_path):
            file_size = os.path.getsize(cache_file_path)
            print(f"💾 [CACHE SAVE] Cache file size: {file_size} bytes")
    except Exception as e:
        print(f"❌ [CACHE ERROR] Error verifying cache file: {e}")


def get_cached_or_fetch(cache_key: str, fetch_function, *args, **kwargs):
    """
    Generic function to get cached data or fetch from API.

    Args:
        cache_key: Unique key for caching this data
        fetch_function: Function to call if cache miss
        *args, **kwargs: Arguments to pass to fetch_function

    Returns:
        Cached data if available, otherwise fresh data from fetch_function
    """
    print(f"🔍 [CACHE DEBUG] Checking cache for key: {cache_key}")
    print(f"🔍 [CACHE DEBUG] Cache directory: {api_cache.cache_dir}")
    print(
        f"🔍 [CACHE DEBUG] Cache directory exists: {os.path.exists(api_cache.cache_dir)}"
    )

    cached_data = get_cached(cache_key)

    if cached_data is not None:
        return cached_data

    print(f"❌ [CACHE MISS] No cached data found for key: {cache_key}")
    print(f"🔄 [CACHE FETCH] Calling fetch function: {fetch_function.__name__}")

    # Cache miss - fetch fresh data
    fresh_data = fetch_function(*args, **kwargs)

    # Cache the fresh data
    set_cached(cache_key, fresh_data)

    return fresh_data


def clear_all_cache():
    """Clear all cached data."""
    api_cache.clear()


def cleanup_old_cache():
    """Remove cache entries that are not from today."""
    return api_cache.cleanup_old()
