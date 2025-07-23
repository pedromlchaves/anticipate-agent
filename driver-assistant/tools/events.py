"""Events-related tools."""

import os
import json
from typing import Dict

from ..config import EVENTS_CACHE_DIR, SCROLL_PAUSE_TIME, MAX_SCROLLS
from ..utils.web_scraping import (
    extract_events_from_html,
    get_headless_chrome_driver,
    scroll_and_load_content,
)


def get_events_from_viralagenda(city: str, date: str) -> Dict[str, any]:
    """
    Fetches events from Viral Agenda for a specific city and date, with caching.

    Args:
        city (str): The city to search for events.
        date (str): The date in 'DD-MM-YYYY' format.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    try:
        cache_dir = EVENTS_CACHE_DIR
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{city}_{date}.json")

        # Check cache before any Selenium logic
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                events = json.load(f)
                return {"status": "success", "events": events, "count": len(events)}

        base_url = "https://www.viralagenda.com"
        search_url = f"{base_url}/pt/{city}/{city}/{date}"

        # Only run Selenium if cache is missing
        driver = get_headless_chrome_driver()
        driver.get(search_url)

        # Handle consent dialog
        try:
            from selenium.webdriver.common.by import By

            consent_button = driver.find_element(
                By.XPATH, "//button[contains(., 'Consentir')]"
            )
            consent_button.click()
        except Exception:
            pass  # If not found, continue

        # Scroll and load all content
        events = scroll_and_load_content(
            driver, extract_events_from_html, SCROLL_PAUSE_TIME, MAX_SCROLLS
        )

        driver.quit()

        # Save to cache
        with open(cache_file, "w") as f:
            json.dump(events, f)

        return {"status": "success", "events": events, "count": len(events)}

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Events information for '{city}' on '{date}' is not available. Error: {str(e)}",
        }
