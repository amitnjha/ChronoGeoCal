import os
import json
import datetime
from typing import List, Dict

import pandas as pd
import pytz
from pytz.exceptions import AmbiguousTimeError, NonExistentTimeError

try:
    from pyluach import dates
except Exception as e:
    raise ImportError("pyluach is required: pip install pyluach") from e

# Try to import MAX_COUNT from your global_config; otherwise use a safe default
from global_config import MAX_COUNT,PLACES_FILE

# -------------------------
# Safe loader for PLACES_FILE (Option 1)
# -------------------------
FILE = PLACES_FILE
if os.path.exists(FILE):
    df_places = pd.read_json(FILE)
else:
    print(f"[WARN] {FILE} not found – using mock data")
    mock_data = {
        "place": ["New York", "London", "Jerusalem", "Tokyo"],
        "tz": ["America/New_York", "Europe/London", "Asia/Jerusalem", "Asia/Tokyo"],
    }
    df_places = pd.DataFrame(mock_data)

df_places = df_places.reset_index(drop=True)
place_list = df_places[["place", "tz"]]

# -------------------------
# Helpers
# -------------------------
def safe_localize(tz: pytz.BaseTzInfo, naive_dt: datetime.datetime) -> datetime.datetime:
    """
    Localize a naive datetime into a pytz timezone with handling for ambiguous/nonexistent times.
    - For AmbiguousTimeError (fall-back DST), choose is_dst=True (the earlier/later choice can be adjusted).
    - For NonExistentTimeError (spring-forward), advance 1 hour and try again.
    Returns an aware datetime.
    """
    try:
        return tz.localize(naive_dt)
    except AmbiguousTimeError:
        # choose is_dst=True (you can change to False if you prefer the other fold)
        return tz.localize(naive_dt, is_dst=True)
    except NonExistentTimeError:
        # push forward 1 hour to the next valid wall time
        shifted = naive_dt + datetime.timedelta(hours=1)
        try:
            return tz.localize(shifted)
        except Exception:
            # fallback: attach tzinfo without conversion (less ideal but robust)
            return shifted.replace(tzinfo=tz)

def fmt_iso(dt: datetime.datetime) -> str:
    """Format an aware datetime to 'YYYY-MM-DD HH:MM:SS' (in its local timezone)."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# -------------------------
# Generation loop
# -------------------------
prompts: List[Dict] = []
prompt_counter = 0

print(f"--- GENERATING UP TO {MAX_COUNT} SAMPLES ---\n")

# We'll iterate triples of places and two Hebrew months for variety (as in your original script)
HEBREW_MONTHS = [1, 7]  # Nisan, Tishrei

for idx1, place1 in place_list.iterrows():
    if prompt_counter >= MAX_COUNT:
        break
    for idx2, place2 in place_list.iterrows():
        if prompt_counter >= MAX_COUNT:
            break
        for idx3, place3 in place_list.iterrows():
            if prompt_counter >= MAX_COUNT:
                break

            # Ensure distinct/interesting triples
            if place1["place"] == place2["place"] or place2["place"] == place3["place"]:
                continue

            for h_month in HEBREW_MONTHS:
                if prompt_counter >= MAX_COUNT:
                    break

                try:
                    # 1) Build Hebrew date and convert to Gregorian
                    hebrew_date = dates.HebrewDate(5785, h_month, 15)
                    greg = hebrew_date.to_greg()  # object with .year .month .day

                    base_date = datetime.date(greg.year, greg.month, greg.day)

                    # 2) Event A: 02:00 - 06:00 in place1 tz
                    tz1 = pytz.timezone(place1["tz"])
                    a_start_naive = datetime.datetime.combine(base_date, datetime.time(2, 0))
                    a_end_naive   = datetime.datetime.combine(base_date, datetime.time(6, 0))

                    dt_a_start = safe_localize(tz1, a_start_naive)
                    dt_a_end   = safe_localize(tz1, a_end_naive)

                    # 3) Event B: 06:00 - 09:00 in place2 tz
                    tz2 = pytz.timezone(place2["tz"])
                    b_start_naive = datetime.datetime.combine(base_date, datetime.time(6, 0))
                    b_end_naive   = datetime.datetime.combine(base_date, datetime.time(9, 0))

                    dt_b_start = safe_localize(tz2, b_start_naive)
                    dt_b_end   = safe_localize(tz2, b_end_naive)

                    # 4) Convert all to place3 timezone (target)
                    tz3 = pytz.timezone(place3["tz"])

                    a_start_tz3 = dt_a_start.astimezone(tz3)
                    a_end_tz3   = dt_a_end.astimezone(tz3)
                    b_start_tz3 = dt_b_start.astimezone(tz3)
                    b_end_tz3   = dt_b_end.astimezone(tz3)

                    # 5) Compute overlap in TZ3
                    overlap_start = max(a_start_tz3, b_start_tz3)
                    overlap_end   = min(a_end_tz3, b_end_tz3)

                    # 6) Build correct & distractor answers — now using ISO datetimes YYYY-MM-DD HH:MM:SS
                    if overlap_start < overlap_end:
                        # Convert overlap start/end to full ISO datetimes in place3 local time
                        correct_iso_start = fmt_iso(overlap_start)
                        correct_iso_end   = fmt_iso(overlap_end)

                        # Build a textual answer using ISO datetimes (you can change formatting if desired)
                        correct_answer = f"{correct_iso_start} - {correct_iso_end}"

                        # Distractor: shift both by +2 hours (naive distractor)
                        distractor_start = overlap_start + datetime.timedelta(hours=2)
                        distractor_end   = overlap_end   + datetime.timedelta(hours=2)
                        distractor_answer = f"{fmt_iso(distractor_start)} - {fmt_iso(distractor_end)}"
                    else:
                        correct_answer = "No overlap"
                        # distractor: claim an overlap starting at A start in TZ3 (ISO)
                        distractor_answer = f"Overlap occurs at {fmt_iso(a_start_tz3)}"

                    # 7) Build input (keeps original instruction phrasing)
                    input_text = (
                        f"In the Hebrew calendar, today is {hebrew_date.hebrew_date_string()}. "
                        f"Event A occurs from 2:00 AM to 6:00 AM in {place1['place']}. "
                        f"Event B occurs from 6:00 AM to 9:00 AM in {place2['place']}. "
                        f"During what time period do these events overlap when both are converted to {place3['place']} time? "
                        f"Convert the final answer in the Hebrew calendar date and {place3['place']} local time. "
                        "PLEASE ONLY PROVIDE THE ANSWER. Think step by step. NO EXPLANATIONS."
                    )

                    # 8) Append prompt (structured dict) — target_scores keys are strings
                    entry = {
                        "input": input_text,
                        "target_scores": {
                            correct_answer: 1.0,
                            distractor_answer: 0.0
                        }
                    }

                    prompts.append(entry)
                    prompt_counter += 1

                except Exception:
                    # Skip problematic triples/dates/timezones robustly
                    continue

# -------------------------
# Save JSON output
# -------------------------
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]
OUT = "prompt3_gen_data_hebrew_" + PLACES + ".json"
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(prompts, f, ensure_ascii=False, indent=2)

print(f"\nGenerated {len(prompts)} prompts -> {OUT}")
if prompts:
    print("\nExample (first entry):")
    print(json.dumps(prompts[0], ensure_ascii=False, indent=2))
