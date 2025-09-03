"""Bus-related tools for getting GTFS data and peak hours from bus stops."""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import pandas as pd

from ..utils.api_cache import get_cached_or_fetch
from ..config import GTFS_DATA_DIR


class GTFSAnalyzer:
    """GTFS Analyzer for bus data."""

    def __init__(self, gtfs_folder: str = None):
        """
        Initialize the GTFS analyzer.

        Args:
            gtfs_folder: Path to the GTFS data folder. If None, uses config default.
        """
        self.gtfs_folder = gtfs_folder or GTFS_DATA_DIR
        self.stops_df = None
        self.stop_times_df = None
        self.trips_df = None
        self.calendar_dates_df = None
        self.calendar_df = None

        # Define city boundaries (approximate coordinates)
        self.city_boundaries = {
            "porto": {
                "lat_min": 41.02,
                "lat_max": 41.27,
                "lon_min": -8.75,
                "lon_max": -8.45,
            },
            "london": {
                "lat_min": 51.28,
                "lat_max": 51.70,
                "lon_min": -0.52,
                "lon_max": 0.33,
            },
            "lisbon": {
                "lat_min": 38.68,
                "lat_max": 38.83,
                "lon_min": -9.25,
                "lon_max": -9.05,
            },
            "berlin": {
                "lat_min": 52.33,
                "lat_max": 52.67,
                "lon_min": 13.09,
                "lon_max": 13.77,
            },
        }

        # Load data
        self._load_data()

    def _load_data(self):
        """Load all GTFS data files."""
        try:
            # Load stops
            self.stops_df = pd.read_csv(os.path.join(self.gtfs_folder, "stops.txt"))

            # Load trips
            self.trips_df = pd.read_csv(os.path.join(self.gtfs_folder, "trips.txt"))

            # Load calendar dates
            self.calendar_dates_df = pd.read_csv(
                os.path.join(self.gtfs_folder, "calendar_dates.txt")
            )

            # Load calendar
            self.calendar_df = pd.read_csv(
                os.path.join(self.gtfs_folder, "calendar.txt")
            )

            # Load stop times (this is a large file, so we'll load it in chunks if needed)
            try:
                self.stop_times_df = pd.read_csv(
                    os.path.join(self.gtfs_folder, "stop_times.txt")
                )
            except MemoryError:
                # Will load in chunks when needed
                self.stop_times_df = None

        except Exception as e:
            print(f"Warning: Could not load GTFS data from {self.gtfs_folder}: {e}")

    def get_city_stops(self, city: str) -> pd.DataFrame:
        """
        Get all stops within a specific city based on coordinates.

        Args:
            city: 'porto', 'london', 'lisbon', or 'berlin'

        Returns:
            DataFrame with stops in the specified city
        """
        if city.lower() not in self.city_boundaries:
            return pd.DataFrame()

        if self.stops_df is None:
            return pd.DataFrame()

        bounds = self.city_boundaries[city.lower()]

        city_stops = self.stops_df[
            (self.stops_df["stop_lat"] >= bounds["lat_min"])
            & (self.stops_df["stop_lat"] <= bounds["lat_max"])
            & (self.stops_df["stop_lon"] >= bounds["lon_min"])
            & (self.stops_df["stop_lon"] <= bounds["lon_max"])
        ].copy()

        city_stops = city_stops[city_stops["location_type"] == 1]

        return city_stops

    def _load_stop_times_chunked(self, stop_ids: List[str]) -> pd.DataFrame:
        """
        Load stop times data for specific stop IDs in chunks to handle large files.

        Args:
            stop_ids: List of stop IDs to filter for

        Returns:
            DataFrame with stop times for the specified stops
        """
        if self.stop_times_df is not None:
            return self.stop_times_df[self.stop_times_df["stop_id"].isin(stop_ids)]

        # Load in chunks
        chunk_size = 100000
        chunks = []

        try:
            for chunk in pd.read_csv(
                os.path.join(self.gtfs_folder, "stop_times.txt"), chunksize=chunk_size
            ):
                filtered_chunk = chunk[chunk["stop_id"].isin(stop_ids)]
                if not filtered_chunk.empty:
                    chunks.append(filtered_chunk)
        except Exception:
            return pd.DataFrame()

        if chunks:
            return pd.concat(chunks, ignore_index=True)
        else:
            return pd.DataFrame()

    def get_bus_count_by_hour_day(
        self, city: str, target_date: str, target_hour: int
    ) -> Dict:
        """
        Get the number of buses stopping at each location in a city for a specific hour and day.

        Args:
            city: 'porto', 'london', 'lisbon', 'berlin'
            target_date: Date in YYYYMMDD format
            target_hour: Hour (0-23)

        Returns:
            Dictionary with stop information and bus counts
        """
        try:
            # Get city stops
            city_stops = self.get_city_stops(city)
            if city_stops.empty:
                return {"error": f"No stops found for {city}"}

            # Get stop times for these stops
            stop_times = self._load_stop_times_chunked(city_stops["stop_id"].tolist())
            if stop_times.empty:
                return {"error": f"No stop times found for stops in {city}"}

            # Convert arrival_time to datetime and extract hour
            # Handle times that go past midnight (e.g., "29:30:00" means 5:30 AM next day)
            def parse_gtfs_time_and_date(time_str, service_date_str):
                try:
                    hours, minutes, seconds = map(int, time_str.split(":"))
                    service_date = datetime.strptime(service_date_str, "%Y%m%d")

                    # If hours >= 24, it's the next day
                    if hours >= 24:
                        hours = hours - 24
                        # Add one day to the service date
                        actual_date = service_date + timedelta(days=1)
                    else:
                        actual_date = service_date

                    return hours, actual_date.strftime("%Y%m%d")
                except Exception:
                    return 0, service_date_str

            stop_times = stop_times.copy()

            # We need to get the service date for each trip to calculate the actual arrival date
            # First, let's get the service dates for all trips
            trip_service_dates = {}
            for _, trip in self.trips_df.iterrows():
                trip_service_dates[trip["trip_id"]] = trip["service_id"]

            # Add service_id to stop_times for date calculation
            stop_times["service_id"] = stop_times["trip_id"].map(trip_service_dates)

            # Calculate actual arrival date and hour for each stop time
            arrival_info = stop_times.apply(
                lambda row: parse_gtfs_time_and_date(row["arrival_time"], target_date),
                axis=1,
            )
            stop_times["arrival_hour"] = [info[0] for info in arrival_info]
            stop_times["actual_arrival_date"] = [info[1] for info in arrival_info]

            # Filter by target hour AND target date
            hourly_stops = stop_times[
                (stop_times["arrival_hour"] == target_hour)
                & (stop_times["actual_arrival_date"] == target_date)
            ]

            if hourly_stops.empty:
                return {"error": f"No buses found for {city} at hour {target_hour}"}

            # Get trips for these stop times
            trip_ids = hourly_stops["trip_id"].unique()
            trips = self.trips_df[self.trips_df["trip_id"].isin(trip_ids)]

            # Get service IDs and check if they run on the target date
            service_ids = trips["service_id"].unique()

            # Convert target date to datetime for day of week calculation
            target_datetime = datetime.strptime(target_date, "%Y%m%d")
            day_of_week = target_datetime.weekday()  # Monday=0, Sunday=6

            # Map day of week to column names
            day_columns = [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]
            day_column = day_columns[day_of_week]

            # Check regular calendar for services that run on this day
            regular_services = self.calendar_df[
                (self.calendar_df["service_id"].isin(service_ids))
                & (self.calendar_df["start_date"] <= int(target_date))
                & (self.calendar_df["end_date"] >= int(target_date))
                & (self.calendar_df[day_column] == 1)
            ]["service_id"].tolist()

            # Check calendar dates for exceptions
            date_services = self.calendar_dates_df[
                (self.calendar_dates_df["date"] == int(target_date))
                & (self.calendar_dates_df["service_id"].isin(service_ids))
            ]

            # Services added on this date
            added_services = date_services[date_services["exception_type"] == 1][
                "service_id"
            ].tolist()
            # Services removed on this date
            removed_services = date_services[date_services["exception_type"] == 2][
                "service_id"
            ].tolist()

            # Final list of running services
            running_services = list(
                set(regular_services + added_services) - set(removed_services)
            )

            # Get trips that run on this date
            running_trips = trips[trips["service_id"].isin(running_services)]

            # Filter stop times for running trips
            final_stops = hourly_stops[
                hourly_stops["trip_id"].isin(running_trips["trip_id"])
            ]

            # Group by stop and count buses
            stop_counts = (
                final_stops.groupby("stop_id").size().reset_index(name="bus_count")
            )

            # Merge with stop information
            result = stop_counts.merge(
                city_stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]],
                on="stop_id",
                how="left",
            )

            # Sort by bus count (descending)
            result = result.sort_values("bus_count", ascending=False)

            return {
                "city": city,
                "date": target_date,
                "hour": target_hour,
                "total_buses": int(result["bus_count"].sum()),
                "total_stops": len(result),
                "stops": result.to_dict("records"),
            }

        except Exception as e:
            return {"error": f"Failed to analyze bus data for {city}: {str(e)}"}

    def get_daily_summary(self, city: str, target_date: str) -> Dict:
        """
        Get a summary of bus activity for a city on a specific date.

        Args:
            city: 'porto', 'london', 'lisbon', 'berlin'
            target_date: Date in YYYYMMDD format

        Returns:
            Dictionary with hourly bus counts
        """
        hourly_counts = {}

        for hour in range(24):
            result = self.get_bus_count_by_hour_day(city, target_date, hour)
            if "error" not in result:
                hourly_counts[hour] = result["total_buses"]
            else:
                hourly_counts[hour] = 0

        return {
            "city": city,
            "date": target_date,
            "total_buses": sum(hourly_counts.values()),
            "hourly_breakdown": hourly_counts,
        }


def get_bus_peak_hours(city: str, date: Optional[str] = None) -> Dict[str, Any]:
    """Returns the peak hours for buses in a specified city organized by stop.

    Args:
        city (str): The name of the city for which to retrieve the peak hours.
        date (str, optional): Date in YYYY-MM-DD format. If not provided, uses current date.

    Returns:
        Dict[str, Any]: Contains status, peak hours summary, and array of stops with their
                       peak hour information aggregated across the top 3 peak hours.
    """

    # Normalize city name
    city = city.lower()

    # Convert date format if provided
    if date:
        try:
            # Convert from YYYY-MM-DD to YYYYMMDD
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            target_date = date_obj.strftime("%Y%m%d")
        except ValueError:
            return {
                "status": "error",
                "error_message": f"Invalid date format. Expected YYYY-MM-DD, got: {date}",
            }
    else:
        # Use current date
        target_date = datetime.now().strftime("%Y%m%d")

    # Use cache key for this specific city and date
    cache_key = f"bus_peak_hours_{city}_{target_date}"

    return get_cached_or_fetch(cache_key, _fetch_bus_peak_hours, city, target_date)


def _fetch_bus_peak_hours(city: str, target_date: str) -> Dict[str, Any]:
    """Internal function to fetch bus peak hours data (without caching).

    Args:
        city (str): The name of the city
        target_date (str): Date in YYYYMMDD format

    Returns:
        Dict[str, Any]: status and result or error msg.
    """
    try:
        # Initialize GTFS analyzer
        analyzer = GTFSAnalyzer()

        # Get daily summary
        result = analyzer.get_daily_summary(city, target_date)

        if "error" in result:
            return {"status": "error", "error_message": result["error"]}

        # Calculate peak hours from hourly breakdown
        hourly_data = result["hourly_breakdown"]

        # Filter out hours with zero buses
        non_zero_hours = {
            hour: count for hour, count in hourly_data.items() if count > 0
        }

        if not non_zero_hours:
            return {
                "status": "error",
                "error_message": f"No bus data found for {city} on {target_date}",
            }

        # Get top 3 peak hours
        sorted_hours = sorted(non_zero_hours.items(), key=lambda x: x[1], reverse=True)
        top_3_peak_hours = sorted_hours[:3]

        # Get detailed stop information for all peak hours and organize by stop
        stops_data = {}  # Dictionary to aggregate data by stop_id

        for hour, count in top_3_peak_hours:
            hour_result = analyzer.get_bus_count_by_hour_day(city, target_date, hour)
            if "error" not in hour_result and "stops" in hour_result:
                for stop in hour_result["stops"]:
                    stop_id = stop["stop_id"]

                    # Initialize stop data if not exists
                    if stop_id not in stops_data:
                        stops_data[stop_id] = {
                            "stop_id": stop["stop_id"],
                            "stop_name": stop["stop_name"],
                            "stop_lat": stop["stop_lat"],
                            "stop_lon": stop["stop_lon"],
                            "peak_hours": [],
                            "total_bus_count": 0,
                            "max_hourly_count": 0,
                        }

                    # Add this hour's data
                    hour_info = {
                        "hour": hour,
                        "hour_formatted": f"{hour:02d}:00",
                        "bus_count": stop["bus_count"],
                    }
                    stops_data[stop_id]["peak_hours"].append(hour_info)
                    stops_data[stop_id]["total_bus_count"] += stop["bus_count"]
                    stops_data[stop_id]["max_hourly_count"] = max(
                        stops_data[stop_id]["max_hourly_count"], stop["bus_count"]
                    )

        # Convert to list and sort by total bus count (descending)
        stops_list = list(stops_data.values())
        stops_list.sort(key=lambda x: x["total_bus_count"], reverse=True)

        return {
            "status": "success",
            "city": city,
            "date": target_date,
            "stops": stops_list,
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Bus peak hours information for '{city}' is not available. Error: {str(e)}",
        }


def get_bus_stops_by_hour(city: str, date: str, hour: int) -> Dict[str, Any]:
    """Get detailed bus stop information for a specific city, date, and hour.

    Args:
        city (str): The name of the city
        date (str): Date in YYYY-MM-DD format
        hour (int): Hour (0-23)

    Returns:
        Dict[str, Any]: status and detailed stop information
    """
    # Normalize city name
    city = city.lower()

    # Convert date format
    try:
        # Convert from YYYY-MM-DD to YYYYMMDD
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        target_date = date_obj.strftime("%Y%m%d")
    except ValueError:
        return {
            "status": "error",
            "error_message": f"Invalid date format. Expected YYYY-MM-DD, got: {date}",
        }

    # Validate hour
    if not 0 <= hour <= 23:
        return {
            "status": "error",
            "error_message": f"Hour must be between 0 and 23, got: {hour}",
        }

    # Use cache key for this specific query
    cache_key = f"bus_stops_{city}_{target_date}_{hour}"

    return get_cached_or_fetch(
        cache_key, _fetch_bus_stops_by_hour, city, target_date, hour
    )


def _fetch_bus_stops_by_hour(city: str, target_date: str, hour: int) -> Dict[str, Any]:
    """Internal function to fetch bus stops data for a specific hour (without caching).

    Args:
        city (str): The name of the city
        target_date (str): Date in YYYYMMDD format
        hour (int): Hour (0-23)

    Returns:
        Dict[str, Any]: status and detailed stop information
    """
    try:
        # Initialize GTFS analyzer
        analyzer = GTFSAnalyzer()

        # Get bus count by hour and day
        result = analyzer.get_bus_count_by_hour_day(city, target_date, hour)

        if "error" in result:
            return {"status": "error", "error_message": result["error"]}

        return {"status": "success", **result}

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Bus stops information for '{city}' at hour {hour} is not available. Error: {str(e)}",
        }


def clear_bus_cache(
    city: Optional[str] = None, date: Optional[str] = None
) -> Dict[str, Any]:
    """Clear bus data cache.

    Args:
        city (str, optional): Specific city to clear cache for
        date (str, optional): Specific date to clear cache for

    Returns:
        Dict[str, Any]: Status of cache clearing operation
    """
    try:
        from ..utils.api_cache import api_cache

        if city and date:
            # Convert date format if provided
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                target_date = date_obj.strftime("%Y%m%d")
                cache_key = f"bus_peak_hours_{city.lower()}_{target_date}"
                api_cache.delete(cache_key)
                return {
                    "status": "success",
                    "message": f"Bus cache cleared for {city} on {date}",
                }
            except ValueError:
                return {
                    "status": "error",
                    "error_message": f"Invalid date format. Expected YYYY-MM-DD, got: {date}",
                }
        elif city:
            # Clear all cache entries for this city
            # This would require iterating through cache keys, which is more complex
            return {
                "status": "success",
                "message": f"Bus cache clearing for {city} (partial implementation)",
            }
        else:
            # Clear all bus cache (would need to iterate through all keys starting with "bus_")
            return {
                "status": "success",
                "message": "Bus cache clearing (partial implementation)",
            }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to clear bus cache: {str(e)}",
        }
