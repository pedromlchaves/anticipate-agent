"""Routing and driving time calculation tools."""

import datetime
import google.maps.routing_v2 as routing_v2
from google.protobuf import timestamp_pb2
from google.type import latlng_pb2
from typing import Optional
from google.adk.agents import Agent
from ..config import SUPPORTED_CITIES
from ..utils.geocoding import geocode_address

import logging
import os

# Use a module-level logger consistent with agent.py
logger = logging.getLogger("driver-assistant.tools.routing")


def get_driving_time_at_time_x(
    origin: str, destination: str, departure_time: str
) -> Optional[float]:
    """
    Gets the driving time between two points at a specific departure time,
    considering traffic conditions, using Google Maps Routes API.

    Args:
        origin: Name or address of the origin point.
        destination: Name or address of the destination point.
        departure_time: The desired departure time (datetime object, must be UTC).

    Returns:
        The driving duration in minutes, or None if an error occurs.
    """
    # Convert departure_time string to a datetime object (assume ISO format)
    logger.info("Converting departure_time to datetime object")
    try:
        departure_time = datetime.datetime.fromisoformat(departure_time)
    except Exception as e:
        logger.error(f"[Time Parsing Error] Could not parse departure_time: {e}")
        return None

    logger.info("Getting geocoding for origin and destination:")
    logger.info(f"Origin: {origin}")
    logger.info(f"Destination: {destination}")
    # Convert origin and destination to latitude and longitude
    try:
        origin_data = geocode_address(origin)
        origin_lat = origin_data["lat"]
        origin_lng = origin_data["lng"]

        destination_data = geocode_address(destination)
        destination_lat = destination_data["lat"]
        destination_lng = destination_data["lng"]

    except Exception as e:
        logger.error(f"[Geocoding Error] Could not geocode addresses: {e}")
        return None

    try:
        client = routing_v2.RoutesClient(
            client_options={"api_key": os.getenv("MAPS_API_KEY")}
        )

        timestamp = timestamp_pb2.Timestamp()
        # The Routes API expects departure_time in UTC.
        # Ensure your datetime object is timezone-aware and in UTC, or convert it.
        # For simplicity in this script, we'll ensure it's set to UTC.
        if departure_time.tzinfo is None or departure_time.tzinfo.utcoffset(
            departure_time
        ) != datetime.timedelta(0):
            logger.warning("[Routes API] Departure time not in UTC. Converting to UTC.")
            departure_time = departure_time.astimezone(datetime.timezone.utc)

        timestamp.FromDatetime(departure_time)

        origin_waypoint = routing_v2.Waypoint(
            location=routing_v2.Location(
                lat_lng=latlng_pb2.LatLng(latitude=origin_lat, longitude=origin_lng)
            )
        )
        destination_waypoint = routing_v2.Waypoint(
            location=routing_v2.Location(
                lat_lng=latlng_pb2.LatLng(
                    latitude=destination_lat, longitude=destination_lng
                )
            )
        )

        request = routing_v2.ComputeRoutesRequest(
            origin=origin_waypoint,
            destination=destination_waypoint,
            travel_mode=routing_v2.RouteTravelMode.DRIVE,
            routing_preference=routing_v2.RoutingPreference.TRAFFIC_AWARE,  # Crucial for traffic
            departure_time=timestamp,
        )

        # Pass field_mask as metadata to the client.compute_routes method
        field_mask_str = "routes.duration,routes.localized_values.duration.text"
        metadata = [("x-goog-fieldmask", field_mask_str)]

        response = client.compute_routes(request=request, metadata=metadata)
        logger.info(f"Routes API response: {response}")

        if response.routes:
            route = response.routes[0]
            duration_seconds = route.duration.seconds
            duration_text = route.localized_values.duration.text
            logger.info(
                f"[Routes API] Driving time: {duration_text} ({duration_seconds} seconds)"
            )
            return duration_seconds / 60
        else:
            logger.warning("[Routes API] No routes found.")
            return None

    except Exception as e:
        logger.error(f"[Routes API] An error occurred: {e}")
        return None
