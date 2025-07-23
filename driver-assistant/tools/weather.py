"""Weather-related tools."""

import requests
import pandas as pd
import datetime
from typing import Dict

from ..config import CITY_CODE_MAPPING


def get_daily_city_weather(city: str) -> Dict[str, any]:
    """Returns the daily weather for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    try:
        city_code = CITY_CODE_MAPPING.get(city)
        if not city_code:
            return {
                "status": "error",
                "error_message": f"Weather information for '{city}' is not available.",
            }

        response = requests.get(
            f"https://api.ipma.pt/public-data/forecast/aggregate/{city_code}.json"
        )
        data = response.json()
        df = pd.DataFrame(data)

        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        df_today = df[df["dataPrev"].str.startswith(today_str)]
        df_today = df_today[
            [
                "dataPrev",
                "tMin",
                "tMax",
                "tMed",
                "probabilidadePrecipita",
                "idIntensidadePrecipita",
            ]
        ]

        forecast = str(df_today.to_dict(orient="records"))
        return {
            "status": "success",
            "weather": forecast,
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
        }
