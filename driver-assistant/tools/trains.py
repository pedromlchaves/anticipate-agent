"""Train-related tools for getting peak hours."""

import requests
import pandas as pd
from typing import Dict, Any
import os

from ..config import (
    LONDON_STATIONS,
    PORTO_STATIONS,
    TRANSPORT_API_BASE_URL,
    CP_API_BASE_URL,
)

TRANSPORT_API_ID = os.getenv("TRANSPORT_API_ID")
TRANSPORT_API_KEY = os.getenv("TRANSPORT_API_KEY")


def get_london_train_peak_hours() -> Dict[str, Any]:
    """Get peak hours for all major London train stations.

    Returns:
        Dict[str, Any]: Dictionary containing peak hours for all London stations
    """
    results = {
        "status": "success",
        "city": "London",
        "stations": {},
        "summary": {
            "total_stations": len(LONDON_STATIONS),
            "successful_stations": 0,
            "failed_stations": 0,
        },
    }

    for station_code, station_name in LONDON_STATIONS.items():
        try:
            # The TransportAPI endpoint for station timetables
            base_url = f"{TRANSPORT_API_BASE_URL}/{station_code}/timetable.json"

            # Set the parameters for the API request
            params = {
                "app_id": TRANSPORT_API_ID,
                "app_key": TRANSPORT_API_KEY,
                "train_status": "passenger",
                "type": "arrival",
            }

            # Make the GET request
            response = requests.get(base_url, params=params)
            response.raise_for_status()

            # Parse the JSON response
            data = response.json()
            arrivals = data.get("arrivals", {}).get("all", [])

            if not arrivals:
                results["stations"][station_code] = {
                    "status": "success",
                    "station_name": station_name,
                    "peak_hours": [],
                    "total_trains": 0,
                    "message": f"No arrivals found for {station_name}",
                }
                results["summary"]["successful_stations"] += 1
                continue

            # Convert to DataFrame and analyze peak hours
            df_arrivals = pd.DataFrame(arrivals)

            if "aimed_arrival_time" not in df_arrivals.columns:
                results["stations"][station_code] = {
                    "status": "error",
                    "station_name": station_name,
                    "error_message": "Arrival time data not available",
                }
                results["summary"]["failed_stations"] += 1
                continue

            # Convert arrival time to datetime
            df_arrivals["aimed_arrival_time"] = pd.to_datetime(
                df_arrivals["aimed_arrival_time"]
            )

            # Group by hour and count trains
            hourly_counts = df_arrivals.groupby(
                df_arrivals["aimed_arrival_time"].dt.hour
            ).size()

            # Format results
            hourly_counts_df = hourly_counts.reset_index()
            hourly_counts_df.columns = ["Hour", "Train_Count"]
            hourly_counts_df["Hour"] = hourly_counts_df["Hour"].apply(
                lambda x: f"{x:02d}:00"
            )

            # Sort by train count to get peak hours
            peak_hours = hourly_counts_df.sort_values("Train_Count", ascending=False)
            top_3_peak_hours = peak_hours.head(3)

            results["stations"][station_code] = {
                "status": "success",
                "station_name": station_name,
                "peak_hours": top_3_peak_hours.to_dict(orient="records"),
                "total_trains": len(arrivals),
            }
            results["summary"]["successful_stations"] += 1

        except requests.exceptions.RequestException as e:
            results["stations"][station_code] = {
                "status": "error",
                "station_name": station_name,
                "error_message": f"API request failed: {str(e)}",
            }
            results["summary"]["failed_stations"] += 1
        except Exception as e:
            results["stations"][station_code] = {
                "status": "error",
                "station_name": station_name,
                "error_message": f"Analysis failed: {str(e)}",
            }
            results["summary"]["failed_stations"] += 1

    return results


def get_porto_train_peak_hours() -> Dict[str, Any]:
    """Get peak hours for all Porto train stations.

    Returns:
        Dict[str, Any]: Dictionary containing peak hours for all Porto stations
    """
    results = {
        "status": "success",
        "city": "Porto",
        "stations": {},
        "summary": {
            "total_stations": len(PORTO_STATIONS),
            "successful_stations": 0,
            "failed_stations": 0,
        },
    }

    for station_code, station_name in PORTO_STATIONS.items():
        try:
            # Use CP API for Portuguese stations
            response = requests.get(f"{CP_API_BASE_URL}?stationId={station_code}")
            response.raise_for_status()
            print(f"Response for {station_name}: {response.status_code}")
            df = pd.DataFrame(response.json())

            if df.empty:
                results["stations"][station_code] = {
                    "status": "success",
                    "station_name": station_name,
                    "peak_hours": [],
                    "total_trains": 0,
                    "message": f"No train data available for {station_name}",
                }
                results["summary"]["successful_stations"] += 1
                continue

            # Convert arrivalTime to datetime and group by hour
            df["arrivalTime"] = pd.to_datetime(df["arrivalTime"], errors="coerce")

            # Remove rows with invalid datetime (NaT values)
            df = df.dropna(subset=["arrivalTime"])

            if df.empty:
                results["stations"][station_code] = {
                    "status": "success",
                    "station_name": station_name,
                    "peak_hours": [],
                    "total_trains": 0,
                    "message": f"No valid arrival times for {station_name}",
                }
                results["summary"]["successful_stations"] += 1
                continue

            hourly_counts = df.groupby(df["arrivalTime"].dt.hour).size()

            # Create a more readable format
            hourly_counts_df = hourly_counts.reset_index()
            hourly_counts_df.columns = ["Hour", "Train_Count"]

            # Fix the hour formatting by ensuring integers and handling any NaN values
            hourly_counts_df["Hour"] = (
                hourly_counts_df["Hour"]
                .fillna(0)
                .astype(int)
                .apply(lambda x: f"{x:02d}:00")
            )

            # Sort by train count to get peak hours
            peak_hours = hourly_counts_df.sort_values("Train_Count", ascending=False)
            top_3_peak_hours = peak_hours.head(3)

            results["stations"][station_code] = {
                "status": "success",
                "station_name": station_name,
                "peak_hours": top_3_peak_hours.to_dict(orient="records"),
                "total_trains": len(df),
            }
            results["summary"]["successful_stations"] += 1

        except Exception as e:
            results["stations"][station_code] = {
                "status": "error",
                "station_name": station_name,
                "error_message": f"Failed to get data: {str(e)}",
            }
            results["summary"]["failed_stations"] += 1

    return results


def get_train_peak_hours(city: str) -> Dict[str, Any]:
    """Get peak hours for train stations in the specified city.

    This function serves as a unified entry point for retrieving train peak hours
    data across different cities and transportation systems. It automatically
    routes to the appropriate city-specific implementation based on the input city.

    The function analyzes train arrival data from multiple stations within the
    specified city to identify the top 3 peak hours (busiest times) based on
    the number of train arrivals. This information is valuable for ride-sharing
    drivers to understand when passenger demand is likely to be highest near
    train stations.

    Supported Cities and Data Sources:
    - London: Uses UK's TransportAPI to analyze 8 major rail hubs including
      London Liverpool Street (LST), Paddington (PAD), Waterloo (WAT),
      Victoria (VIC), London Bridge (LBG), Euston (EUS), King's Cross (KGX),
      and Charing Cross (CHX). These are the busiest stations in the UK
      where both National Rail and Underground networks intersect.

    - Porto: Uses Portuguese CP (Comboios de Portugal) API to analyze
      Porto Campanhã (94-50100) and Porto São Bento (94-1008) stations,
      which are the main railway hubs in Porto connecting the city to
      national and regional destinations.

    Peak Hours Analysis:
    The function groups train arrivals by hour (00:00-23:00) and counts the
    frequency of arrivals. It then identifies the top 3 hours with the highest
    number of arrivals as "peak hours". This data helps drivers understand:
    - When stations will have the most passenger traffic
    - Optimal times to position near train stations for pickups
    - High-demand periods for ride-sharing services

    Args:
        city (str): The name of the city for which to retrieve train peak hours.
                   Must be one of the supported cities:
                   - "London" (case-insensitive): Analyzes all major London stations
                   - "Porto" (case-insensitive): Analyzes Porto train stations

    Returns:
        Dict[str, Any]: A comprehensive dictionary containing peak hours analysis
                       with the following structure:

        Success Response:
        {
            "status": "success",
            "city": str,  # The analyzed city name
            "stations": {
                "station_code": {
                    "status": "success",
                    "station_name": str,  # Human-readable station name
                    "peak_hours": [  # Top 3 peak hours, sorted by train count
                        {
                            "Hour": str,  # Format "HH:00" (e.g., "08:00")
                            "Train_Count": int  # Number of trains in that hour
                        },
                        # ... up to 3 peak hours
                    ],
                    "total_trains": int,  # Total number of trains analyzed
                },
                # ... more stations
            },
            "summary": {
                "total_stations": int,      # Number of stations analyzed
                "successful_stations": int, # Stations with successful data retrieval
                "failed_stations": int      # Stations that failed analysis
            }
        }

        Error Response:
        {
            "status": "error",
            "error_message": str,  # Detailed error description
            "supported_cities": List[str]  # List of cities that are supported
        }

        Individual Station Error (within success response):
        {
            "status": "error",
            "station_name": str,
            "error_message": str  # Specific error for this station
        }

    Raises:
        No exceptions are raised directly. All errors are captured and returned
        in the response dictionary with appropriate error messages.

    Example Usage:
        >>> result = get_train_peak_hours("London")
        >>> if result["status"] == "success":
        ...     for station_code, data in result["stations"].items():
        ...         if data["status"] == "success":
        ...             print(f"{data['station_name']} peak hours:")
        ...             for hour in data["peak_hours"]:
        ...                 print(f"  {hour['Hour']}: {hour['Train_Count']} trains")

        >>> result = get_train_peak_hours("Porto")
        >>> print(f"Total stations analyzed: {result['summary']['total_stations']}")

    API Dependencies:
        - London: Requires TRANSPORT_API_ID and TRANSPORT_API_KEY environment
          variables for accessing UK's TransportAPI (transportapi.com)
        - Porto: Uses public CP API, no authentication required

    Data Freshness:
        - The function retrieves real-time or near real-time arrival data
        - Peak hours are calculated based on current day's scheduled arrivals
        - Results may vary throughout the day as schedules update

    Performance Considerations:
        - London analysis queries 8 different API endpoints sequentially
        - Porto analysis queries 2 different API endpoints sequentially
        - Total execution time depends on API response times
        - Failed stations don't block analysis of other stations
    """
    # Normalize city name for comparison (case-insensitive)
    city_normalized = city.strip().lower()

    # Route to appropriate city-specific function
    if city_normalized == "london":
        return get_london_train_peak_hours()
    elif city_normalized == "porto":
        return get_porto_train_peak_hours()
    else:
        # Return error for unsupported cities
        supported_cities = ["London", "Porto"]
        return {
            "status": "error",
            "error_message": f"City '{city}' is not supported for train peak hours analysis. "
            f"Please use one of the supported cities: {', '.join(supported_cities)}",
            "supported_cities": supported_cities,
            "requested_city": city,
        }
