from strava_tools import (
    fetch_activities, extract_gear_ids_from_activities, fetch_gear_details,
    combine_shoes, combine_bikes, refresh_access_token, exchange_code_for_tokens
)
import os
from dotenv import load_dotenv
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
activities_path = os.path.join(script_dir, "activities.json")
gear_ids_path = os.path.join(script_dir, "gear_ids.json")
all_gear_path = os.path.join(script_dir, "all_gear.json")
shoes_csv = os.path.join(script_dir, "shoe_league_table.csv")
bikes_csv = os.path.join(script_dir, "bike_league_table.csv")

# Step 0: Ensure access token is valid (handle first-time and refresh)
load_dotenv()
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
authorization_code = os.getenv('AUTHORIZATION_CODE')
access_token = os.getenv('STRAVA_ACCESS_TOKEN')
expires_at = os.getenv('STRAVA_EXPIRES_AT')

now = int(time.time())

if expires_at and access_token and int(expires_at) > now:
    print("Access token is still valid, using existing token.")
    os.environ['STRAVA_ACCESS_TOKEN'] = access_token
elif refresh_token:
    print("Access token expired or missing, refreshing using refresh token...")
    new_access_token, new_refresh_token, new_expires_at = refresh_access_token(client_id, client_secret, refresh_token)
    if not new_access_token or not new_refresh_token or not new_expires_at:
        raise Exception("Failed to refresh access token. Please check your refresh token and try again.")
    os.environ['STRAVA_ACCESS_TOKEN'] = new_access_token
    os.environ['STRAVA_REFRESH_TOKEN'] = new_refresh_token
    os.environ['STRAVA_EXPIRES_AT'] = str(new_expires_at)
    # --- Update .env file with new tokens and expiry ---
    env_path = os.path.join(script_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
    else:
        lines = []
    new_lines = []
    found_access = found_refresh = found_expiry = False
    for line in lines:
        if line.startswith("STRAVA_ACCESS_TOKEN="):
            new_lines.append(f"STRAVA_ACCESS_TOKEN={new_access_token}\n")
            found_access = True
        elif line.startswith("STRAVA_REFRESH_TOKEN="):
            new_lines.append(f"STRAVA_REFRESH_TOKEN={new_refresh_token}\n")
            found_refresh = True
        elif line.startswith("STRAVA_EXPIRES_AT="):
            new_lines.append(f"STRAVA_EXPIRES_AT={new_expires_at}\n")
            found_expiry = True
        else:
            new_lines.append(line)
    if not found_access:
        new_lines.append(f"STRAVA_ACCESS_TOKEN={new_access_token}\n")
    if not found_refresh:
        new_lines.append(f"STRAVA_REFRESH_TOKEN={new_refresh_token}\n")
    if not found_expiry:
        new_lines.append(f"STRAVA_EXPIRES_AT={new_expires_at}\n")
    with open(env_path, "w") as f:
        f.writelines(new_lines)
    print(".env file updated with refreshed tokens and expiry.")
elif authorization_code:
    print("No refresh token found. Exchanging authorization code for tokens...")
    new_access_token, new_refresh_token, new_expires_at = exchange_code_for_tokens(client_id, client_secret, authorization_code)
    if not new_access_token or not new_refresh_token or not new_expires_at:
        raise Exception("Failed to exchange authorization code for tokens. Please check your code and try again.")
    os.environ['STRAVA_ACCESS_TOKEN'] = new_access_token
    os.environ['STRAVA_REFRESH_TOKEN'] = new_refresh_token
    os.environ['STRAVA_EXPIRES_AT'] = str(new_expires_at)
else:
    raise Exception("No refresh token or authorization code found. Please authorize the app with Strava.")

# Step 1: Download activities first
new_activities_count = fetch_activities(activities_path)

if new_activities_count == 0:
    print("No new activities. Skipping gear and league table updates.")
else:
    # Step 2: Extract gear IDs from activities
    extract_gear_ids_from_activities(activities_path, gear_ids_path)

    # Step 3: Download gear details
    fetch_gear_details(gear_ids_path, all_gear_path)

    # Step 4: Generate league tables
    combine_shoes(all_gear_path, activities_path, shoes_csv)
    combine_bikes(all_gear_path, activities_path, bikes_csv)