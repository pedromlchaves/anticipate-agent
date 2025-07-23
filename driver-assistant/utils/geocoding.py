"""Geocoding utilities."""

import requests
from typing import Dict, Any
from ..config import MAPS_API_KEY  # Ensure you have a config file with your API key


def geocode_address(address: str) -> Dict[str, Any]:
    """
    Geocode an address to get its latitude and longitude using Google's Geocoding API.

    Args:
        address (str): The address to geocode.

    Returns:
        Dict[str, Any]: Dictionary containing formatted address, lat, and lng.
                        Returns an empty dictionary if geocoding fails.
    """
    # IMPORTANT: Replace 'YOUR_GOOGLE_API_KEY' with your actual Google Cloud API key
    # Ensure the Geocoding API is enabled for your project.
    API_KEY = MAPS_API_KEY
    BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    params = {
        "address": address,
        "key": API_KEY,
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if data["status"] == "OK":
            result = data["results"][0]
            formatted_address = result["formatted_address"]
            location = result["geometry"]["location"]
            lat = location["lat"]
            lng = location["lng"]

            print(f"Formatted Address: {formatted_address}")
            print(f"Latitude: {lat}, Longitude: {lng}")

            return {
                "address": formatted_address,
                "lat": lat,
                "lng": lng,
            }
        else:
            print(f"Geocoding failed. Status: {data['status']}")
            if "error_message" in data:
                print(f"Error Message: {data['error_message']}")
            return {}

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {}
    except IndexError:
        print("No results found for the given address.")
        return {}
    except KeyError as e:
        print(f"Unexpected JSON structure: {e}")
        return {}


# Example Usage (uncomment to test after replacing API_KEY)
# if __name__ == "__main__":
#     # Example for a specific address in Porto, Portugal
#     address_porto = "Rua de Cedofeita 340, Porto, Portugal"
#     geocode_result_porto = geocode_address(address_porto)
#     if geocode_result_porto:
#         print("\n--- Geocoding Result for Porto ---")
#         print(f"Address: {geocode_result_porto['address']}")
#         print(f"Lat: {geocode_result_porto['lat']}")
#         print(f"Lng: {geocode_result_porto['lng']}")

#     # Example for a generic address
#     address_london = "1600 Amphitheatre Parkway, Mountain View, CA"
#     geocode_result_london = geocode_address(address_london)
#     if geocode_result_london:
#         print("\n--- Geocoding Result for Mountain View ---")
#         print(f"Address: {geocode_result_london['address']}")
#         print(f"Lat: {geocode_result_london['lat']}")
#         print(f"Lng: {geocode_result_london['lng']}")

#     # Example for an invalid address
#     address_invalid = "asdfasdfasdfasdf"
#     geocode_result_invalid = geocode_address(address_invalid)
#     if not geocode_result_invalid:
#         print("\n--- Geocoding Result for Invalid Address ---")
#         print("Geocoding failed as expected for invalid address.")
