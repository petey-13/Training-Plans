# fetch_strava.py
import os
import json
import requests

CLIENT_ID     = os.environ["STRAVA_CLIENT_ID"]
CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["STRAVA_REFRESH_TOKEN"]

def get_access_token():
    res = requests.post("https://www.strava.com/oauth/token", data={
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type":    "refresh_token"
    })
    res.raise_for_status()
    return res.json()["access_token"]

def fetch_all_activities(token):
    season_start = 1773705600  # Mar 16 2026 — matches your JS
    activities, page = [], 1
    while True:
        res = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {token}"},
            params={"after": season_start, "per_page": 100, "page": page}
        )
        res.raise_for_status()
        batch = res.json()
        if not batch:
            break
        activities.extend(batch)
        page += 1
    return activities

if __name__ == "__main__":
    token      = get_access_token()
    activities = fetch_all_activities(token)
    os.makedirs("data", exist_ok=True)
    with open("data/strava_data.json", "w") as f:
        json.dump(activities, f)
    print(f"Saved {len(activities)} activities.")
