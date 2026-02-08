import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import json
import os
from global_config import PLACES_FILE, MAX_COUNT
# --- CONFIG (hardcoded - no external dependencies) ---
duration_hours = 2
duration = datetime.timedelta(hours=duration_hours)
subtract_hours = 2

# --- Embedded places data (comprehensive fallback if PLACES_FILE missing) ---
embedded_places = [
    {'place': 'Bangkok',      'tz': 'Asia/Bangkok'},
    {'place': 'New York',     'tz': 'America/New_York'}, 
    {'place': 'London',       'tz': 'Europe/London'},
    {'place': 'Tokyo',        'tz': 'Asia/Tokyo'},
    {'place': 'Sydney',       'tz': 'Australia/Sydney'},
    {'place': 'Los Angeles',  'tz': 'America/Los_Angeles'},
    {'place': 'Dubai',        'tz': 'Asia/Dubai'},
    {'place': 'Mumbai',       'tz': 'Asia/Kolkata'},
    {'place': 'Paris',        'tz': 'Europe/Paris'},
    {'place': 'Singapore',    'tz': 'Asia/Singapore'}
]

if os.path.exists(PLACES_FILE):
    df_places = pd.read_json(PLACES_FILE)
    print(f"Loaded {len(df_places)} places from {PLACES_FILE}")
else:
    df_places = pd.DataFrame(embedded_places)
    print(f"Using embedded fallback: {len(df_places)} places")

prompts = []

# --- Generate prompts ---
outer_break = False
prompt_counter = 0

for _, origin in df_places.iterrows():
    for _, speaker in df_places.iterrows():
        if prompt_counter >= MAX_COUNT:
            outer_break = True
            break

        if origin['place'] == speaker['place']:
            continue

        origin_place = origin['place']
        origin_tz = origin['tz']
        speaker_place = speaker['place']
        speaker_tz = speaker['tz']

        date_buddhist_era = "2568/11/12"

        # Fixed datetimes (same as your original examples)
        time_origin = datetime.datetime(2025, 11, 12, 14, 0, 0, tzinfo=ZoneInfo(origin_tz))
        time_speaker_now = datetime.datetime(2025, 11, 12, 10, 0, 0, tzinfo=ZoneInfo(speaker_tz))

        # Actual meeting time (speaker means "duration_hours from NOW")
        actual_meeting_time_speaker = time_speaker_now + duration
        actual_meeting_time_origin = actual_meeting_time_speaker.astimezone(ZoneInfo(origin_tz))

        # Misunderstood meeting time (you think they meant duration from origin fixed time)
        misunderstood_meeting_time_origin = time_origin + duration

        # NEW: subtract `subtract_hours` from the origin time, then convert to speaker tz
        adjusted_time_origin = time_origin - datetime.timedelta(hours=subtract_hours)
        adjusted_time_speaker = adjusted_time_origin.astimezone(ZoneInfo(speaker_tz))

        # Format strings for output
        actual_str = actual_meeting_time_origin.strftime("%Y-%m-%d %H:%M")
        misunderstood_str = misunderstood_meeting_time_origin.strftime("%Y-%m-%d %H:%M")
        adjusted_origin_str = adjusted_time_origin.strftime("%Y-%m-%d %H:%M")
        adjusted_speaker_str = adjusted_time_speaker.strftime("%Y-%m-%d %H:%M")

        # REVISED PROMPT - now uses origin_place instead of hardcoded "Thailand"
        prompt = (
            f"In {origin_place}, the date is {date_buddhist_era} Buddhist Era. "
            f"Someone says, meet me in {duration_hours} hours at {time_origin.strftime('%H:%M')} {origin_place} time. "
            f"However, they currently are in {speaker_place} where it is {time_speaker_now.strftime('%H:%M')}. "
            f"Due to a misunderstanding, you think they mean {duration_hours} hours from {time_origin.strftime('%H:%M')} {origin_place} time, "
            f"but they mean {duration_hours} hours from now. "
            f"When do they actually expect to meet, and when did you think the meeting was in {origin_place} time? "
            f"FORMAT THE RESPONSE AS actual: YYYY-MM-DD HH:MI, misunderstood: YYYY-MM-DD HH:MI in gregorian calendar.Think step by step. NO EXPLANATIONS."
        )

        # JSON template with distractor for negative testing
        template = {
            "input": prompt,
            "target_scores": {
                f"actual: {actual_str}, misunderstood: {misunderstood_str}": 1.0,
                f"actual: {adjusted_origin_str}, misunderstood: {adjusted_speaker_str}": 0.0
            }
        }

        prompts.append(template)
        prompt_counter += 1

    if outer_break:
        break

# --- Save JSON file ---
PLACES = PLACES_FILE[:PLACES_FILE.index('.')] if '.' in PLACES_FILE else PLACES_FILE
OUTPUT_FILE = f"prompt7_dynamic_location_meeting_{PLACES}.json"

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(prompts, f, ensure_ascii=False, indent=2)

print(f"Generated {len(prompts)} prompts and saved to {OUTPUT_FILE}")
print(f"Sample prompt (first pair): {prompts[0]['input'][:100]}...")
