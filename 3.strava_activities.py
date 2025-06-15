import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime

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

def get_new_activities(access_token, after_datetime):
    all_new_activities = []
    page = 1
    per_page = 200
    max_pages = 20
    params = {'per_page': per_page, 'page': page}
    if after_datetime is not None:
        after_epoch = int(after_datetime.timestamp())
        params['after'] = after_epoch
    while page <= max_pages:
        params['page'] = page
        response = requests.get(
            url='https://www.strava.com/api/v3/athlete/activities',
            headers={'Authorization': f'Bearer {access_token}'},
            params=params
        )
        activities = response.json()
        if not isinstance(activities, list) or not activities:
            break
        all_new_activities.extend(activities)
        page += 1
    return all_new_activities

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "activities.json")
    # Load existing activities if file exists
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            existing_activities = json.load(f)
        # Find the most recent start_date_local
        if existing_activities:
            most_recent = max(
                existing_activities,
                key=lambda x: x.get("start_date_local", x.get("start_date", "1970-01-01T00:00:00Z"))
            )
            most_recent_date = most_recent.get("start_date_local", most_recent.get("start_date"))
            most_recent_dt = datetime.strptime(most_recent_date[:19], "%Y-%m-%dT%H:%M:%S")
        else:
            most_recent_dt = datetime(1970, 1, 1)
    else:
        existing_activities = []
        # If no file, fetch ALL activities by setting 'after' to 0 (epoch)
        most_recent_dt = datetime(1970, 1, 1)

    athlete = get_athlete(access_token)
    print(f"Athlete: {athlete.get('firstname', '')} {athlete.get('lastname', '')} (id: {athlete.get('id', '')})")
    if not existing_activities:
        # No after parameter, fetch all activities
        new_activities = get_new_activities(access_token, None)
    else:
        new_activities = get_new_activities(access_token, most_recent_dt)
    print(f"\nFound {len(new_activities)} new activities since {most_recent_dt.isoformat()}.")

    # If no activities.json or it's empty, just use new_activities as the full list
    if not existing_activities and new_activities:
        unique_activities = sorted(new_activities, key=lambda x: x.get("start_date_local", x.get("start_date", "")), reverse=True)
        with open(json_path, "w") as f:
            json.dump(unique_activities, f, indent=2)
        print(f"Created activities.json with {len(unique_activities)} activities.")
    elif new_activities:
        all_activities = existing_activities + new_activities
        # Remove duplicates by activity id
        unique_activities = {a['id']: a for a in all_activities}.values()
        unique_activities = sorted(unique_activities, key=lambda x: x.get("start_date_local", x.get("start_date", "")), reverse=True)
        with open(json_path, "w") as f:
            json.dump(unique_activities, f, indent=2)
        print(f"Added {len(new_activities)} new activities. Total now: {len(unique_activities)}")
    else:
        print("No new activities to add.")

if __name__ == '__main__':
    main()