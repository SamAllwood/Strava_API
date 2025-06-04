import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()  # Loads variables from .env into environment

access_token = os.getenv('STRAVA_ACCESS_TOKEN')
refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
print(f"Access Token: {access_token}")

def get_athlete(access_token):
    response = requests.get(
        url='https://www.strava.com/api/v3/athlete',
        headers={
            'Authorization': f'Bearer {access_token}'
        }
    )
    try:
        data = response.json()
    except Exception:
        print("Failed to parse JSON. Response text:")
        print(response.text)
        raise
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(data)
        raise Exception("Failed to fetch athlete data")
    return data

def get_all_activities(access_token):
    all_activities = []
    page = 1
    per_page = 200  # Strava's max per page
    max_pages = 20  # Only download the first 20 pages
    while page <= max_pages:
        response = requests.get(
            url='https://www.strava.com/api/v3/athlete/activities?per_page=200',
            headers={'Authorization': f'Bearer {access_token}'},
            params={'per_page': per_page, 'page': page}
        )
        activities = response.json()
        if not isinstance(activities, list):
            print("Unexpected response:", activities)
            break
        all_activities.extend(activities)
        page += 1
    return all_activities

def main():
    athlete = get_athlete(access_token)
    print(f"Athlete: {athlete.get('firstname', '')} {athlete.get('lastname', '')} (id: {athlete.get('id', '')})")
    activities = get_all_activities(access_token)
    print(f"\nShowing {min(5, len(activities))} of {len(activities)} activities:")
    for activity in activities[:5]:  # Show only first 5
        print(f"- {activity.get('name')} | {activity.get('distance')}m | {activity.get('start_date_local')}")
    # Save all activities to a JSON file in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "activities.json")
    with open(json_path, "w") as f:
        json.dump(activities, f, indent=2)
    print(f"\nAll activities saved to {json_path}")
    
if __name__ == '__main__':
    main()