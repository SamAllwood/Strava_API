import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()  # Loads variables from .env into environment

access_token = os.getenv('STRAVA_ACCESS_TOKEN')
refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

script_dir = os.path.dirname(os.path.abspath(__file__))
gear_path = os.path.join(script_dir, "gear_ids.json")
with open(gear_path, "r") as f:
    gear_ids = json.load(f)

print("Loaded gear IDs:", gear_ids)

def get_gear(access_token, gear_id):
    response = requests.get(
        url=f'https://www.strava.com/api/v3/gear/{gear_id}',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    return response.json()


def main():
    # Loop through all gear IDs
    all_gear = []
    for gid in gear_ids:    
        gear = get_gear(access_token, gid)
        all_gear.append(gear)
    
    # Save gear data to a JSON file in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "all_gear.json")
    with open(json_path, "w") as f:
        json.dump(all_gear, f, indent=4)
    print(f"Gear data saved to {json_path}")

if __name__ == '__main__':
    main()