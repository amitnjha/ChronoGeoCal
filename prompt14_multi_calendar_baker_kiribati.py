from __future__ import annotations
import os
import json
import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import List, Dict, Tuple, Any
from global_config import MAX_COUNT,PLACES_FILE


# -------------------------
# Config
# -------------------------
IN_FILE = PLACES_FILE
INPUT_PLACES_FILE = PLACES_FILE
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]
try:
    import pandas as pd
except ImportError as e:
    raise ImportError(
        "pandas is required for this script but not available. "
        "Install it with `pip install pandas` and rerun. "
        f"(original error: {e})"
    )

# -------------------------
# Config
# -------------------------
IN_PLACES = PLACES_FILE
OUT_FILE = "prompt14_multi_calendar_baker_kiribati_"+PLACES+".json"
MAX_COUNT = 10  # adjust as needed

BAKER_TZNAME = "Pacific/Baker"          # may not exist on many systems
KIRITIMATI_TZNAME = "Pacific/Kiritimati"  # UTC+14

EVENT_TIMES_BAKER = [
    datetime.datetime(2025, 12, 31, 10, 0),
    datetime.datetime(2025, 1, 1, 1, 30),
]

# -------------------------
# Timezone helpers
# -------------------------
def get_baker_timezone():
    try:
        return ZoneInfo(BAKER_TZNAME)
    except ZoneInfoNotFoundError:
        return datetime.timezone(datetime.timedelta(hours=-12), name="UTC-12")

# -------------------------
# Calendar helpers
# -------------------------
def fmt_gregorian(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M %z")

def fmt_iso_week(dt: datetime.datetime) -> str:
    iy, iw, iday = dt.isocalendar()
    return f"{iy}-W{iw:02d}-{iday} {dt.strftime('%H:%M %z')}"

def jdn_from_gregorian(y: int, m: int, d: int) -> int:
    a = (14 - m) // 12
    y2 = y + 4800 - a
    m2 = m + 12 * a - 3
    return (
        d
        + (153 * m2 + 2) // 5
        + 365 * y2
        + y2 // 4
        - y2 // 100
        + y2 // 400
        - 32045
    )

def jdn_to_julian_date(jdn: int) -> Tuple[int, int, int]:
    c = jdn + 32082
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = d - 4800 + (m // 10)
    return year, month, day

def julian_calendar_string(dt: datetime.datetime) -> str:
    dt_utc = dt.astimezone(datetime.timezone.utc)
    jdn = jdn_from_gregorian(dt_utc.year, dt_utc.month, dt_utc.day)
    y, m, d = jdn_to_julian_date(jdn)
    return f"{y:04d}-{m:02d}-{d:02d} {dt.strftime('%H:%M %z')} (Julian)"

def julian_date_jd(dt: datetime.datetime) -> float:
    dt_utc = dt.astimezone(datetime.timezone.utc)
    jdn = jdn_from_gregorian(dt_utc.year, dt_utc.month, dt_utc.day)
    frac = (dt_utc.hour - 12)/24 + dt_utc.minute/1440 + dt_utc.second/86400
    return round(jdn + frac, 6)

def to_utc_iso(dt: datetime.datetime) -> str:
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def make_calendar_fields(dt: datetime.datetime) -> Dict[str, Any]:
    return {
        "gregorian": fmt_gregorian(dt),
        "iso_week": fmt_iso_week(dt),
        "julian": julian_calendar_string(dt),
        "jd": julian_date_jd(dt),
        "utc": to_utc_iso(dt),
    }

# -------------------------
# Places loader with fallback
# -------------------------
def load_places_df(path: str) -> pd.DataFrame:
    if os.path.exists(path):
        try:
            return pd.read_json(path)
        except Exception:
            print(f"[WARN] Could not read {path}, using fallback places")
    print("[INFO] Using fallback example places")
    return pd.DataFrame([
        {"place": "London", "tz": "Europe/London"},
        {"place": "New York", "tz": "America/New_York"},
        {"place": "Tokyo", "tz": "Asia/Tokyo"},
    ])

# -------------------------
# Prompt generation for all places
# -------------------------
def generate_prompts_from_df(df_places: pd.DataFrame, max_count: int):
    baker_tz = get_baker_timezone()
    kiri_tz = ZoneInfo(KIRITIMATI_TZNAME)

    entries = []

    for _, row in df_places.iterrows():
        place_name = row["place"]
        tz_name = row["tz"]

        try:
            place_tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            print(f"[WARN] Timezone {tz_name} not found. Skipping {place_name}.")
            continue

        for naive_dt in EVENT_TIMES_BAKER:
            if len(entries) >= max_count:
                break

            baker_dt = naive_dt.replace(tzinfo=baker_tz)
            place_dt = baker_dt.astimezone(place_tz)

            baker_fields = make_calendar_fields(baker_dt)
            place_fields = make_calendar_fields(place_dt)

            #correct_text = f"Correct {place_name} time is {place_fields['gregorian']}."
            correct_text = f"{place_fields['gregorian']}"
            wrong_dt = (baker_dt + datetime.timedelta(hours=24)).astimezone(place_tz)
            wrong_fields = make_calendar_fields(wrong_dt)
            wrong_text = f"Wrong {place_name} time is {wrong_fields['gregorian']}."

            entry = {
                "input": (
                    f"When it is {baker_dt.strftime('%H:%M')} on "
                    f"{baker_dt.strftime('%Y-%m-%d')} in Baker Island, "
                    f"what date and time is it in {place_name}? "
                    "List all four calendar dates and times.Think step by step. NO EXPLANATION."
                ),
                "answers": {
                    "correct": {
                        "baker": baker_fields,
                        place_name.lower(): place_fields,
                    },
                    "distractor": {
                        "baker": baker_fields,
                        place_name.lower(): wrong_fields,
                    },
                },
                "target_scores": {
                    correct_text: 1.0,
                    wrong_text: 0.0,
                },
            }

            entries.append(entry)

    return entries

# -------------------------
# Main function
# -------------------------
def main():
    df_places = load_places_df(IN_PLACES)
    prompts = generate_prompts_from_df(df_places, MAX_COUNT)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Generated {len(prompts)} prompts → {OUT_FILE}")

    # Print up to 3 sample prompts
    sample_count = min(3, len(prompts))
    for i in range(sample_count):
        print(f"\n--- Sample Prompt {i+1} ---")
        print(json.dumps(prompts[i], indent=2, ensure_ascii=False))

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    main()
