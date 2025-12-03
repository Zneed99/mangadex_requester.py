import requests
from bs4 import BeautifulSoup
import re
import json
import os

# User-Agent headers to avoid basic blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/119.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

STATE_FILE = "observed_series.json"


def load_observed_series():
    """Load observed series from JSON file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def get_latest_chapter_from_config(series):
    """Fetch the latest chapter number and build reading link."""
    try:
        response = requests.get(series["check_url"], headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch {series['check_url']}: {e}")
        return None, None

    soup = BeautifulSoup(response.text, "html.parser")
    element = soup.select_one(series["check_selector"])
    if not element:
        print(f"No element found for selector '{series['check_selector']}' at {series['check_url']}")
        return None, None

    # Extract chapter number using regex
    match = re.search(r"(\d+)", element.text)
    if not match:
        print(f"Could not extract chapter number from '{element.text.strip()}'")
        return None, None

    chapter_number = int(match.group(1))
    read_link = series["read_url_template"].format(chapter_number)
    return chapter_number, read_link


def check_all_optional_scrapers():
    """Loop through all series with optional scraper config in observed_series.json."""
    observed_series = load_observed_series()
    for mid, series_data in observed_series.items():
        scraper_config = series_data.get("optional_scraper")
        if not scraper_config:
            continue

        print(f"\nChecking series: {series_data['title']} (Optional Scraper)")
        chapter_number, read_link = get_latest_chapter_from_config(scraper_config)
        if chapter_number:
            print(f"Latest chapter: {chapter_number}")
            print(f"Read link: {read_link}")
        else:
            print("Could not find latest chapter.")


if __name__ == "__main__":
    check_all_optional_scrapers()
