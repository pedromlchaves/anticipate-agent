"""Comprehensive cache management for all tools."""

from typing import Dict, Any
from .api_cache import api_cache, clear_all_cache, cleanup_old_cache


def get_cache_status() -> Dict[str, Any]:
    """Get comprehensive cache status for all tools.

    Returns:
        Dict[str, Any]: Status information for cache system
    """
    try:
        from pathlib import Path
        from datetime import date

        cache_dir = Path(api_cache.cache_dir)

        if not cache_dir.exists():
            return {
                "status": "success",
                "cache_dir": str(cache_dir),
                "total_files": 0,
                "today_files": 0,
                "old_files": 0,
                "message": "Cache directory doesn't exist yet",
            }

        cache_files = list(cache_dir.glob("*.json"))
        total_files = len(cache_files)

        today_str = str(date.today())
        today_files = 0
        old_files = 0

        for cache_file in cache_files:
            try:
                import json

                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                if cache_data.get("date") == today_str:
                    today_files += 1
                else:
                    old_files += 1
            except Exception:
                old_files += 1  # Count corrupted files as old

        return {
            "status": "success",
            "cache_dir": str(cache_dir),
            "total_files": total_files,
            "today_files": today_files,
            "old_files": old_files,
            "current_date": today_str,
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get cache status: {str(e)}",
        }


def clear_all_tool_cache() -> Dict[str, Any]:
    """Clear all cache for all tools.

    Returns:
        Dict[str, Any]: Status of cache clearing operation
    """
    try:
        clear_all_cache()
        return {"status": "success", "message": "All tool cache cleared successfully"}
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to clear all cache: {str(e)}",
        }


def cleanup_old_cache_all_tools() -> Dict[str, Any]:
    """Clean up old cache entries for all tools.

    Returns:
        Dict[str, Any]: Status and count of cleaned up entries
    """
    try:
        removed_count = cleanup_old_cache()
        return {
            "status": "success",
            "message": f"Cleaned up {removed_count} old cache entries across all tools",
            "removed_count": removed_count,
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to cleanup old cache: {str(e)}",
        }


def clear_cache_by_tool(tool_name: str) -> Dict[str, Any]:
    """Clear cache for a specific tool.

    Args:
        tool_name (str): Name of the tool ('trains', 'flights', 'weather', 'events')

    Returns:
        Dict[str, Any]: Status of cache clearing operation
    """
    try:
        tool_name = tool_name.lower()

        if tool_name == "trains":
            from ..tools.trains import clear_train_cache

            return clear_train_cache()
        elif tool_name == "flights":
            from ..tools.flights import clear_flight_cache

            return clear_flight_cache()
        elif tool_name == "weather":
            from ..tools.weather import clear_weather_cache

            return clear_weather_cache()
        elif tool_name == "events":
            from ..tools.events import clear_events_cache

            return clear_events_cache()
        else:
            return {
                "status": "error",
                "error_message": f"Unknown tool '{tool_name}'. Available tools: trains, flights, weather, events",
            }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to clear {tool_name} cache: {str(e)}",
        }
