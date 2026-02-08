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

    # VARY MEETING TIMES FOR EACH PROMPT
    hour_offset = idx % 6
    minute_offset = (idx * 15) % 60
    
    meeting_start_caracas = datetime.datetime(2025, 11, 11, 14 + hour_offset, minute_offset, 0, tzinfo=ZoneInfo(caracas_tz))
    meeting_end_caracas = meeting_start_caracas + datetime.timedelta(hours=2, minutes=30)

    # Convert meeting times to your location
    meeting_start_your = meeting_start_caracas.astimezone(ZoneInfo(your_tz))
    meeting_end_your = meeting_end_caracas.astimezone(ZoneInfo(your_tz))

    actual_duration = meeting_end_caracas - meeting_start_caracas
    
    # WRONG ANSWER: Always different from correct - rotates through 3 common mistakes
    wrong_duration = datetime.timedelta(hours=3)
    
    # Case 1: start + 3hr (most common)
    wrong_end_your1 = meeting_start_your + wrong_duration
    # Case 2: Caracas end time directly  
    wrong_end_your2 = meeting_end_caracas.astimezone(ZoneInfo(your_tz))
    # Case 3: start + actual duration + 30min error
    wrong_end_your3 = meeting_start_your + actual_duration + datetime.timedelta(minutes=30)
    
    # Select wrong answer that ≠ correct answer
    candidates = [wrong_end_your1, wrong_end_your2, wrong_end_your3]
    wrong_end_your = min(candidates, key=lambda x: abs((x-meeting_end_your).total_seconds()) if x != meeting_end_your else float('inf'))

    # PROMPT 1: Caracas end time only
    template1 = {
        "input": (
            f"Someone in Caracas says, The meeting lasted from {meeting_start_caracas.strftime('%H:%M')} "
            f"to {meeting_end_caracas.strftime('%H:%M')} yesterday. However, you are in {your_location}, "
            f"and when you checked the start time in your timezone, your clock showed {meeting_start_your.strftime('%H:%M')}. "
            f"The meeting actually lasted {format_timedelta(actual_duration)}, but due to timezone confusion, you calculated it lasted {format_timedelta(wrong_duration)}. "
            f"What time did it end in Caracas? "
            f"GIVE RESPONSE IN YYYY-MM-DD HH:MM:SS format. "
            f"Think step by step. NO EXPLANATIONS."
        ),
        "target_scores": {
            f"{meeting_end_caracas.strftime('%Y-%m-%d %H:%M:%S')}": 1.0,  # CORRECT
            f"{wrong_end_your.strftime('%Y-%m-%d %H:%M:%S')}": 0.0        # WRONG (guaranteed ≠ correct)
        }
    }
    prompts.append(template1)
    prompt_counter += 1

    if prompt_counter >= MAX_COUNT:
        break

    # PROMPT 2: Your location end time only  
    template2 = {
        "input": (
            f"Someone in Caracas says, The meeting lasted from {meeting_start_caracas.strftime('%H:%M')} "
            f"to {meeting_end_caracas.strftime('%H:%M')} yesterday. However, you are in {your_location}, "
            f"and when you checked the start time in your timezone, your clock showed {meeting_start_your.strftime('%H:%M')}. "
            f"The meeting actually lasted {format_timedelta(actual_duration)}, but due to timezone confusion, you calculated it lasted {format_timedelta(wrong_duration)}. "
            f"What time did it end in {your_location}? "
            f"GIVE RESPONSE IN YYYY-MM-DD HH:MM:SS format. " 
            f"Think step by step. NO EXPLANATIONS."
        ),
        "target_scores": {
            f"{meeting_end_your.strftime('%Y-%m-%d %H:%M:%S')}": 1.0,     # CORRECT
            f"{wrong_end_your.strftime('%Y-%m-%d %H:%M:%S')}": 0.0        # WRONG (guaranteed ≠ correct)
        }
    }
    prompts.append(template2)
    prompt_counter += 1

# --- Save JSON file ---
with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
    json.dump(prompts, f, ensure_ascii=False, indent=2)

print(f"Generated {len(prompts)} prompts and saved to {PROMPTS_FILE}")