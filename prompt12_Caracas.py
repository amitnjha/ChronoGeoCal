import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import json
from global_config import MAX_COUNT,PLACES_FILE
# --- CONFIG ---

prompt_counter = 0

INPUT_PLACES_FILE = PLACES_FILE
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]
PROMPTS_FILE = "prompt12_caracas_meeting_"+PLACES+".json"

df_places = pd.read_json(PLACES_FILE)

place_list = df_places[['place','tz']]


prompts = []

# --- Helper function to format durations ---
def format_timedelta(td):
    total_minutes = int(td.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours} hours, {minutes} minutes"

# --- Generate prompts ---
for idx, place1 in df_places.iterrows():
    if prompt_counter >= MAX_COUNT:
        break

    caracas = "Caracas"
    caracas_tz = "America/Caracas"
    your_location = place1['place']
    your_tz = place1['tz']

    # Meeting times in Caracas
    meeting_start_caracas = datetime.datetime(2025, 11, 11, 14, 0, 0, tzinfo=ZoneInfo(caracas_tz))
    meeting_end_caracas = datetime.datetime(2025, 11, 11, 16, 30, 0, tzinfo=ZoneInfo(caracas_tz))

    # Convert meeting times to your location
    meeting_start_your = meeting_start_caracas.astimezone(ZoneInfo(your_tz))
    meeting_end_your = meeting_end_caracas.astimezone(ZoneInfo(your_tz))

    # Actual duration
    actual_duration = meeting_end_caracas - meeting_start_caracas
    # Example wrong duration
    wrong_duration = datetime.timedelta(hours=3)

    # JSON template
    template = {
        "input": (
            f"Someone in Caracas says, The meeting lasted from {meeting_start_caracas.strftime('%H:%M')} "
            f"to {meeting_end_caracas.strftime('%H:%M')} yesterday. However, you are in {your_location}, "
            f"and when you checked the start time in your timezone, your clock showed {meeting_start_your.strftime('%H:%M')}. "
            f"The meeting actually lasted {format_timedelta(actual_duration)}, but due to timezone confusion, you calculated it lasted {format_timedelta(wrong_duration)}. "
            f"What was the actual duration, and what time did it end in both locations?"
        ),
        "target_scores": {
            f"Actual duration: {format_timedelta(actual_duration)}; Meeting ended in Caracas at {meeting_end_caracas.strftime('%Y-%m-%d %H:%M')}; "
            f"Meeting ended in {your_location} at {meeting_end_your.strftime('%Y-%m-%d %H:%M')}": 1.0,
            "Distractor: Assume wrong duration": 0.0
        }
    }

    prompts.append(template)
    prompt_counter += 1

# --- Save JSON file ---
with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
    json.dump(prompts, f, ensure_ascii=False, indent=2)

print(f"Generated {len(prompts)} prompts and saved to {PROMPTS_FILE}")