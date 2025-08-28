"""Flight-related tools for getting peak hours."""

import pandas as pd
import json
from bs4 import BeautifulSoup
from typing import Dict

from ..config import AIRPORT_CODE_MAPPING
from ..utils.web_scraping import get_headless_chrome_driver
from ..utils.api_cache import get_cached_or_fetch


def get_flight_peak_hours(city: str) -> Dict[str, any]:
    """Returns the peak hours for flights in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the peak hours.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    # Use cache key based on city and date
    cache_key = f"flight_peak_hours_{city.lower()}"

    return get_cached_or_fetch(cache_key, _fetch_flight_peak_hours, city)


def _fetch_flight_peak_hours(city: str) -> Dict[str, any]:
    """Internal function to fetch flight data from API (without caching).

    Args:
        city (str): The name of the city for which to retrieve the peak hours.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    """Returns the peak hours for flights in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the peak hours.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    try:
        airport_code = AIRPORT_CODE_MAPPING.get(city)
        if not airport_code:
            return {
                "status": "error",
                "error_message": f"Airport information for '{city}' is not available.",
            }

        url = (
            "https://www.aeroportoporto.pt/en/flights_proxy?day=hoje&movtype=A&IATA="
            + airport_code
        )

        driver = get_headless_chrome_driver()
        driver.get(url)

        soup = BeautifulSoup(driver.page_source, features="html.parser")
        driver.quit()

        df = pd.DataFrame(json.loads(soup.body.contents[0])["flights"])

        # Convert 'time' column to datetime if it's not already
        df["time"] = pd.to_datetime(df["time"])

        # Group by hour and count occurrences
        hourly_counts = df.groupby(df["time"].dt.hour).size().reset_index(name="Count")

        # Optional: format hour as HH:00
        hourly_counts["Hour"] = hourly_counts["time"].apply(lambda x: f"{x:02d}:00")
        hourly_counts = hourly_counts[["Hour", "Count"]]
        hourly_counts = hourly_counts.to_dict(orient="records")
        return {
            "status": "success",
            "peak_hours": str(hourly_counts),
        }

    except Exception as e:

        return {
            "status": "error",
            "error_message": f"Peak hours information for '{city}' is not available. The exception was {str(e)}.",
        }


def clear_flight_cache(city: str = None) -> Dict[str, any]:
    """Clear flight cache.

    Args:
        city (str, optional): Specific city cache to clear.

    Returns:
        Dict[str, any]: Status of cache clearing operation
    """
    try:
        from ..utils.api_cache import api_cache

        if city:
            # Clear specific city cache
            cache_key = f"flight_peak_hours_{city.lower()}"
            api_cache.delete(cache_key)
            return {"status": "success", "message": f"Flight cache cleared for {city}"}
        else:
            # Clear all flight cache - let cleanup handle it
            return {
                "status": "success",
                "message": "Use cleanup_old_cache() to clear all old flight data",
            }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to clear flight cache: {str(e)}",
        }
