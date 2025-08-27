"""Configuration settings for the ride sharing driver planner agent."""

import os


# Helper function to safely get environment variables and strip whitespace
def get_env_var(key: str, default: str = "") -> str:
    """Get environment variable and strip any whitespace/newlines."""
    return os.getenv(key, default).strip()


# City mappings
AIRPORT_CODE_MAPPING = {
    "Porto": "OPO",
    "Braga": "OPO",
    "Lisbon": "LIS",
}

CITY_CODE_MAPPING = {"Porto": "1131200"}

# London train stations for peak hours analysis
LONDON_STATIONS = {
    "LST": "London Liverpool Street",
    "PAD": "London Paddington",
    "WAT": "London Waterloo",
    "VIC": "London Victoria",
    "LBG": "London Bridge",
    "EUS": "London Euston",
    "KGX": "London King's Cross",
    "CHX": "London Charing Cross",
}

# Porto train stations for peak hours analysis
PORTO_STATIONS = {
    "94-2006": "Porto Campanhã",  # Existing code from CP
    "94-1008": "Porto São Bento",  # Real CP code (updated from mock)
}

# API Base URLs
TRANSPORT_API_BASE_URL = "https://transportapi.com/v3/uk/train/station"
CP_API_BASE_URL = "https://www.cp.pt/sites/spring/station/trains"

# Supported cities
SUPPORTED_CITIES = ["Porto", "London"]

# Cache settings
EVENTS_CACHE_DIR = "driver-assistant/data/events_cache"
TOOL_CACHE_DIR = "driver-assistant/data/tool_cache"

# Selenium settings
SCROLL_PAUSE_TIME = 0.5
MAX_SCROLLS = 10

# Environment variables (with automatic whitespace stripping)
LANGFUSE_HOST = get_env_var("LANGFUSE_HOST", "https://cloud.langfuse.com")
LANGFUSE_SECRET_KEY = get_env_var("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY = get_env_var("LANGFUSE_PUBLIC_KEY")
MAPS_API_KEY = get_env_var("MAPS_API_KEY")
TRANSPORT_API_ID = get_env_var("TRANSPORT_API_ID")
TRANSPORT_API_KEY = get_env_var("TRANSPORT_API_KEY")
GOOGLE_CLOUD_PROJECT = get_env_var("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = get_env_var("GOOGLE_CLOUD_LOCATION")
GOOGLE_GENAI_USE_VERTEXAI = get_env_var("GOOGLE_GENAI_USE_VERTEXAI", "true")
