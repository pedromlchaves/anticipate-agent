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
    # Handle specific cities with dedicated implementations
    if city.lower() == "london":
        return get_london_weather()
    elif city.lower() == "porto":
        return get_porto_weather()

    # Fallback for other cities using the old implementation
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


def get_porto_weather() -> Dict[str, any]:
    """Returns the daily weather for Porto.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    cache_key = "porto_weather"
    return get_cached_or_fetch(cache_key, _fetch_porto_weather)


def _fetch_porto_weather() -> Dict[str, any]:
    """Internal function to fetch weather data from Porto API (without caching).

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    try:
        city_code = CITY_CODE_MAPPING.get("Porto")
        if not city_code:
            return {
                "status": "error",
                "error_message": "Weather information for Porto is not available.",
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


def get_london_weather() -> Dict[str, any]:
    """Returns the daily weather for London.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    cache_key = "london_weather"
    return get_cached_or_fetch(cache_key, _fetch_london_weather)


def _fetch_london_weather() -> Dict[str, any]:
    """Internal function to fetch weather data from London API (without caching).

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    try:
        response = requests.get(
            "https://weather-broker-cdn.api.bbci.co.uk/en/forecast/aggregated/2643743"
        )
        response.raise_for_status()
        data = response.json()

        return {
            "status": "success",
            "weather": data,
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
            # Clear specific city cache using dedicated cache keys
            if city.lower() == "london":
                cache_key = "london_weather"
            elif city.lower() == "porto":
                cache_key = "porto_weather"
            else:
                # Fallback for other cities
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
