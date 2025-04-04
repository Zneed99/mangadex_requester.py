import requests

# MangaDex API endpoint
url = "https://api.mangadex.org/manga"

# Optional: You can pass query parameters, for example to filter by title or language
params = {
    "availableTranslatedLanguage[]": "en",  # Only English translations
    "title": "One Piece",  # Search for a title (optional)
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    for manga in data["data"]:
        print(f"Manga ID: {manga['id']} & Title: {manga['attributes']['title']['en']}")
        # title = manga["attributes"]["title"].get("en", "No English Title")
        # print(f"Title: {title}")
else:
    print(f"Failed to fetch manga: {response.status_code} - {response.text}")
