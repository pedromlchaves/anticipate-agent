"""Web scraping utilities."""

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from typing import List, Dict, Any
from datetime import datetime


def extract_events_from_html(html_content: str) -> List[Dict[str, Any]]:
    """
    Extracts event information from the provided HTML content.

    Args:
        html_content (str): The HTML content of the page.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents an event.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    events_data = []

    # Find all <li> elements with itemscope and itemtype="https://schema.org/Event"
    # This targets the main event blocks
    event_list_items = soup.find_all(
        "li",
        {"itemscope": "", "itemtype": lambda x: x and "schema.org/Event" in x},
    )

    for event_li in event_list_items:
        event = {}

        # Extract Event Name
        title_tag = event_li.find("div", class_="viral-event-title")
        if title_tag:
            name_span = title_tag.find("span", itemprop="name")
            if name_span:
                event["name"] = name_span.get_text(strip=True).replace("▸", "").strip()

        # Extract Date and Time
        # The 'data-date-start' and 'data-date-end' attributes contain ISO 8601 formatted dates
        date_start_str = event_li.get("data-date-start")
        date_end_str = event_li.get("data-date-end")

        if date_start_str:
            try:
                # Parse the start date and time
                start_dt = datetime.fromisoformat(
                    date_start_str.replace("+01:00", "+0100").replace("+00:00", "+0000")
                )
                event["start_date"] = start_dt.strftime("%Y-%m-%d")
                event["start_time"] = start_dt.strftime("%H:%M")
            except ValueError:
                event["start_date"] = None
                event["start_time"] = None

        if date_end_str:
            try:
                # Parse the end date and time
                end_dt = datetime.fromisoformat(
                    date_end_str.replace("+01:00", "+0100").replace("+00:00", "+0000")
                )
                event["end_date"] = end_dt.strftime("%Y-%m-%d")
                event["end_time"] = end_dt.strftime("%H:%M")
            except ValueError:
                event["end_date"] = None
                event["end_time"] = None

        # Fallback for time from .viral-event-hour if data-date-start is missing time
        if "start_time" not in event or not event["start_time"]:
            hour_div = event_li.find("div", class_="viral-event-hour")
            if hour_div and hour_div.get_text(strip=True) != "N/D":
                event["start_time"] = hour_div.get_text(strip=True)

        # Extract Location
        location_tag = event_li.find("a", itemprop="location")
        if location_tag:
            place_name = location_tag.find("span", itemprop="name")
            if place_name:
                event["location_name"] = place_name.get_text(strip=True)
            address = location_tag.find("meta", itemprop="address")
            if address:
                event["location_address"] = (
                    address.get("content", "").strip().replace(" - Porto", "")
                )  # Clean up " - Porto" if present

        # Extract Categories
        category_links = event_li.find_all(
            "a", title=lambda x: x and "Ver eventos desta categoria" in x
        )
        if category_links:
            event["categories"] = [link.get_text(strip=True) for link in category_links]

        # Extract URL
        url_tag = event_li.find("a", onclick=lambda x: x and "Navigate.openHref" in x)
        if url_tag and url_tag.get("href") and url_tag.get("href") != "#":
            event["url"] = "https://www.viralagenda.com" + url_tag.get("href")

        # Add event if it has a name (basic validation)
        if "name" in event and event["name"]:
            events_data.append(event)

    return events_data


def get_headless_chrome_driver() -> webdriver.Chrome:
    """
    Get a headless Chrome driver.

    Returns:
        webdriver.Chrome: Configured Chrome driver instance.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)


def scroll_and_load_content(
    driver: webdriver.Chrome,
    extract_func,
    scroll_pause_time: float = 0.5,
    max_scrolls: int = 10,
) -> List[Dict[str, Any]]:
    """
    Scroll through a page and extract content using the provided function.

    Args:
        driver: Chrome driver instance
        extract_func: Function to extract content from HTML
        scroll_pause_time: Time to pause between scrolls
        max_scrolls: Maximum number of scrolls

    Returns:
        List[Dict[str, Any]]: Extracted content
    """
    last_content_count = 0
    scroll_count = 0

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollBy(0, window.innerHeight*4);")

        # Wait to load page
        time.sleep(scroll_pause_time)

        scroll_count += 1

        full_html = driver.page_source
        content = extract_func(full_html)

        content_count = len(content)

        if content_count == last_content_count:
            print(
                f"No new content found after {scroll_count} scrolls. Stopping scroll."
            )
            print("Total content found:", content_count)
            break

        last_content_count = content_count

        if scroll_count >= max_scrolls:
            print(f"Reached maximum scroll limit of {max_scrolls}. Stopping scroll.")
            break

    return content
