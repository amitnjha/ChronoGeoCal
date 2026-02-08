import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import json
from global_config import MAX_COUNT,PLACES_FILE
# --- CONFIG ---

prompt_counter = 0

df_places = pd.read_json(PLACES_FILE)

place_list = df_places[['place','tz']]


prompts = []

# --- Generate prompts ---
for idx, place1 in df_places.iterrows():
    for idx2, place2 in df_places.iterrows():
        if prompt_counter >= MAX_COUNT:
            break
        if place1['place'] == place2['place']:
            continue

        lord_howe_island = place1["place"]
        lord_howe_tz = place1["tz"]
        location2 = place2['place']
        location2_tz = place2['tz']

        # DST transition in Lord Howe Island: 2025-10-05, 2:00 AM spring forward by 30 min
        dst_date = datetime.datetime(2025, 10, 5, 2, 0, 0, tzinfo=ZoneInfo(lord_howe_tz))
        dst_action = "spring forward"
        transition_time = "2:00 AM (clocks spring forward by 30 minutes)"

        # Event A ends at given time in Lord Howe Island
        event_a_end = datetime.datetime(2025, 10, 5, 15, 0, 0, tzinfo=ZoneInfo(lord_howe_tz))

        # Event B in location2 starts when Event A ends
        event_b_start = event_a_end.astimezone(ZoneInfo(location2_tz))

        # Duration of Event B
        duration_b = datetime.timedelta(hours=2)
        event_b_end = event_b_start + duration_b

        # JSON template
        template = {
            "input": (
                f"Lord Howe Island (Australia) is unique: DST shifts clocks by only 30 minutes (not 1 hour), "
                f"changing between UTC+10:30 and UTC+11. On {dst_date.strftime('%Y-%m-%d')}, clocks {dst_action}. "
                f"Event A ends at {event_a_end.strftime('%H:%M')}. Event B in {location2} must start exactly when A ends. "
                f"If B lasts {duration_b.seconds // 3600} hours, when does B end in {location2}? GIVE RESPONSE IN YYYY-MM-DD HH:MI:SS format.Think step by step. NO EXPLANATIONS."
            ),
            "target_scores": {
                f"{event_b_end.astimezone(ZoneInfo(location2_tz)).strftime('%Y-%m-%d %H:%M %Z')}": 1.0,
                "Distractor: assume clocks shift 1 hour": 0.0
            }
        }

        prompts.append(template)
        prompt_counter += 1

INPUT_PLACES_FILE = PLACES_FILE
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]
OUTPUT_FILE = "prompt10_lord_howe_dst_"+PLACES+".json"

# --- Save JSON file ---
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(prompts, f, ensure_ascii=False, indent=2)

print(f"Generated {len(prompts)} prompts and saved to {OUTPUT_FILE}")
