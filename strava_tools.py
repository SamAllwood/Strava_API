import os
import json
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()
access_token = os.getenv('STRAVA_ACCESS_TOKEN')
refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

def fetch_activities(json_path):
    # Download all activities if file doesn't exist, else only new ones
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            existing_activities = json.load(f)
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
        most_recent_dt = None  # None means fetch all

    def get_new_activities(after_datetime):
        all_new_activities = []
        page = 1
        per_page = 200
        max_pages = 20
        params = {'per_page': per_page, 'page': page}
        if after_datetime:
            params['after'] = int(after_datetime.timestamp())
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

    new_activities = get_new_activities(most_recent_dt)
    if not existing_activities and new_activities:
        unique_activities = sorted(new_activities, key=lambda x: x.get("start_date_local", x.get("start_date", "")), reverse=True)
        with open(json_path, "w") as f:
            json.dump(unique_activities, f, indent=2)
        print(f"Created activities.json with {len(unique_activities)} activities.")
    elif new_activities:
        all_activities = existing_activities + new_activities
        unique_activities = {a['id']: a for a in all_activities}.values()
        unique_activities = sorted(unique_activities, key=lambda x: x.get("start_date_local", x.get("start_date", "")), reverse=True)
        with open(json_path, "w") as f:
            json.dump(unique_activities, f, indent=2)
        print(f"Added {len(new_activities)} new activities. Total now: {len(unique_activities)}")
    else:
        print("No new activities to add.")

def extract_gear_ids_from_activities(activities_path, gear_ids_path):
    with open(activities_path, "r") as f:
        activities = json.load(f)
    gear_ids = set()
    for activity in activities:
        gear_id = activity.get("gear_id")
        if gear_id:
            gear_ids.add(gear_id)
    with open(gear_ids_path, "w") as f:
        json.dump(list(gear_ids), f)
    print(f"Extracted {len(gear_ids)} gear IDs from activities.")

def fetch_gear_details(gear_ids_path, all_gear_path):
    with open(gear_ids_path, "r") as f:
        gear_ids = json.load(f)
    all_gear = []
    for gid in gear_ids:
        response = requests.get(
            url=f'https://www.strava.com/api/v3/gear/{gid}',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        gear = response.json()
        all_gear.append(gear)
    with open(all_gear_path, "w") as f:
        json.dump(all_gear, f, indent=2)
    print(f"Saved all gear details to {all_gear_path}")

def combine_shoes(all_gear_path, activities_path, output_csv):
    # Load data
    with open(all_gear_path, "r") as f:
        all_gear = json.load(f)
    with open(activities_path, "r") as f:
        activities = json.load(f)

    # Filter only shoes from all_gear (IDs starting with 'g')
    shoes = {g['id']: g for g in all_gear if g['id'].startswith('g')}

    # Prepare stats for each shoe
    shoe_stats = {}
    for shoe_id, shoe in shoes.items():
        shoe_stats[shoe_id] = {
            "name": shoe.get("name", "Unknown"),
            "retired": shoe.get("retired", False),
            "longest_run": 0,
            "total_distance": 0,
            "total_elevation_gain": 0,
            "activity_count": 0,
            "average_run_length": 0,
            "total_time": 0,
            "average_pace": 0,
            "first_use": None  
        }

    # Aggregate activity data by shoe
    for activity in activities:
        gear_id = activity.get("gear_id")
        if gear_id in shoe_stats:
            dist = activity.get("distance", 0)
            elev = activity.get("total_elevation_gain", 0)
            time = activity.get("moving_time", 0)
            date_str = activity.get("start_date_local", activity.get("start_date"))
            try:
                date_obj = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
            except Exception:
                date_obj = None
            shoe_stats[gear_id]["total_distance"] += dist
            shoe_stats[gear_id]["total_elevation_gain"] += elev
            shoe_stats[gear_id]["longest_run"] = max(shoe_stats[gear_id]["longest_run"], dist)
            shoe_stats[gear_id]["activity_count"] += 1
            shoe_stats[gear_id]["total_time"] += time
            # Track first use
            if date_obj:
                if shoe_stats[gear_id]["first_use"] is None or date_obj < shoe_stats[gear_id]["first_use"]:
                    shoe_stats[gear_id]["first_use"] = date_obj

    # Calculate average run length and average pace for each shoe
    for stats in shoe_stats.values():
        if stats["activity_count"] > 0:
            stats["average_run_length"] = stats["total_distance"] / stats["activity_count"]
        else:
            stats["average_run_length"] = 0
        if stats["total_distance"] > 0:
            stats["average_pace"] = (stats["total_time"] / 60) / (stats["total_distance"] / 1000)
        else:
            stats["average_pace"] = 0
        # Format first use as 'Mon YYYY'
        if stats["first_use"]:
            stats["first_use_str"] = stats["first_use"].strftime("%b %Y")
        else:
            stats["first_use_str"] = "-"

    # Create league table sorted by average_run_length
    league = sorted(shoe_stats.values(), key=lambda x: x["average_run_length"], reverse=True)

    # Print league table
    print(f"{'Shoe':30} {'Retired':>8} {'Runs':>5} {'First Use':>10} {'Longest(km)':>12} {'Total Dist(km)':>15} {'Total Elev(km)':>15} {'Avg Run(km)':>12} {'Tot Time(h)':>12} {'Avg Pace':>10}")
    print("-" * 145)
    for s in league:
        avg_pace_str = f"{int(s['average_pace']):02d}:{int((s['average_pace']%1)*60):02d}" if s['average_pace'] > 0 else "-"
        retired_str = "Yes" if s.get('retired') else "No"
        print(f"{s['name'][:30]:30} {retired_str:>8} {s['activity_count']:5} {s['first_use_str']:>10} {s['longest_run']/1000:12.2f} {s['total_distance']/1000:15.2f} {s['total_elevation_gain']/1000:15.2f} {s['average_run_length']/1000:12.2f} {s['total_time']/3600:12.2f} {avg_pace_str:>10}")

    # Optionally, save league table to CSV
    import csv
    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Shoe", "Retired", "Runs", "First Use", "Longest Run (km)", "Total Distance (km)", "Total Elevation Gain (km)",
            "Average Run Length (km)", "Total Time (h)", "Average Pace (min/km)"
        ])
        for s in league:
            avg_pace_str = f"{int(s['average_pace']):02d}:{int((s['average_pace']%1)*60):02d}" if s['average_pace'] > 0 else "-"
            retired_str = "Yes" if s.get('retired') else "No"
            writer.writerow([
                s['name'],
                retired_str,
                s['activity_count'],
                s['first_use_str'],
                round(s['longest_run']/1000, 1),
                round(s['total_distance']/1000, 1),
                round(s['total_elevation_gain']/1000, 1),
                round(s['average_run_length']/1000, 1),
                round(s['total_time']/3600),
                avg_pace_str
            ])
    print(f"\nLeague table saved to {output_csv}")
    pass

def combine_bikes(all_gear_path, activities_path, output_csv):
    # Load data
    with open(all_gear_path, "r") as f:
        all_gear = json.load(f)
    with open(activities_path, "r") as f:
        activities = json.load(f)

    # Filter only bikes from all_gear (IDs starting with 'b')
    bikes = {g['id']: g for g in all_gear if g['id'].startswith('b')}

    # Prepare stats for each bike
    bike_stats = {}
    for bike_id, bike in bikes.items():
        bike_stats[bike_id] = {
            "name": bike.get("name", "Unknown"),
            "retired": bike.get("retired", False),  
            "longest_ride": 0,
            "total_distance": 0,
            "total_elevation_gain": 0,
            "activity_count": 0,
            "average_ride_length": 0,
            "total_time": 0,
            "average_speed": 0
        }

    # Aggregate activity data by bike
    for activity in activities:
        gear_id = activity.get("gear_id")
        if gear_id in bike_stats:
            dist = activity.get("distance", 0)
            elev = activity.get("total_elevation_gain", 0)
            time = activity.get("moving_time", 0)  
            bike_stats[gear_id]["total_distance"] += dist
            bike_stats[gear_id]["total_elevation_gain"] += elev
            bike_stats[gear_id]["longest_ride"] = max(bike_stats[gear_id]["longest_ride"], dist)
            bike_stats[gear_id]["activity_count"] += 1
            bike_stats[gear_id]["total_time"] += time

    # Calculate average ride length and average speed for each bike
    for stats in bike_stats.values():
        if stats["activity_count"] > 0:
            stats["average_ride_length"] = stats["total_distance"] / stats["activity_count"] / 1000  
        else:
            stats["average_ride_length"] = 0
        # Calculate average speed (km/h)
        if stats["total_time"] > 0:
            stats["average_speed"] = (stats["total_distance"] / 1000) / (stats["total_time"] / 3600)
        else:
            stats["average_speed"] = 0

    # Create league table sorted by average_ride_length
    league = sorted(bike_stats.values(), key=lambda x: x["average_ride_length"], reverse=True)

    # Calculate totals
    totals = {
        "name": "TOTAL",
        "activity_count": sum(s['activity_count'] for s in league),
        "longest_ride": max(s['longest_ride'] for s in league) if league else 0,
        "total_distance": sum(s['total_distance'] for s in league),
        "total_elevation_gain": sum(s['total_elevation_gain'] for s in league),
        "average_ride_length": sum(s['total_distance'] for s in league) / sum(s['activity_count'] for s in league) / 1000 if sum(s['activity_count'] for s in league) > 0 else 0,
        "total_time": sum(s['total_time'] for s in league),
        "average_speed": (sum(s['total_distance'] for s in league) / 1000) / (sum(s['total_time'] for s in league) / 3600) if sum(s['total_time'] for s in league) > 0 else 0
    }

    # Print league table
    print(f"{'Bike':30} {'Retired':>8} {'Rides':>5} {'Longest(km)':>12} {'Total Dist(km)':>15} {'Total Elev(km)':>15} {'Avg Ride(km)':>12} {'Tot Time(h)':>12} {'Avg Speed':>10}")
    print("-" * 130)
    for s in league:
        retired_str = "Yes" if s.get('retired') else "No"
        print(f"{s['name'][:30]:30} {retired_str:>8} {s['activity_count']:5} {s['longest_ride']/1000:12.2f} {s['total_distance']/1000:15.2f} {s['total_elevation_gain']/1000:15.2f} {s['average_ride_length']:12.2f} {s['total_time']/3600:12.2f} {s['average_speed']:10.2f}")
    # Print totals row
    print("-" * 130)
    print(f"{'TOTAL':30} {'':>8} {totals['activity_count']:5} {totals['longest_ride']/1000:12.2f} {totals['total_distance']/1000:15.2f} {totals['total_elevation_gain']/1000:15.2f} {totals['average_ride_length']:12.2f} {totals['total_time']/3600:12.2f} {totals['average_speed']:10.2f}")

    # Optionally, save league table to CSV
    import csv
    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Bike", "Retired", "Rides", "Longest Ride (km)", "Total Distance (km)", "Total Elevation Gain (km)",
            "Average Ride Length (km)", "Total Time (h)", "Average Speed (km/h)"
        ])
        for s in league:
            retired_str = "Yes" if s.get('retired') else "No"
            writer.writerow([
                s['name'],
                retired_str,
                s['activity_count'],
                round(s['longest_ride']/1000, 1),
                round(s['total_distance']/1000, 1),
                round(s['total_elevation_gain']/1000, 1),
                round(s['average_ride_length'], 1),
                round(s['total_time']/3600),  # Nearest hour
                round(s['average_speed'], 1)
            ])
        # Write totals row
        writer.writerow([
            'TOTAL',
            '',
            totals['activity_count'],
            round(totals['longest_ride']/1000, 1),
            round(totals['total_distance']/1000, 1),
            round(totals['total_elevation_gain']/1000, 1),
            round(totals['average_ride_length'], 1),
            round(totals['total_time']/3600),  # Nearest hour
            round(totals['average_speed'], 1)
        ])
    print(f"\nLeague table saved to {output_csv}")
    pass

def refresh_access_token(client_id, client_secret, refresh_token):
    response = requests.post(
        url="https://www.strava.com/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
    )
    tokens = response.json()
    if "access_token" in tokens and "refresh_token" in tokens:
        # Optionally update your .env or a local file with new tokens
        return tokens["access_token"], tokens["refresh_token"]
    else:
        raise Exception(f"Failed to refresh token: {tokens}")