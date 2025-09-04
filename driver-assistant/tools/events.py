"""Events-related tools."""

from typing import Dict

from google.adk.agents import Agent
from google.adk.tools.url_context_tool import url_context


from ..config import SCROLL_PAUSE_TIME, MAX_SCROLLS
from ..utils.web_scraping import (
    extract_events_from_html,
    get_headless_chrome_driver,
    scroll_and_load_content,
)
from ..utils.api_cache import after_agent_cache, before_agent_cache, get_cached, get_cached_or_fetch, set_cached


def get_events_from_viralagenda(city: str, date: str) -> Dict[str, any]:
    """
    Fetches events from Viral Agenda for a specific city and date, with caching.

    Args:
        city (str): The city to search for events.
        date (str): The date in 'DD-MM-YYYY' format.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    cache_key = f"events_{city.lower()}_{date}"
    return get_cached_or_fetch(cache_key, _fetch_events_from_viralagenda, city, date)


def _fetch_events_from_viralagenda(city: str, date: str) -> Dict[str, any]:
    """
    Internal function to fetch events from Viral Agenda (without caching).

    Args:
        city (str): The city to search for events.
        date (str): The date in 'DD-MM-YYYY' format.

    Returns:
        Dict[str, any]: status and result or error msg.
    """
    try:
        base_url = "https://www.viralagenda.com"
        search_url = f"{base_url}/pt/{city}/{city}/{date}"

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

        return {"status": "success", "events": events, "count": len(events)}

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Events information for '{city}' on '{date}' is not available. Error: {str(e)}",
        }


def create_events_from_url_agent() -> Agent:
    """
    Creates a context agent for fetching events from a given url.
    """
    return Agent(
        name="events_from_url_agent",
        model="gemini-2.5-flash",
        description="Agent to extract events from a given url",
        instruction=(
            """
            You are an agent that fetches events from a given url.

            Return a list of events found on the page as:

            {
                "status": "success",
                "events": [
                    {
                        "name": "<event-name>",
                        "start_date": "<start_date>",
                        "end_date": "<end_date>",
                        "start_time": "<start_time>",
                        "end_time": "<end_time>",
                        "location_name": "<location_name>",
                        "location_address": "<location_address>",
                        "url": "<event-url>",
                        "categories": "<event-categories>"
                    },
                    ...
                ],
            }
            """
        ),
        # before_agent_callback=before_agent_cache,  # check if cached
        # after_agent_callback=after_agent_cache,  # cache response
        tools=[
            url_context,
        ],
    )


def clear_events_cache(city: str = None, date: str = None) -> Dict[str, any]:
    """Clear events cache.

    Args:
        city (str, optional): Specific city cache to clear.
        date (str, optional): Specific date cache to clear.

    Returns:
        Dict[str, any]: Status of cache clearing operation
    """
    try:
        from ..utils.api_cache import api_cache

        if city and date:
            # Clear specific city/date cache
            cache_key = f"events_{city.lower()}_{date}"
            api_cache.delete(cache_key)
            return {
                "status": "success",
                "message": f"Events cache cleared for {city} on {date}",
            }
        elif city:
            # Would need pattern matching to clear all dates for a city
            # For now, let cleanup handle it
            return {
                "status": "success",
                "message": f"Use cleanup_old_cache() to clear old {city} events",
            }
        else:
            # Clear all events cache - let cleanup handle it
            return {
                "status": "success",
                "message": "Use cleanup_old_cache() to clear all old events",
            }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to clear events cache: {str(e)}",
        }
