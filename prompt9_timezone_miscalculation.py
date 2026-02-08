import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import json
import os
import random


from global_config import MAX_COUNT,PLACES_FILE
# --- CONFIG ---


df_places = pd.read_json(PLACES_FILE)

# Fallback places if file missing/empty
embedded_places = [
    {'place': 'Bangkok',      'tz': 'Asia/Bangkok'},
    {'place': 'New York',     'tz': 'America/New_York'}, 
    {'place': 'London',       'tz': 'Europe/London'},
    {'place': 'Tokyo',        'tz': 'Asia/Tokyo'},
    {'place': 'Sydney',       'tz': 'Australia/Sydney'},
    {'place': 'Dubai',        'tz': 'Asia/Dubai'},
    {'place': 'Los Angeles',  'tz': 'America/Los_Angeles'},
    {'place': 'Paris',        'tz': 'Europe/Paris'},
    {'place': 'Singapore',    'tz': 'Asia/Singapore'},
    {'place': 'Mumbai',       'tz': 'Asia/Kolkata'}
]

# Common timezone mistake offsets
wrong_offsets = [2, 3, 4, 6, 7, 8, 9, 12]  
wrong_formats = [
    lambda t: t.strftime('%I:%M %p').lstrip('0').lower(),
    lambda t: t.strftime('%l:%M%p').strip().lower(), 
    lambda t: f"{t.strftime('%I:%M')} {t.strftime('%p').lower()}",
]

prompt_counter = 0
prompts = []

try:
    df_places = pd.read_json(PLACES_FILE)
    if df_places.empty:
        raise ValueError("Empty file")
    print(f"Loaded {len(df_places)} places from {PLACES_FILE}")
except:
    df_places = pd.DataFrame(embedded_places)
    print(f"Using fallback places ({len(df_places)} locations)")

# --- Generate prompts ---
for idx, place1 in df_places.iterrows():
    if prompt_counter >= MAX_COUNT:
        break
    for idx2, place2 in df_places.iterrows():
        if prompt_counter >= MAX_COUNT:
            break
        if place1['place'] == place2['place']:
            continue

        origin_location = place1["place"]      # Any origin now
        origin_tz = place1["tz"]
        reference_location = place2["place"]
        reference_tz = place2["tz"]

        # Event start time in ORIGIN location (not just Marquesas)
        event_start_origin = datetime.datetime(2025, 11, 12, 14, 30, 0, tzinfo=ZoneInfo(origin_tz))

        # Reference time in reference location
        reference_time = datetime.datetime(2025, 11, 12, 10, 0, 0, tzinfo=ZoneInfo(reference_tz))

        # Convert event start time to reference location (CORRECT)
        event_start_reference = event_start_origin.astimezone(ZoneInfo(reference_tz))
        
        # WRONG time - pick random offset + format
        wrong_offset_hours = random.choice(wrong_offsets)
        wrong_diff = datetime.timedelta(hours=wrong_offset_hours)
        wrong_event_time = reference_time + wrong_diff
        wrong_format = random.choice(wrong_formats)
        wrong_event_time_str = wrong_format(wrong_event_time)

        # JSON template - generic origin location
        template = {
            "input": (
                f"Someone says that the event starts at {event_start_origin.strftime('%H:%M')} "
                f"{origin_location} time, which is {wrong_offset_hours} hours after {reference_time.strftime('%H:%M')} "
                f"in {reference_location}. However, their calculation is incorrect. "
                f"What is the actual time in {reference_location} when the event starts? "
                f"GIVE RESPONSE IN HH:MI format. "
                f"Think step by step. NO EXPLANATIONS."
            ),
            "target_scores": {
                f"{event_start_reference.strftime('%H:%M')}": 1.0,      
                f"{wrong_event_time_str}": 0.0                          
            }
        }

        prompts.append(template)
        prompt_counter += 1

PLACES = os.path.splitext(os.path.basename(PLACES_FILE))[0]
OUTPUT_FILE = f"prompt9_timezone_miscalculation_{PLACES}.json"  # Generic name

# --- Save JSON file ---
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(prompts, f, ensure_ascii=False, indent=2)

print(f"Generated {len(prompts)} prompts and saved to {OUTPUT_FILE}")
print(f"Sample (first): {prompts[0]['input'][:150]}...")
print(f"Sample scores: {prompts[0]['target_scores']}")
