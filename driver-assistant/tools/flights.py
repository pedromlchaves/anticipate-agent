"""Flight-related tools for getting peak hours."""

import pandas as pd
import json
from bs4 import BeautifulSoup
from typing import Dict, List

from ..config import AIRPORT_CODE_MAPPING
from ..utils.web_scraping import get_headless_chrome_driver
from ..utils.api_cache import get_cached_or_fetch
import requests


def get_flight_peak_hours(city: str) -> Dict[str, any]:
    """Returns the peak hours for flights in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the peak hours.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    # Handle specific cities with dedicated implementations
    if city.lower() == "london":
        return get_london_flight_peak_hours()
    elif city.lower() == "porto":
        return get_porto_flight_peak_hours()


def get_porto_flight_peak_hours() -> Dict[str, any]:
    """Returns the peak hours for flights in Porto.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    # Use cache key for Porto flights
    cache_key = "porto_flight_peak_hours"

    return get_cached_or_fetch(cache_key, _fetch_porto_flight_peak_hours)


def _fetch_porto_flight_peak_hours() -> Dict[str, any]:
    """Internal function to fetch flight data from Porto airport (without caching).

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    try:
        airport_code = AIRPORT_CODE_MAPPING.get("Porto")
        print("Fetched this airport code", airport_code)
        if not airport_code:
            return {
                "status": "error",
                "error_message": "Airport information for 'Porto' is not available.",
            }

        url = "https://api.flightradar24.com/common/v1/airport.json?code=opo&plugin[]=&plugin-setting[schedule][mode]=arrivals&plugin-setting[schedule][timestamp]=1756389803&page=1&limit=100&fleet=&token="

        driver = get_headless_chrome_driver()
        driver.get(url)

        soup = BeautifulSoup(driver.page_source, features="html.parser")
        driver.quit()

        # Extract the JSON text from the soup body content
        text = soup.find("pre").text
        data = json.loads(text)
        flights = data["result"]["response"]["airport"]["pluginData"]["schedule"][
            "arrivals"
        ]["data"]

        print("Successfully fetched Porto flight data!")
        print(f"Found {len(flights)} flights")

        df = pd.json_normalize(flights)
        df_simple = df[
            [
                "flight.identification.number.default",
                "flight.airline.name",
                "flight.airport.origin.code.iata",
                "flight.status.text",
                "flight.time.scheduled.arrival",
            ]
        ].rename(
            columns={
                "flight.identification.number.default": "flight_number",
                "flight.airline.name": "airline",
                "flight.airport.origin.code.iata": "origin",
                "flight.status.text": "status",
                "flight.time.scheduled.arrival": "arrival_timestamp",
            }
        )

        # 3. Convert the arrival timestamp into a readable datetime
        # The 'unit="s"' tells pandas the number is in seconds
        df_simple["arrival_time"] = pd.to_datetime(
            df_simple["arrival_timestamp"], unit="s", utc=True
        )

        print("--- Parsed DataFrame ---")
        print(df_simple)

        # 4. Convert to the local timezone of the airport (Porto is Europe/Lisbon)
        df_simple["arrival_time_local"] = df_simple["arrival_time"].dt.tz_convert(
            "Europe/Lisbon"
        )

        # 5. Extract the hour from the local time
        df_simple["hour"] = df_simple["arrival_time_local"].dt.hour

        # 6. Count the flights per hour and get the top 3
        top_3_peak_hours = df_simple["hour"].value_counts().nlargest(3)
        return {
            "status": "success",
            "peak_hours": str(top_3_peak_hours),
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Peak hours information for 'Porto' is not available. The exception was {str(e)}.",
        }


def clear_porto_flight_cache() -> Dict[str, any]:
    """Clear Porto flight cache.

    Returns:
        Dict[str, any]: Status of cache clearing operation
    """
    try:
        from ..utils.api_cache import api_cache

        cache_key = "porto_flight_peak_hours"
        api_cache.delete(cache_key)
        return {"status": "success", "message": "Porto flight cache cleared"}

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to clear Porto flight cache: {str(e)}",
        }


def get_london_flight_peak_hours() -> Dict[str, any]:
    """Returns the peak hours for flights in London (aggregated from all airports).

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    # Use cache key for London flights
    cache_key = "london_flight_peak_hours"

    return get_cached_or_fetch(cache_key, _fetch_london_flight_peak_hours)


def _fetch_london_flight_peak_hours() -> Dict[str, any]:
    """Internal function to fetch flight data from all London airports (without caching).

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    try:
        all_flights = []

        # Fetch flights from Gatwick
        gatwick_flights = _fetch_gatwick_flights()
        if gatwick_flights:
            all_flights.extend(gatwick_flights)

        # Add other airports here when provided
        # heathrow_flights = _fetch_heathrow_flights()
        # luton_flights = _fetch_luton_flights()
        # stansted_flights = _fetch_stansted_flights()

        if not all_flights:
            return {
                "status": "error",
                "error_message": "No flight data available from any London airports.",
            }

        # Create DataFrame and analyze peak hours
        df = pd.DataFrame(all_flights)

        # Remove duplicates based on flight number and scheduled time
        df_unique = df.drop_duplicates(subset=["flightNumber", "scheduledTime"])

        # Convert scheduled time to hour
        df_unique["hour"] = pd.to_datetime(
            df_unique["scheduledTime"], format="%H:%M", errors="coerce"
        ).dt.hour

        # Get top 3 peak hours
        top_3_peak_hours = df_unique["hour"].value_counts().nlargest(3)

        # Format the results
        peak_hours_list = []
        for hour, count in top_3_peak_hours.items():
            peak_hours_list.append({"Hour": f"{hour:02d}:00", "Count": count})

        return {
            "status": "success",
            "peak_hours": str(peak_hours_list),
            "total_flights": len(df_unique),
            "airports_included": ["Gatwick"],  # Update when adding more airports
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Peak hours information for London flights is not available. The exception was {str(e)}.",
        }


def _fetch_gatwick_flights() -> List[Dict]:
    """Fetch flights from Gatwick Airport.

    Returns:
        List[Dict]: List of flight dictionaries
    """
    BASE_URL = "https://www.gatwickairport.com/on/demandware.store/Sites-Gatwick-Site/en_GB/LiveFlights-FetchFlights"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def fetch_page_flights(page_num):
        """Fetch flights from a specific page number."""
        params = {"page": page_num, "terminal": "all", "destination": "A", "search": ""}

        try:
            response = requests.get(
                BASE_URL, headers=HEADERS, params=params, timeout=15
            )
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.content, "html.parser")
            flight_rows = soup.find_all("tr", class_="flight-line")

            page_flights = []
            for row in flight_rows:
                try:
                    time = row.find("td", class_="time").text.strip()
                    origin = row.find("td", class_="destination").text.strip()

                    desktop_cells = row.find_all("td", class_="d-none d-md-table-cell")
                    flight_number = desktop_cells[0].text.strip()
                    status = desktop_cells[1].text.strip()

                    page_flights.append(
                        {
                            "scheduledTime": time,
                            "origin": origin,
                            "flightNumber": flight_number,
                            "status": status,
                            "airport": "Gatwick",
                        }
                    )
                except (AttributeError, IndexError):
                    continue

            return page_flights
        except requests.RequestException:
            return []

    all_flights = []

    # Start with page 0
    current_page = 0
    flights = fetch_page_flights(current_page)
    if flights:
        all_flights.extend(flights)

    # Fetch positive pages (1, 2, 3, ...)
    page = 1
    while True:
        flights = fetch_page_flights(page)
        if not flights:
            break
        all_flights.extend(flights)
        page += 1

    # Fetch negative pages (-1, -2, -3, ...)
    page = -1
    while True:
        flights = fetch_page_flights(page)
        if not flights:
            break
        all_flights.extend(flights)
        page -= 1

    return all_flights


def clear_london_flight_cache() -> Dict[str, any]:
    """Clear London flight cache.

    Returns:
        Dict[str, any]: Status of cache clearing operation
    """
    try:
        from ..utils.api_cache import api_cache

        cache_key = "london_flight_peak_hours"
        api_cache.delete(cache_key)
        return {"status": "success", "message": "London flight cache cleared"}

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to clear London flight cache: {str(e)}",
        }
