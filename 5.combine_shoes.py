import json
import os
from datetime import datetime

# Set up paths
script_dir = os.path.dirname(os.path.abspath(__file__))
gear_path = os.path.join(script_dir, "all_gear.json")
activities_path = os.path.join(script_dir, "activities.json")

# Load data
with open(gear_path, "r") as f:
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
        "first_use": None  # <-- Add first use
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
csv_path = os.path.join(script_dir, "shoe_league_table.csv")
with open(csv_path, "w", newline="") as csvfile:
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
print(f"\nLeague table saved to {csv_path}")