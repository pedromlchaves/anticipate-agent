"""Configuration settings for the ride sharing driver planner agent."""

# Google Maps API Key
MAPS_API_KEY = "AIzaSyDrvmtNgkUgENqDZDvNFo3QOSk_5eR9EPw"

# City mappings
AIRPORT_CODE_MAPPING = {
    "Porto": "OPO",
    "Braga": "OPO",
    "Lisbon": "LIS",
}

STATION_CODE_MAPPING = {
    "Porto": "94-2006",
}

CITY_CODE_MAPPING = {"Porto": "1131200"}

# Supported cities
SUPPORTED_CITIES = ["Porto"]

# Cache settings
EVENTS_CACHE_DIR = "driver-assistant/data/events_cache"
TOOL_CACHE_DIR = "driver-assistant/data/tool_cache"

# Selenium settings
SCROLL_PAUSE_TIME = 0.5
MAX_SCROLLS = 10
