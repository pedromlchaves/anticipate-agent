#!/usr/bin/env python3
"""Quick test for the new Stansted Airport functionality."""

import sys
import os

# Add the driver-assistant directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "driver-assistant"))

try:
    from tools.flights import get_london_flight_peak_hours

    print("Testing London flight peak hours with Stansted included...")
    result = get_london_flight_peak_hours()

    print("Result:")
    print(f"Status: {result['status']}")
    if result["status"] == "success":
        print(f"Peak hours: {result['peak_hours']}")
        print(f"Total flights: {result['total_flights']}")
        print(f"Airports included: {result['airports_included']}")
    else:
        print(f"Error: {result['error_message']}")

except ImportError as e:
    print(f"Import error: {e}")
    print("This is expected if dependencies are not installed.")
except Exception as e:
    print(f"Error testing functionality: {e}")
