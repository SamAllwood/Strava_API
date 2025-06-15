from strava_tools import fetch_activities, extract_gear_ids_from_activities, fetch_gear_details, combine_shoes, combine_bikes, refresh_access_token
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
activities_path = os.path.join(script_dir, "activities.json")
gear_ids_path = os.path.join(script_dir, "gear_ids.json")
all_gear_path = os.path.join(script_dir, "all_gear.json")
shoes_csv = os.path.join(script_dir, "shoe_league_table.csv")
bikes_csv = os.path.join(script_dir, "bike_league_table.csv")

# Step 1: Download activities first
fetch_activities(activities_path)

# Step 2: Extract gear IDs from activities
extract_gear_ids_from_activities(activities_path, gear_ids_path)

# Step 3: Download gear details
fetch_gear_details(gear_ids_path, all_gear_path)

# Step 4: Generate league tables
combine_shoes(all_gear_path, activities_path, shoes_csv)
combine_bikes(all_gear_path, activities_path, bikes_csv)