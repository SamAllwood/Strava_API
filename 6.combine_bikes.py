import json
import os

# Set up paths
script_dir = os.path.dirname(os.path.abspath(__file__))
gear_path = os.path.join(script_dir, "all_gear.json")
activities_path = os.path.join(script_dir, "activities.json")

# Load data
with open(gear_path, "r") as f:
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
        "retired": bike.get("retired", False),  # <-- Add retired status
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
        time = activity.get("moving_time", 0)  # <-- changed from elapsed_time to moving_time
        bike_stats[gear_id]["total_distance"] += dist
        bike_stats[gear_id]["total_elevation_gain"] += elev
        bike_stats[gear_id]["longest_ride"] = max(bike_stats[gear_id]["longest_ride"], dist)
        bike_stats[gear_id]["activity_count"] += 1
        bike_stats[gear_id]["total_time"] += time

# Calculate average ride length and average speed for each bike
for stats in bike_stats.values():
    if stats["activity_count"] > 0:
        stats["average_ride_length"] = stats["total_distance"] / stats["activity_count"] / 1000  # in km
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
csv_path = os.path.join(script_dir, "bike_league_table.csv")
with open(csv_path, "w", newline="") as csvfile:
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
print(f"\nLeague table saved to {csv_path}")
