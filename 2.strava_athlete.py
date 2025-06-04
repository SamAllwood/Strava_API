import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()  # Loads variables from .env into environment

def save_tokens_to_env(access_token, refresh_token, env_path=None):
    if env_path is None:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    # Read existing lines
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
    else:
        lines = []
    new_lines = []
    found_access = found_refresh = False
    for line in lines:
        if line.startswith("STRAVA_ACCESS_TOKEN="):
            new_lines.append(f"STRAVA_ACCESS_TOKEN={access_token}\n")
            found_access = True
        elif line.startswith("STRAVA_REFRESH_TOKEN="):
            new_lines.append(f"STRAVA_REFRESH_TOKEN={refresh_token}\n")
            found_refresh = True
        else:
            new_lines.append(line)
    if not found_access:
        new_lines.append(f"STRAVA_ACCESS_TOKEN={access_token}\n")
    if not found_refresh:
        new_lines.append(f"STRAVA_REFRESH_TOKEN={refresh_token}\n")
    with open(env_path, "w") as f:
        f.writelines(new_lines)

def refresh_access_token(client_id, client_secret, refresh_token):
    response = requests.post(
        url='https://www.strava.com/oauth/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
    )
    tokens = response.json()
    if 'access_token' in tokens and 'refresh_token' in tokens:
        save_tokens_to_env(tokens['access_token'], tokens['refresh_token'])
        return tokens['access_token'], tokens['refresh_token']
    else:
        raise Exception(f"Failed to refresh token: {tokens}")

def get_athlete(access_token):
    response = requests.get(
        url='https://www.strava.com/api/v3/athlete',
        headers={
            'Authorization': f'Bearer {access_token}'
        }
    )
    # If token expired, refresh and retry once
    if response.status_code == 401:
        print("Access token expired, refreshing...")
        access_token, _ = refresh_access_token(CLIENT_ID, CLIENT_SECRET, refresh_token)
        response = requests.get(
            url='https://www.strava.com/api/v3/athlete',
            headers={
                'Authorization': f'Bearer {access_token}'
            }
        )
    return response.json()

def get_gear_ids(athlete_json):
    gear_ids = []
    # Extract bike gear IDs
    for bike in athlete_json.get("bikes", []):
        gear_ids.append(bike.get("id"))
    # Extract shoe gear IDs
    for shoe in athlete_json.get("shoes", []):
        gear_ids.append(shoe.get("id"))
    return gear_ids

# Example usage:
if __name__ == "__main__":
    access_token = os.getenv('STRAVA_ACCESS_TOKEN')
    refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')

    athlete = get_athlete(access_token)
    import pprint
    pprint.pprint(athlete)
    gear_ids = get_gear_ids(athlete)
    print("Gear IDs:", gear_ids)
    print(f"Athlete: {athlete.get('firstname', '')} {athlete.get('lastname', '')} (id: {athlete.get('id', '')})")
    
    # Save gear IDs to a JSON file in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gear_path = os.path.join(script_dir, "gear_ids.json")
    with open(gear_path, "w") as f:
        json.dump(gear_ids, f)
    print(f"Gear IDs saved to {gear_path}")