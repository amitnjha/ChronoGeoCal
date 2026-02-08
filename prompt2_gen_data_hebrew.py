from pyluach import dates
import pandas as pd
import datetime
import pytz
import json
import re
from global_config import MAX_COUNT,PLACES_FILE

# ---------------- CONFIG ----------------
HEBREW_YEAR = 5762
HEBREW_DAY = 1
TIMES_TO_TEST = [(10, 1), (2, 1)]

INPUT_PLACES_FILE = PLACES_FILE
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]

OUTPUT_FILE = "prompt2_gen_data_hebrew_" + PLACES + ".json"

# ---------------- BiDi cleanup ----------------
# Keep \u200e (LRM) to help JSON viewers render correctly.
# Only strip classic embedding/override controls that cause major artifacts.
BIDI_CHARS = re.compile(r'[\u200f\u202a-\u202e]')  # NOTE: \u200e REMOVED

def clean_rtl(text: str) -> str:
    """Remove problematic BiDi control characters and trim surrounding whitespace."""
    if not isinstance(text, str):
        return text
    return BIDI_CHARS.sub('', text).strip()

# ---------------- LOAD PLACES ----------------
df_places = pd.read_json(INPUT_PLACES_FILE)
df_places = df_places[['place', 'tz']]  # ensure correct columns
places = df_places.to_dict("records")

# ---------------- HELPERS ----------------
def fmt_ymdhms(dt: datetime.datetime) -> str:
    """Format timezone-aware datetime as 'YYYY-MM-DD HH:MM:SS'."""
    if dt.strftime("%Y-%m-%d %H:%M:%S") is None:
        print("Warning: datetime formatting returned None")
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# ---------------- GENERATION ----------------
prompts = []
prompt_counter = 0

# Base LTR wrappers to make most viewers treat the whole string as LTR
LTR_EMBED_START = "\u202a"   # LRE
POP_DIRECTIONAL = "\u202c"   # PDF
LRM = "\u200e"               # Left-to-right mark

for p1 in places:
    for p2 in places:
        if p1["place"] == p2["place"]:
            continue

        if prompt_counter >= MAX_COUNT:
            break

        try:
            tz1 = pytz.timezone(p1["tz"])
            tz2 = pytz.timezone(p2["tz"])
        except Exception as e:
            print(f"Skipping pair ({p1.get('place')}, {p2.get('place')}) due to invalid timezone: {e}")
            continue

        # Hebrew months (1..13; month 13 only in leap years)
        for month in range(1, 14):
            if prompt_counter >= MAX_COUNT:
                break

            try:
                hdate = dates.HebrewDate(HEBREW_YEAR, month, HEBREW_DAY)
            except Exception:
                # invalid month for this Hebrew year (e.g., month 13 in non-leap year)
                continue

            gdate = hdate.to_greg()

            # Clean the Hebrew date string but keep \u200e to stabilize punctuation
            raw_hebrew = hdate.hebrew_date_string()
            hebrew_text = clean_rtl(raw_hebrew)

            for hour, minute in TIMES_TO_TEST:
                if prompt_counter >= MAX_COUNT:
                    break

                naive_dt = datetime.datetime(
                    gdate.year, gdate.month, gdate.day, hour, minute, 0
                )

                # Localize in place1 tz and compute place2 equivalent
                dt_place1 = tz1.localize(naive_dt)
                dt_place2 = dt_place1.astimezone(tz2)
                # Wrap whole prompt in explicit LTR embedding, and
                # insert an LRM immediately after the Hebrew block.
                input_text = (
                    f"{LTR_EMBED_START}"  # Force LTR paragraph for the JSON viewer
                    f"Assume Today is {hebrew_text}{LRM}. "
                    f"It is currently {hour:02d}:{minute:02d} in {p1['place']}. "
                    f"What time and date is it in {p2['place']} in Gregorian Calendar? "
                    f"GIVE RESPONSE IN YYYY-MM-DD HH:MM:SS format.Think step by step. NO EXPLANATION."
                    f"{POP_DIRECTIONAL}"
                )

                prompt = {
                    "input": input_text,
                    "target_scores": {
                        fmt_ymdhms(dt_place2): 1.0,
                        fmt_ymdhms(dt_place1): 0.0
                    }
                }
                if len(prompt.get("target_scores")) == 1:
                    #print("Warning: prompt target_scores is badly formed: skipping", dt_place2, dt_place1)
                    continue
                prompts.append(prompt)
                prompt_counter += 1

# ---------------- SAVE OUTPUT ----------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(prompts, f, ensure_ascii=False, indent=2)

# ---------------- SUMMARY ----------------
print(f"Generated {len(prompts)} prompts (MAX_COUNT={MAX_COUNT})")
print(f"Saved to {OUTPUT_FILE}")

if prompts:
    print("\nExample prompt (first):")
    print(json.dumps(prompts[0], ensure_ascii=False, indent=2))
