import datetime
import json
import pandas as pd
from pyluach import dates
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from global_config import MAX_COUNT,PLACES_FILE

# ---------------- CONFIG ----------------
EVENT_A_START_STR = "10:01"
DURATION_HOURS = 4
BUFFER_HOURS = 1
INPUT_PLACES_FILE = PLACES_FILE
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]
OUTPUT_FILE = "prompt6_gen_data_"+PLACES+".json"

# BiDi control characters for proper JSON rendering
LTR_EMBED_START = "\u202a"   # LRE - Left-to-Right Embedding
POP_DIRECTIONAL = "\u202c"   # PDF - Pop Directional Formatting
LRM = "\u200e"               # LRM - Left-to-Right Mark

# ---------------- LOAD PLACES ----------------
df_places = pd.read_json(PLACES_FILE)

# ---------------- HELPERS ----------------
def fmt_hm(dt: datetime.datetime) -> str:
    """Format time as HH:MM."""
    return dt.strftime("%H:%M")

def clean_hebrew_for_json(hebrew_str: str) -> str:
    """Ensure Hebrew renders correctly in JSON viewers."""
    return f"{hebrew_str}{LRM}"

# ---------------- GENERATION ----------------
prompts = []
prompt_counter = 0

print(f"--- GENERATING UP TO {MAX_COUNT} SAMPLES ---\n")

for _, place1 in df_places.iterrows():
    if prompt_counter >= MAX_COUNT:
        break

    for _, place2 in df_places.iterrows():
        if prompt_counter >= MAX_COUNT:
            break

        if place1['place'] == place2['place']:
            continue

        for h_month in [1, 7]:
            if prompt_counter >= MAX_COUNT:
                break

            try:
                # 1. Base Hebrew date → Gregorian
                hebrew_date_in = dates.HebrewDate(5785, h_month, 15)
                greg_date = hebrew_date_in.to_greg()

                # Clean Hebrew strings for JSON rendering
                input_hebrew = clean_hebrew_for_json(hebrew_date_in.hebrew_date_string())

                # 2. Event A start in Place 1 timezone
                start_h, start_m = map(int, EVENT_A_START_STR.split(':'))
                naive_start = datetime.datetime(
                    greg_date.year, greg_date.month, greg_date.day, 
                    start_h, start_m
                )
                tz1 = ZoneInfo(place1['tz'])
                dt_start_p1 = naive_start.replace(tzinfo=tz1)

                # 3. Event B absolute time (after duration + buffer)
                total_offset = datetime.timedelta(hours=DURATION_HOURS + BUFFER_HOURS)
                dt_event_b_absolute = dt_start_p1 + total_offset

                # 4. Convert to Place 2 local time
                tz2 = ZoneInfo(place2['tz'])
                dt_event_b_p2 = dt_event_b_absolute.astimezone(tz2)

                # 5. Hebrew date for Event B
                res_ymd = dt_event_b_p2.date()
                res_greg = dates.GregorianDate(res_ymd.year, res_ymd.month, res_ymd.day)
                res_heb_str = clean_hebrew_for_json(res_greg.to_heb().hebrew_date_string())

                # Answer strings - WRONG ANSWER FIRST (0.0), CORRECT SECOND (1.0)
                wrong_answer = f"{input_hebrew}, {fmt_hm(naive_start + total_offset)}"
                correct_answer = f"{res_heb_str}, {fmt_hm(dt_event_b_p2)}"

                # **REVERSED ORDER**: Wrong (0.0) first, then correct (1.0)
                prompt = {
                    "input": (
                        f"{LTR_EMBED_START}"
                        f"In the Hebrew calendar, the date is {input_hebrew}. "
                        f"Event A in {place1['place']} happens at {EVENT_A_START_STR} and lasts {DURATION_HOURS} hours. "
                        f"Event B in {place2['place']} must start at least {BUFFER_HOURS} hour after Event A ends. "
                        f"What is the earliest possible start time for Event B in {place2['place']} local time in Hebrew Calendar?Think step by step. NO EXPLANATIONS."
                        f"{POP_DIRECTIONAL}"
                    ),
                    "target_scores": {
                        wrong_answer: 0.0,
                        correct_answer: 1.0
                    }
                }

                prompts.append(prompt)
                prompt_counter += 1

            except ZoneInfoNotFoundError:
                continue
            except Exception as e:
                print(f"Error processing {place1['place']} → {place2['place']}: {e}")
                continue

# ---------------- SAVE OUTPUT ----------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(prompts, f, ensure_ascii=False, indent=2, sort_keys=False)

print(f"Generated {len(prompts)} prompts and saved to {OUTPUT_FILE}")

if prompts:
    print("\nExample prompt (first):")
    print(json.dumps(prompts[0], ensure_ascii=False, indent=2, sort_keys=False))
