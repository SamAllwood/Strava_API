from strava_tools import (
    fetch_activities, extract_gear_ids_from_activities, fetch_gear_details,
    combine_shoes, combine_bikes, refresh_access_token, exchange_code_for_tokens
)
import os
from dotenv import load_dotenv

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

if refresh_token:
    # Normal case: refresh access token
    print("Refreshing access token using refresh token...")
    new_access_token, new_refresh_token = refresh_access_token(client_id, client_secret, refresh_token)
    if not new_access_token or not new_refresh_token:
        raise Exception("Failed to refresh access token. Please check your refresh token and try again.")
    os.environ['STRAVA_ACCESS_TOKEN'] = new_access_token
    os.environ['STRAVA_REFRESH_TOKEN'] = new_refresh_token
elif authorization_code:
    # First time: exchange authorization code for tokens
    print("No refresh token found. Exchanging authorization code for tokens...")
    new_access_token, new_refresh_token = exchange_code_for_tokens(client_id, client_secret, authorization_code)
    if not new_access_token or not new_refresh_token:
        raise Exception("Failed to exchange authorization code for tokens. Please check your code and try again.")
    os.environ['STRAVA_ACCESS_TOKEN'] = new_access_token
    os.environ['STRAVA_REFRESH_TOKEN'] = new_refresh_token
else:
    raise Exception("No refresh token or authorization code found. Please authorize the app with Strava.")

# Step 1: Download activities first
fetch_activities(activities_path)

# Step 2: Extract gear IDs from activities
extract_gear_ids_from_activities(activities_path, gear_ids_path)

# Step 3: Download gear details
fetch_gear_details(gear_ids_path, all_gear_path)

# Step 4: Generate league tables
combine_shoes(all_gear_path, activities_path, shoes_csv)
combine_bikes(all_gear_path, activities_path, bikes_csv)