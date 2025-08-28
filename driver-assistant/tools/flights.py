"""Flight-related tools for getting peak hours."""

import pandas as pd
import json
from bs4 import BeautifulSoup
from typing import Dict, List
from datetime import datetime, timedelta

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
        Dict[str, any]: status and result or error msg with peak hours per airport.
    """
    try:
        airports_data = {}
        all_flights = []
        successful_airports = []

        # Define airport fetching functions
        airport_fetchers = {
            "Gatwick": _fetch_gatwick_flights,
            "Stansted": _fetch_stansted_flights,
            "Heathrow": _fetch_heathrow_flights,
        }

        # Fetch flights from each airport and analyze individually
        for airport_name, fetch_function in airport_fetchers.items():
            try:
                airport_flights = fetch_function()
                if airport_flights:
                    # Analyze peak hours for this specific airport
                    df_airport = pd.DataFrame(airport_flights)

                    # Remove duplicates
                    df_unique = df_airport.drop_duplicates(
                        subset=["flightNumber", "scheduledTime"]
                    )

                    # Convert scheduled time to hour
                    df_unique["hour"] = pd.to_datetime(
                        df_unique["scheduledTime"], format="%H:%M", errors="coerce"
                    ).dt.hour

                    # Get top 3 peak hours for this airport
                    top_3_peak_hours = df_unique["hour"].value_counts().nlargest(3)

                    # Format the results for this airport
                    peak_hours_list = []
                    for hour, count in top_3_peak_hours.items():
                        peak_hours_list.append(
                            {"Hour": f"{hour:02d}:00", "Count": count}
                        )

                    airports_data[airport_name] = {
                        "status": "success",
                        "peak_hours": peak_hours_list,
                        "total_flights": len(df_unique),
                    }

                    # Add to overall collection
                    all_flights.extend(airport_flights)
                    successful_airports.append(airport_name)
                else:
                    airports_data[airport_name] = {
                        "status": "success",
                        "peak_hours": [],
                        "total_flights": 0,
                        "message": f"No flight data available for {airport_name}",
                    }
            except Exception as e:
                airports_data[airport_name] = {
                    "status": "error",
                    "error_message": f"Failed to fetch data for {airport_name}: {str(e)}",
                }

        if not all_flights:
            return {
                "status": "error",
                "error_message": "No flight data available from any London airports.",
            }
        return {
            "status": "success",
            "airports": airports_data,
            "airports_included": successful_airports,
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


def _fetch_stansted_flights() -> List[Dict]:
    """Fetch flights from Stansted Airport using GraphQL API.

    Returns:
        List[Dict]: List of flight dictionaries
    """
    URL = (
        "https://nihwye5mfbajrg54x3fjcy4q5e.appsync-api.eu-west-1.amazonaws.com/graphql"
    )
    HEADERS = {
        "accept": "*/*",
        "content-type": "application/json",
        "x-api-key": "da2-wr4hf6b2frdfdisv7ugsvdmo3a",
        "Referer": "https://www.stanstedairport.com/",
    }

    # Define the GraphQL query and variables for the next 24 hours
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=24)
    start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    QUERY = """
    query($airportCode: String!, $startDate: AWSDateTime, $endDate: AWSDateTime, $size: Int, $from: Int){
      allArrivalsWithinMonth(tenant: $airportCode, startDate: $startDate, endDate: $endDate, size: $size from: $from){
        scheduledArrivalDateTime
        departureAirport {
          cityName
          code
        }
        flightNumber
        airline {
          name
        }
        status
      }
    }
    """

    VARIABLES = {
        "airportCode": "STN",
        "startDate": start_time_str,
        "endDate": end_time_str,
        "size": 1000,
    }

    PAYLOAD = {"query": QUERY, "variables": VARIABLES}

    try:
        response = requests.post(URL, headers=HEADERS, json=PAYLOAD, timeout=15)

        if response.status_code != 200:
            return []

        data = response.json()
        flights = data.get("data", {}).get("allArrivalsWithinMonth", [])

        if not flights:
            return []

        # Convert to the expected format
        stansted_flights = []
        for flight in flights:
            try:
                # Parse the scheduled arrival time and extract just the time part
                arrival_datetime = pd.to_datetime(flight["scheduledArrivalDateTime"])
                scheduled_time = arrival_datetime.strftime("%H:%M")

                stansted_flights.append(
                    {
                        "scheduledTime": scheduled_time,
                        "origin": flight.get("departureAirport", {}).get(
                            "cityName", "Unknown"
                        ),
                        "flightNumber": flight.get("flightNumber", "Unknown"),
                        "status": flight.get("status", "Unknown"),
                        "airport": "Stansted",
                    }
                )
            except (AttributeError, KeyError, TypeError):
                continue

        return stansted_flights

    except requests.RequestException:
        return []


def _fetch_heathrow_flights() -> List[Dict]:
    """Fetch flights from Heathrow Airport using their API.

    Returns:
        List[Dict]: List of flight dictionaries
    """
    from datetime import datetime

    # Use current date for the API
    current_date = datetime.now().strftime("%Y-%m-%d")

    URL = f"https://api-dp-prod.dp.heathrow.com/pihub/flights/arrivals?date={current_date}&orderBy=localArrivalTime&excludeCodeShares=true"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "origin": "https://www.heathrow.com",
        "referer": "https://www.heathrow.com/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        # NOTE: The cookie is session-specific and may expire.
        "cookie": "CONSENTMGR=consent:true%7Cts:1756377776050%7Cid:0198f045f0d90008b45c0df7b81505075002106d009dc; AMCVS_FCD067055294DE7D0A490D44%40AdobeOrg=1; AMCV_FCD067055294DE7D0A490D44%40AdobeOrg=179643557%7CMCIDTS%7C20329%7CMCMID%7C36535854847972742273654252358522731734%7CMCAAMLH-1756982576%7C6%7CMCAAMB-1756982576%7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y%7CMCOPTOUT-1756384976s%7CNONE%7CvVersion%7C5.5.0; gpv_pn=en%20%7C%20heathrowairport%20%7C%20en%20%7C%20arrivals; gpv_url=https%3A%2F%2Fwww.heathrow.com%2Farrivals; s_cc=true; utag_main=v_id:0198f045f0d90008b45c0df7b81505075002106d009dc$_sn:1$_se:2$_ss:0$_st:1756379587333$ses_id:1756377772249%3Bexp-session$_pn:2%3Bexp-session; _cs_mk=0.34966660639990244_1756377787355",
    }

    try:
        response = requests.get(URL, headers=headers, timeout=15)

        if response.status_code != 200:
            return []

        flight_data = response.json()

        if not flight_data:
            return []

        # Convert to the expected format
        heathrow_flights = []
        for flight in flight_data:
            try:
                flight_service = flight["flightService"]
                route_info = flight_service["aircraftMovement"]["route"]["portsOfCall"]

                # Find the origin and destination details from the list of ports
                origin_port = next(
                    (p for p in route_info if p.get("portOfCallType") == "ORIGIN"), None
                )
                dest_port = next(
                    (p for p in route_info if p.get("portOfCallType") == "DESTINATION"),
                    None,
                )

                if not dest_port:
                    continue  # Skip if no destination is found

                # Parse the scheduled arrival time and extract just the time part
                arrival_time_str = dest_port["operatingTimes"]["scheduled"]["local"]
                arrival_datetime = pd.to_datetime(arrival_time_str)
                scheduled_time = arrival_datetime.strftime("%H:%M")

                heathrow_flights.append(
                    {
                        "scheduledTime": scheduled_time,
                        "origin": (
                            origin_port["airportFacility"]["iataIdentifier"]
                            if origin_port
                            else "N/A"
                        ),
                        "flightNumber": flight_service.get(
                            "iataFlightIdentifier", "Unknown"
                        ),
                        "status": "Scheduled",  # Heathrow API doesn't provide status in the same format
                        "airport": "Heathrow",
                    }
                )
            except (KeyError, TypeError, AttributeError):
                continue

        return heathrow_flights

    except requests.RequestException:
        return []


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
