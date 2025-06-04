
# R Analysis of Strava Activity Data
# Load necessary libraries
library(tidyverse)
library(ggplot2)
library(jsonlite)

# Load the JSON data
raw_data <- jsonlite::fromJSON("activities.json") 
strava_data <- raw_data %>%
  select(
    name,
    type,
    start_date_local,
    distance,
    moving_time,
    elapsed_time,
    total_elevation_gain,
    average_speed,
    max_speed,
    average_heartrate,
    max_heartrate,
    achievement_count,
    kudos_count,
    comment_count,
    athlete_count,
    commute,
    gear_id,
    average_speed,
    suffer_score,
    average_temp
  ) %>%
  mutate(
    start_data = as.Date(start_date_local),
    distance_km = distance / 1000,  # Convert distance to kilometers
    moving_time = sprintf("%02d:%02d", moving_time %/% 60, moving_time %% 60), # Convert moving time to HH:MM format
    elapsed_time = sprintf("%02d:%02d", elapsed_time %/% 60, elapsed_time %% 60), # Convert elapsed time to HH:MM format
      ) %>%
  select(-c(start_date_local)) %>%
  rename(average_heartrate_bpm = average_heartrate,
         max_heartrate_bpm = max_heartrate,
         activity_name = name)

# Load gear data
gear_data <- jsonlite::fromJSON("all_gear.json") #%>%
  select(id, name, primary) %>%
  rename(gear_id = id, gear_name = name)

# Convert the data to a tibble for easier manipulation
strava_data <- as_tibble(strava_data)

# Save the cleaned data to a CSV file
write_csv(strava_data, "strava_data_cleaned.csv")
