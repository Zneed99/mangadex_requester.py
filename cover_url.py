import json
import requests

# Load your observed_series JSON
with open("observed_series.json", "r", encoding="utf-8") as f:
    observed_series = json.load(f)

for manga_id, series_data in observed_series.items():
    title = series_data.get("title", "Unknown Title")
    try:
        # Get manga data
        url = f"https://api.mangadex.org/manga/{manga_id}?includes[]=cover_art"
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        
        cover_file = None
        for rel in data.get("relationships", []):
            if rel.get("type") == "cover_art":
                attributes = rel.get("attributes", {})
                cover_file = attributes.get("fileName")
                if cover_file:
                    break

        if cover_file:
            cover_url = f"https://uploads.mangadex.org/covers/{manga_id}/{cover_file}"
            print(f"{title}: {cover_url}")
        else:
            print(f"{title}: No cover found")

    except Exception as e:
        print(f"{title}: Error fetching cover - {e}")
