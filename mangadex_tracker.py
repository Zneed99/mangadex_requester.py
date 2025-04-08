import requests
import time
import json
import os

STATE_FILE = "observed_series.json"

# --- Persistence Layer ---


#
def load_observed_series():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_observed_series(observed_series):
    with open(STATE_FILE, "w") as f:
        json.dump(observed_series, f, indent=4)


# --- Developer functions --- #
def manual_recheck():
    observed_series = load_observed_series()
    check_for_updates(observed_series)
    print("🔄 Manual recheck completed.")


# --- Tracker ---


def check_for_updates(observed_series, return_messages=False):
    updated = False
    messages = []

    for manga_id in observed_series:
        latest_id, chapter_info = get_latest_english_chapter(manga_id)

        if latest_id is None:
            continue

        last_seen_id = observed_series[manga_id]["last_chapter_id"]

        if last_seen_id != latest_id:
            chapter_number = chapter_info.get("chapter", "N/A")
            chapter_title = chapter_info.get("title", "No title")
            chapter_url = f"https://mangadex.org/chapter/{latest_id}/1"
            manga_title = observed_series[manga_id]["title"]

            # Update the saved state
            observed_series[manga_id]["last_chapter_id"] = latest_id
            observed_series[manga_id]["last_chapter_number"] = chapter_number
            observed_series[manga_id]["last_chapter_title"] = chapter_title
            updated = True

            # Format update message
            message = (
                f"🔔 **@everyone**\n"
                f"📢 **New Chapter Released!**\n"
                f"**{manga_title}** – Chapter {chapter_number}: {chapter_title}\n"
                f"{chapter_url}"
            )

            messages.append(message)

            if not return_messages:
                print(message)

    if updated:
        save_observed_series(observed_series)

    return messages if return_messages else None


# --- Add/Remove Functions --- #
def search_manga_titles_for_tracking(search_title):
    url = "https://api.mangadex.org/manga"
    params = {"title": search_title, "limit": 10, "availableTranslatedLanguage[]": "en"}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()["data"]

        if not results:
            return "❌ No matches found.", []

        message = f"🔎 **Search Results for '{search_title}':**\n"
        choices = []
        for idx, entry in enumerate(results, start=1):
            name = entry["attributes"]["title"].get("en", "Unknown Title")
            manga_id = entry["id"]
            message += f"[{idx}] {name} | ID: `{manga_id}`\n"
            choices.append((name, manga_id, entry))

        message += "\nReply with `/select [number]` to track a series."
        return message, choices

    except requests.RequestException as e:
        return f"❌ Error contacting MangaDex: {e}", []


def finalize_tracking(selection_index, choices, observed_series):
    selected_title, selected_id, selected_entry = choices[selection_index]

    if selected_id in observed_series:
        return f"⚠️ '{selected_title}' is already being tracked."

    chapter_url = "https://api.mangadex.org/chapter"
    chap_params = {
        "manga": selected_id,
        "limit": 1,
        "order[createdAt]": "desc",
        "translatedLanguage[]": "en",
    }

    try:
        chapter_response = requests.get(chapter_url, params=chap_params)
        chapter_response.raise_for_status()
        chapter_data = chapter_response.json()["data"]

        if not chapter_data:
            return "⚠️ No English chapter found. Series not added."

        chapter = chapter_data[0]
        chapter_id = chapter["id"]
        chapter_number = chapter["attributes"].get("chapter", "N/A")
        chapter_title = chapter["attributes"].get("title", "No title")

        observed_series[selected_id] = {
            "title": selected_title,
            "last_chapter_id": chapter_id,
            "last_chapter_number": chapter_number,
            "last_chapter_title": chapter_title,
        }

        save_observed_series(observed_series)

        return (
            f"✅ **{selected_title}** added and initial chapter recorded:\n"
            f"📖 Chapter {chapter_number}: {chapter_title}\n"
            f"🔗 https://mangadex.org/chapter/{chapter_id}"
        )

    except requests.RequestException as e:
        return f"❌ Error fetching chapter data: {e}"


def remove_series_by_title(title, observed_series):
    matches = {
        mid: info
        for mid, info in observed_series.items()
        if title.lower() in info["title"].lower()
    }

    if not matches:
        return "❌ No tracked series match that title."

    if len(matches) == 1:
        manga_id, info = next(iter(matches.items()))
        return {
            "prompt": (
                f"🗑️ Confirm removal of '{info['title']}' (ID: `{manga_id}`) with `/confirm_remove {manga_id}`"
            ),
            "options": [(manga_id, info["title"])],
        }

    message = "🔎 **Multiple matches found:**\n"
    sorted_matches = list(matches.items())
    for idx, (mid, info) in enumerate(sorted_matches, start=1):
        message += f"[{idx}] {info['title']} | ID: `{mid}`\n"
    message += "\nUse `/confirm_remove [number]` to select which one to remove."

    return {
        "prompt": message,
        "options": [(mid, info["title"]) for mid, info in sorted_matches],
    }


def confirm_remove_by_id(manga_id, observed_series):
    if manga_id not in observed_series:
        return "❌ Could not find that manga ID in the tracked list."

    title = observed_series[manga_id]["title"]
    del observed_series[manga_id]
    save_observed_series(observed_series)
    return f"✅ '{title}' has been removed."


def confirm_remove_by_index(index, matches, observed_series):
    if not (0 <= index < len(matches)):
        return "❌ Invalid selection. Use a number from the search list."

    selected_id, selected_title = matches[index]
    del observed_series[selected_id]
    save_observed_series(observed_series)
    return f"✅ '{selected_title}' has been removed."


# --- Lookup Functions --- #
def get_latest_english_chapter(manga_id, return_message=False):
    url = "https://api.mangadex.org/chapter"
    params = {
        "manga": manga_id,
        "limit": 1,
        "order[createdAt]": "desc",
        "translatedLanguage[]": "en",
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data["data"]:
            chapter = data["data"][0]
            chapter_id = chapter["id"]
            chapter_attrs = chapter["attributes"]

            if return_message:
                chapter_number = chapter_attrs.get("chapter", "N/A")
                chapter_title = chapter_attrs.get("title", "No title")
                publish_date = chapter_attrs.get("publishAt", "Unknown Date")
                url = f"https://mangadex.org/chapter/{chapter_id}"

                message = (
                    f"📘 **Latest English Chapter Info:**\n"
                    f"• Chapter {chapter_number}: {chapter_title}\n"
                    f"• Published: {publish_date}\n"
                    f"🔗 {url}"
                )
                return chapter_id, chapter_attrs, message

            return chapter_id, chapter_attrs
        else:
            return None, None, "⚠️ No English chapters found."

    except requests.RequestException as e:
        error_msg = f"❌ Request error for manga {manga_id}: {e}"
        print(error_msg)
        return None, None, error_msg if return_message else (None, None)


def get_manga_by_title(title):
    url = "https://api.mangadex.org/manga"
    params = {"title": title, "limit": 10, "availableTranslatedLanguage[]": "en"}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()["data"]

        matches = []
        for entry in results:
            attributes = entry["attributes"]
            name = attributes["title"].get("en", "Unknown Title")
            manga_id = entry["id"]
            matches.append((name, manga_id))
        return matches

    except requests.RequestException as e:
        print(f"Error searching MangaDex: {e}")
        return []


def list_tracked_series(observed_series):
    if not observed_series:
        return "📭 No series are being tracked."

    message = "**📘 Currently Tracked Series:**\n"
    for info in observed_series.values():
        title = info["title"]
        chapter = info["last_chapter_number"]
        chap_title = info["last_chapter_title"]
        message += f"• **{title}** – Chapter {chapter}: {chap_title}\n"

    return message


def show_latest_chapter(title, observed_series):
    for info in observed_series.values():
        if title.lower() in info["title"].lower():
            chapter = info["last_chapter_number"]
            chap_title = info["last_chapter_title"]
            chap_id = info["last_chapter_id"]
            return (
                f"📖 **{info['title']}**\n"
                f"• Chapter {chapter}: {chap_title}\n"
                f"🔗 https://mangadex.org/chapter/{chap_id}"
            )

    return "❌ No tracked series found matching that title."


def search_manga_title(title):
    results = get_manga_by_title(title)
    if not results:
        return "❌ No matches found."

    message = "🔎 **MangaDex Search Results:**\n"
    for idx, (name, mid) in enumerate(results, start=1):
        message += f"[{idx}] {name}\n"
    return message


def fetch_manga_info(manga_id):
    url = f"https://api.mangadex.org/manga/{manga_id}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json()["data"]
    except Exception as e:
        print(f"❌ Error fetching manga info: {e}")
        return None


def show_manga_info(title, observed_series):
    for mid, info in observed_series.items():
        if title.lower() in info["title"].lower():
            metadata = fetch_manga_info(mid)
            if not metadata:
                return "❌ Could not fetch detailed info."

            attr = metadata["attributes"]
            desc = attr["description"].get("en", "No description.")
            status = attr.get("status", "Unknown")
            tags = [
                tag["attributes"]["name"].get("en", "Unknown") for tag in attr["tags"]
            ]
            genre_str = ", ".join(tags)

            return (
                f"📘 **{info['title']}**\n"
                f"• Status: {status}\n"
                f"• Genres: {genre_str}\n"
                f"• Description: {desc[:400]}..."
            )

    return "❌ No tracked series match that title."


# --- Main ---

if __name__ == "__main__":
    print("✅ MangaDex Tracker started...")

    # # Load or initialize the observed_series from file
    # observed_series = load_observed_series()
    # # add_series_by_title("Attack on titan", observed_series)
    # # remove_series_by_title("Attack on titan", observed_series)
    # # list_tracked_series(observed_series)
    # # show_latest_chapter("Attack on titan", observed_series)
    # # search_manga_title("Attack on titan")
    # # show_manga_info("Attack on titan", observed_series)
    # # manual_recheck()

    # # Polling loop
    # while True:
    #     print(f"⏳ Checking for updates...")
    #     check_for_updates(observed_series)
    #     time.sleep(10)  # Check every 5 minutes
