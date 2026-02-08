import datetime
import json
import random
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import pandas as pd
from global_config import MAX_COUNT,PLACES_FILE

# --- Files / Constants ---
PLACES_FILE = PLACES_FILE
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]
OUTPUT_FILE = "prompt8_chatham_dst_"+PLACES+".json"

# Chatham DST transition facts
DST_DATE_STR = "September 28, 2025"
TRANSITION_LOCAL_START_HOUR = 3
TRANSITION_LOCAL_START_MIN = 45
LOC1_NAME = "Chatham Islands"
LOC1_TZ = "Pacific/Chatham"

# Load places data
try:
    df_places = pd.read_json(PLACES_FILE)
except Exception as exc:
    raise SystemExit(f"Failed to read {PLACES_FILE}: {exc}")

# Validate required columns
required_cols = {"place", "tz"}
if not required_cols.issubset(set(df_places.columns)):
    raise SystemExit(f"{PLACES_FILE} must contain columns: {required_cols}")

df_places = df_places.loc[:, ['place', 'tz']].reset_index(drop=True)

prompts = []
prompt_counter = 0

print(f"--- GENERATING up to {MAX_COUNT} PROMPTS ---")

# Variable duration options
DURATION_OPTIONS = [
    (30, "30 minutes"),
    (45, "45 minutes"), 
    (60, "1 hour"),
    (75, "1 hour and 15 minutes"),
    (90, "1 hour and 30 minutes"),
    (105, "1 hour and 45 minutes"),
    (120, "2 hours")
]

def minutes_to_delta(minutes: int) -> datetime.timedelta:
    """Convert minutes to timedelta."""
    hours = minutes // 60
    mins = minutes % 60
    return datetime.timedelta(hours=hours, minutes=mins)

# Use each row as loc2
for r in df_places.itertuples(index=False):
    if prompt_counter >= MAX_COUNT:
        break

    loc2_name, loc2_tz = r.place, r.tz

    try:
        # Construct Chatham start: 2025-09-28 03:45 local (post-DST jump)
        t1_start_chatham = datetime.datetime(
            2025, 9, 28, TRANSITION_LOCAL_START_HOUR, TRANSITION_LOCAL_START_MIN,
            tzinfo=ZoneInfo(LOC1_TZ)
        )
        
        # Pick random duration for this prompt
        total_minutes, dur_str = random.choice(DURATION_OPTIONS)
        dur_delta = minutes_to_delta(total_minutes)

        t1_end_chatham = t1_start_chatham + dur_delta

        # Helper function
        def fmt_for_tz(dt_chatham: datetime.datetime, tz_str: str) -> str:
            tz = ZoneInfo(tz_str)
            return dt_chatham.astimezone(tz).strftime("%H:%M")

        # Correct times
        ch1_s = t1_start_chatham.strftime("%H:%M")
        ch1_e = t1_end_chatham.strftime("%H:%M")
        l2_m1_s = fmt_for_tz(t1_start_chatham, loc2_tz)
        l2_m1_e = fmt_for_tz(t1_end_chatham, loc2_tz)

        # Correct answer (single line with comma + score)
        correct_answer = (
            f"Chatham Islands: {ch1_s}–{ch1_e}, "
            f"{loc2_name}: {l2_m1_s}–{l2_m1_e} : 1.0"
        )

        # Distractor (ignores DST jump - starts at 02:45 naive)
        naive_start = datetime.datetime(2025, 9, 28, 2, 45)
        naive_end = naive_start + dur_delta
        
        distractor_answer = (
            f"Chatham Islands: {naive_start.strftime('%H:%M')}–{naive_end.strftime('%H:%M')}, "
            f"{loc2_name}: {l2_m1_s}–{l2_m1_e} : 0.0"
        )

        # Prompt with variable duration
        prompt_text = (
            f"On {DST_DATE_STR}, daylight saving time (DST) begins in the {LOC1_NAME}. "
            f"At the DST transition, the local clocks move forward from 02:45 to 03:45. "
            f"A video meeting starts exactly at the moment the DST change takes effect "
            f"(that is, at 03:45 local time in the {LOC1_NAME}) and lasts for {dur_str}. "
            f"The meeting involves participants in two locations: "
            f"{LOC1_NAME} "
            f"{loc2_name} "
            f"Determine the local start and end times in both locations. "
            f"Assume all listed locations correctly observe DST according to their local time zones. "
            f"Report your answer in the following format (single line with score): "
            f"Chatham Islands: HH:MM – HH:MM, {loc2_name}: HH:MM – HH:MM : X.X. Think step by step. NO EXPLANATIONS."
        )

        template = {
            "input": prompt_text,
            "meta": {
                "loc1": LOC1_NAME,
                "loc1_tz": LOC1_TZ,
                "loc2": loc2_name,
                "loc2_tz": loc2_tz,
                "dst_date": DST_DATE_STR,
                "transition": "02:45 -> 03:45 (local)",
                "duration_minutes": total_minutes,
                "duration_str": dur_str
            },
            "target_scores": {
                correct_answer: 1.0,
                distractor_answer: 0.0
            }
        }

        prompts.append(template)
        prompt_counter += 1

    except ZoneInfoNotFoundError:
        print(f"Skipping {loc2_name} — unknown timezone: {loc2_tz}")
    except Exception as e:
        print(f"Error for {loc2_name}: {e}")

# Save to JSON
try:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(prompts)} prompts to {OUTPUT_FILE}")
except Exception as e:
    raise SystemExit(f"Failed to write output file {OUTPUT_FILE}: {e}")