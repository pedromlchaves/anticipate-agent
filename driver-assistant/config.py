"""Configuration settings for the ride sharing driver planner agent."""

# City mappings
AIRPORT_CODE_MAPPING = {
    "Porto": "OPO",
    "Braga": "OPO",
    "Lisbon": "LIS",
}

CITY_CODE_MAPPING = {"Porto": "1131200"}

# Train station mappings
STATION_CODE_MAPPING = {
    "Porto": "94-50100",  # Porto Campanhã
}

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
    "94-50100": "Porto Campanhã",  # Existing code from CP
    "94-1008": "Porto São Bento",  # Real CP code (updated from mock)
}

# API Base URLs
TRANSPORT_API_BASE_URL = "https://transportapi.com/v3/uk/train/station"
CP_API_BASE_URL = "https://www.cp.pt/sites/spring/station/trains"

# Supported cities
SUPPORTED_CITIES = ["Porto"]

# Cache settings
EVENTS_CACHE_DIR = "driver-assistant/data/events_cache"
TOOL_CACHE_DIR = "driver-assistant/data/tool_cache"

# Selenium settings
SCROLL_PAUSE_TIME = 0.5
MAX_SCROLLS = 10
