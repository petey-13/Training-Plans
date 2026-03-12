import os
import json
import requests

# 1. Grab the secrets from GitHub
CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("STRAVA_REFRESH_TOKEN")

def get_strava_data():
    # 2. Ask Strava for a fresh Access Token
    auth_url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    
    res = requests.post(auth_url, data=payload)
    access_token = res.json().get("access_token")

    # 3. Use the fresh token to get your last 5 activities
    activities_url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"per_page": 5} # Change this number if you want more/fewer activities
    
    activities_res = requests.get(activities_url, headers=headers, params=params)
    
    # 4. Save the data to a file in your repository
    with open("strava_data.json", "w") as f:
        json.dump(activities_res.json(), f)

if __name__ == "__main__":
    get_strava_data()
