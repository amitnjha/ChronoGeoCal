import datetime
import json
import pandas as pd
from pyluach import dates
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from global_config import MAX_COUNT,PLACES_FILE

# ---------------- CONFIG ----------------
DURATION_HOURS = 6
OUTPUT_FILE = "prompt4_gen_data_dst_end.json"

# BiDi control characters for proper JSON rendering
LTR_EMBED_START = "\u202a"   # LRE
POP_DIRECTIONAL = "\u202c"   # PDF
LRM = "\u200e"               # LRM

# ---------------- LOAD PLACES ----------------
df_places_all = pd.read_json(PLACES_FILE)

# ---------------- HELPERS ----------------
def fmt_hm(dt: datetime.datetime) -> str:
    return dt.strftime("%H:%M")

def clean_hebrew_for_json(hebrew_str: str) -> str:
    return f"{hebrew_str}{LRM}"

# ---------------- GENERATION ----------------
prompts = []
prompt_counter = 0
duration_delta = datetime.timedelta(hours=DURATION_HOURS)

print(f"--- GENERATING UP TO {MAX_COUNT} SAMPLES ---\n")

# Filter places that actually observe DST
df_places_dst = df_places_all[df_places_all["dst"] != False]

for _, place1 in df_places_dst.iterrows():
    if prompt_counter >= MAX_COUNT:
        break

    location1 = place1["place"]
    tz1_str = place1["tz"]
    dst_info = place1["dst"]

    end_date_str = dst_info.get("end")
    trans_time_str = dst_info.get("transition_time", "02:00")

    try:
        ymd = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        h, m = map(int, trans_time_str.split(":"))
    except Exception:
        continue

    # Hebrew date of DST end
    g_date = dates.GregorianDate(ymd.year, ymd.month, ymd.day)
    heb_end_str = clean_hebrew_for_json(g_date.to_heb().hebrew_date_string())

    for _, place2 in df_places_all.iterrows():
        if prompt_counter >= MAX_COUNT:
            break

        if place1["place"] == place2["place"]:
            continue

        location2 = place2["place"]

        try:
            # Departure at ambiguous DST fall-back time (first occurrence)
            naive_dep = datetime.datetime(ymd.year, ymd.month, ymd.day, h, m)
            tz1 = ZoneInfo(tz1_str)
            dep_dt = naive_dep.replace(tzinfo=tz1, fold=0)

            # Arrival absolute time
            arrival_utc = dep_dt + duration_delta
            tz2 = ZoneInfo(place2["tz"])
            arrival_local = arrival_utc.astimezone(tz2)

            # Arrival Hebrew date
            arr_ymd = arrival_local.date()
            arr_greg = dates.GregorianDate(arr_ymd.year, arr_ymd.month, arr_ymd.day)
            arr_heb_str = clean_hebrew_for_json(arr_greg.to_heb().hebrew_date_string())

            correct_answer = f"{arr_heb_str}, {fmt_hm(arrival_local)}"

            wrong_dt = arrival_local + datetime.timedelta(hours=1)
            wrong_answer = f"{arr_heb_str}, {fmt_hm(wrong_dt)}"

            prompt = {
                "input": (
                    f"{LTR_EMBED_START}"
                    f"On {heb_end_str} in {location1}, daylight saving time ends and clocks fall back one hour. "
                    f"A flight departs at this exact time. "
                    f"If the flight duration is {DURATION_HOURS} hours to {location2}, "
                    f"what time does it arrive in both local time and Hebrew calendar date at the destination?Think step by step. NO EXPLANATIONS."
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
            print(f"Error processing {location1} → {location2}: {e}")
            continue

# ---------------- SAVE OUTPUT ----------------
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]
OUTPUT_FILE = "prompt4_gen_data_dst_end_" + PLACES + ".json"

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(prompts, f, ensure_ascii=False, indent=2, sort_keys=False)

print(f"Generated {len(prompts)} prompts and saved to {OUTPUT_FILE}")

if prompts:
    print("\nExample prompt (first):")
    print(json.dumps(prompts[0], ensure_ascii=False, indent=2, sort_keys=False))
