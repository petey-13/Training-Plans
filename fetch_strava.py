# fetch_strava.py
import os
import json
import requests

CLIENT_ID     = os.environ.get("STRAVA_CLIENT_ID", "NOT_FOUND")
CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET", "NOT_FOUND")
REFRESH_TOKEN = os.environ.get("STRAVA_REFRESH_TOKEN", "NOT_FOUND")

print("CLIENT_ID:", repr(CLIENT_ID))
print("CLIENT_SECRET length:", len(CLIENT_SECRET))
print("REFRESH_TOKEN length:", len(REFRESH_TOKEN))

def get_access_token():
    res = requests.post("https://www.strava.com/oauth/token", data={
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type":    "refresh_token"
    })
    print("Status:", res.status_code)
    print("Response:", res.json())
    res.raise_for_status()
    return res.json()["access_token"]

def fetch_all_activities(token):
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
