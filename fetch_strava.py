# fetch_strava.py

import os
import json
import time
import requests

CLIENT_ID     = os.environ.get("STRAVA_CLIENT_ID",     "NOT_FOUND")
CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET", "NOT_FOUND")
REFRESH_TOKEN = os.environ.get("STRAVA_REFRESH_TOKEN", "NOT_FOUND")

def get_access_token():
    res = requests.post("https://www.strava.com/oauth/token", data={
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type":    "refresh_token"
    })
    print("Status:", res.status_code)
    res.raise_for_status()
    return res.json()["access_token"]

def fetch_all_activities(token):
    activities, page = [], 1
    while True:
        res = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {token}"},
            params={"per_page": 100, "page": page}
        )
        print("Activities status:", res.status_code)
        res.raise_for_status()
        batch = res.json()
        if not batch:
            break
        activities.extend(batch)
        page += 1
    return activities

def best_rolling_avg(watts, window_seconds):
    """Return the best (highest) average watts over any window_seconds window."""
    if len(watts) < window_seconds:
        return None
    total = sum(watts[:window_seconds])
    best = total
    for i in range(window_seconds, len(watts)):
        total += watts[i] - watts[i - window_seconds]
        if total > best:
            best = total
    return round(best / window_seconds, 1)

def fetch_power_bests(activity_id, token):
    """Fetch watts stream for an activity and return 5sec/1/5/10/20-min best power."""
    res = requests.get(
        f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
        headers={"Authorization": f"Bearer {token}"},
        params={"keys": "watts", "key_by_type": "true"}
    )
    # Respect rate limits — Strava allows 100 req/15min
    if res.status_code == 429:
        print("  Rate limited — sleeping 60s...")
        time.sleep(60)
        return None
    if res.status_code != 200:
        return None

    data = res.json()
    watts = data.get("watts", {}).get("data", [])
    if not watts:
        return None

    return {
        "best_5sec_watts":  best_rolling_avg(watts, 5),
        "best_1min_watts":  best_rolling_avg(watts, 60),
        "best_5min_watts":  best_rolling_avg(watts, 300),
        "best_10min_watts": best_rolling_avg(watts, 600),
        "best_20min_watts": best_rolling_avg(watts, 1200),
    }

POWER_KEYS = ("best_5sec_watts", "best_1min_watts", "best_5min_watts", "best_10min_watts", "best_20min_watts")

if __name__ == "__main__":
    token = get_access_token()
    activities = fetch_all_activities(token)

    # Load previously saved data to avoid re-fetching streams
    existing_path = "data/strava_data.json"
    existing_map = {}
    if os.path.exists(existing_path):
        with open(existing_path) as f:
            for act in json.load(f):
                existing_map[act["id"]] = act

    # Only fetch power streams for rides with device power that we haven't processed yet
    power_sports = {"Ride", "VirtualRide", "GravelRide", "EBikeRide", "MountainBikeRide"}
    needs_streams = [
        a for a in activities
        if a.get("sport_type") in power_sports
        and a.get("device_watts")
        and "best_5sec_watts" not in existing_map.get(a["id"], {})
    ]

    print(f"Fetching power streams for {len(needs_streams)} new/unprocessed rides...")

    for i, activity in enumerate(needs_streams):
        aid = activity["id"]
        print(f"  [{i+1}/{len(needs_streams)}] {activity['name'][:50]}")
        bests = fetch_power_bests(aid, token)
        if bests:
            activity.update(bests)
        # Merge existing power bests for already-processed activities
        if aid in existing_map:
            for key in POWER_KEYS:
                if key in existing_map[aid] and key not in activity:
                    activity[key] = existing_map[aid][key]
        # Small delay to stay well within rate limits
        time.sleep(0.5)

    # Merge power bests from existing data into all activities
    for activity in activities:
        aid = activity["id"]
        if aid in existing_map:
            for key in POWER_KEYS:
                if key in existing_map[aid] and key not in activity:
                    activity[key] = existing_map[aid][key]

    os.makedirs("data", exist_ok=True)
    with open(existing_path, "w") as f:
        json.dump(activities, f)

    print(f"Saved {len(activities)} activities.")

    # Print all-time bests as a sanity check
    bests = {k: 0 for k in POWER_KEYS}
    for a in activities:
        for k in bests:
            bests[k] = max(bests[k], a.get(k) or 0)
    print(f"\nAll-time bests:")
    print(f"  5-sec:  {bests['best_5sec_watts']}W")
    print(f"  1-min:  {bests['best_1min_watts']}W")
    print(f"  5-min:  {bests['best_5min_watts']}W")
    print(f"  10-min: {bests['best_10min_watts']}W")
    print(f"  20-min: {bests['best_20min_watts']}W")
