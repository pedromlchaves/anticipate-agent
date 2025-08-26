"""Flight-related tools for getting peak hours."""

import pandas as pd
import json
from bs4 import BeautifulSoup
from typing import Dict

from ..config import AIRPORT_CODE_MAPPING
from ..utils.web_scraping import get_headless_chrome_driver


def get_flight_peak_hours(city: str) -> Dict[str, any]:
    """Returns the peak hours for flights in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the peak hours.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    try:
        airport_code = AIRPORT_CODE_MAPPING.get(city)
        if not airport_code:
            return {
                "status": "error",
                "error_message": f"Airport information for '{city}' is not available.",
            }

        url = (
            "https://www.aeroportoporto.pt/en/flights_proxy?day=hoje&movtype=A&IATA="
            + airport_code
        )

        driver = get_headless_chrome_driver()
        driver.get(url)

        soup = BeautifulSoup(driver.page_source, features="html.parser")
        driver.quit()

        df = pd.DataFrame(json.loads(soup.body.contents[0])["flights"])

        # Convert 'time' column to datetime if it's not already
        df["time"] = pd.to_datetime(df["time"])

        # Group by hour and count occurrences
        hourly_counts = df.groupby(df["time"].dt.hour).size().reset_index(name="Count")

        # Optional: format hour as HH:00
        hourly_counts["Hour"] = hourly_counts["time"].apply(lambda x: f"{x:02d}:00")
        hourly_counts = hourly_counts[["Hour", "Count"]]
        hourly_counts = hourly_counts.to_dict(orient="records")
        return {
            "status": "success",
            "peak_hours": str(hourly_counts),
        }

    except Exception as e:

        return {
            "status": "error",
            "error_message": f"Peak hours information for '{city}' is not available. The exception was {str(e)}.",
        }
