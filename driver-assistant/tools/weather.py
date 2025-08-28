"""Weather-related tools."""

import requests
import pandas as pd
import datetime
from typing import Dict

from ..config import CITY_CODE_MAPPING
from ..utils.api_cache import get_cached_or_fetch


def get_daily_city_weather(city: str) -> Dict[str, any]:
    """Returns the daily weather for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    cache_key = f"weather_{city.lower()}"
    return get_cached_or_fetch(cache_key, _fetch_daily_city_weather, city)


def _fetch_daily_city_weather(city: str) -> Dict[str, any]:
    """Internal function to fetch weather data from API (without caching).

    Args:
        city (str): The name of the city for which to retrieve the weather.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    """Returns the daily weather for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    try:
        city_code = CITY_CODE_MAPPING.get(city)
        if not city_code:
            return {
                "status": "error",
                "error_message": f"Weather information for '{city}' is not available.",
            }

        response = requests.get(
            f"https://api.ipma.pt/public-data/forecast/aggregate/{city_code}.json"
        )
        data = response.json()
        df = pd.DataFrame(data)

        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        df_today = df[df["dataPrev"].str.startswith(today_str)]
        desired_columns = [
            "dataPrev",
            "tMin",
            "tMax",
            "tMed",
            "probabilidadePrecipita",
            "idIntensidadePrecipita",
        ]
        available_columns = [col for col in desired_columns if col in df_today.columns]
        df_today = df_today[available_columns]

        forecast = str(df_today.to_dict(orient="records"))
        return {
            "status": "success",
            "weather": forecast,
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
        }


def clear_weather_cache(city: str = None) -> Dict[str, any]:
    """Clear weather cache.

    Args:
        city (str, optional): Specific city cache to clear.

    Returns:
        Dict[str, any]: Status of cache clearing operation
    """
    try:
        from ..utils.api_cache import api_cache

        if city:
            # Clear specific city cache
            cache_key = f"weather_{city.lower()}"
            api_cache.delete(cache_key)
            return {"status": "success", "message": f"Weather cache cleared for {city}"}
        else:
            # Clear all weather cache - let cleanup handle it
            return {
                "status": "success",
                "message": "Use cleanup_old_cache() to clear all old weather data",
            }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to clear weather cache: {str(e)}",
        }
