import os
import json
import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import List, Dict

import pandas as pd
from global_config import MAX_COUNT,PLACES_FILE


# -------------------------
# Config
# -------------------------
IN_FILE = PLACES_FILE
INPUT_PLACES_FILE = PLACES_FILE
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]
OUT_FILE = "prompt13_marquesas_time_difference_gen_"+PLACES+".json"
MARQUESAS_TZNAME = "Pacific/Marquesas"  # IANA tz for Marquesas Islands (UTC-09:30)

# Example event times (naive datetimes; will be attached to Marquesas tz)
EVENT_TIMES_MARQUESAS = [
    datetime.datetime(2025, 12, 5, 12, 0),   # 12:00 local Marquesas
    datetime.datetime(2025, 12, 6, 8, 30),   # 08:30 local Marquesas
]

# How we model a plausible "wrong" calculation (common mistake):
WRONG_CALC_STRATEGY = "round_to_nearest_hour"

# -------------------------
# Helpers
# -------------------------
def fmt_iso_with_offset(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M %z")

def diff_to_hhmm(seconds: float) -> str:
    sign = "+" if seconds >= 0 else "-"
    total_seconds = abs(int(round(seconds)))
    mins_total = total_seconds // 60
    hrs = mins_total // 60
    mins = mins_total % 60
    return f"{sign}{int(hrs):02d}:{int(mins):02d}"

def load_places_dataframe(path: str) -> pd.DataFrame:
    df = None
    if os.path.exists(path):
        try:
            df = pd.read_json(path, orient="records")
        except Exception:
            try:
                df = pd.read_json(path)
            except Exception as e:
                print(f"[WARN] Failed to read {path} ({e}) — using mock data")
                df = None
    if df is None:
        mock_data = [
            {"place": "London", "tz": "Europe/London", "dst": {"start": "2025-03-30", "transition_time": "01:00"}},
            {"place": "New York", "tz": "America/New_York", "dst": {"start": "2025-03-09", "transition_time": "02:00"}},
            {"place": "Tokyo", "tz": "Asia/Tokyo", "dst": False},
            {"place": "Sydney", "tz": "Australia/Sydney", "dst": {"start": "2025-10-05", "transition_time": "02:00"}}]
        df = pd.DataFrame(mock_data)
        print("[INFO] Using mock places data")
    for col in ("place", "tz"):
        if col not in df.columns:
            raise ValueError(f"Input places data must contain column '{col}'")
    df = df.reset_index(drop=True)
    return df

def _marquesas_zoneinfo_fallback() -> datetime.tzinfo:
    try:
        return ZoneInfo(MARQUESAS_TZNAME)
    except ZoneInfoNotFoundError:
        # Marquesas is UTC-9:30 (no DST)
        return datetime.timezone(datetime.timedelta(hours=-9, minutes=-30), name="UTC-09:30")

# -------------------------
# Main generation
# -------------------------
def generate_prompts(df_places_all: pd.DataFrame, max_count: int) -> List[Dict]:
    if not (df_places_all["tz"] == MARQUESAS_TZNAME).any():
        marq_row = {"place": "Marquesas Islands", "tz": MARQUESAS_TZNAME, "dst": False}
        df_places_all = pd.concat([df_places_all, pd.DataFrame([marq_row])], ignore_index=True)
        df_places_all = df_places_all.reset_index(drop=True)
        print("[INFO] Added Marquesas Islands to places list")

    prompts: List[Dict] = []
    prompt_counter = 0
    ref_rows = [row for _, row in df_places_all.iterrows() if row["tz"] != MARQUESAS_TZNAME]
    marq_tz = _marquesas_zoneinfo_fallback()

    for event_naive in EVENT_TIMES_MARQUESAS:
        if prompt_counter >= max_count:
            break
        event_dt_marq = event_naive.replace(tzinfo=marq_tz)

        for rec in ref_rows:
            if prompt_counter >= max_count:
                break
            ref_place = rec["place"]
            ref_tz_name = rec["tz"]

            try:
                ref_tz = ZoneInfo(ref_tz_name)
            except ZoneInfoNotFoundError:
                print(f"[WARN] Reference timezone not found: {ref_tz_name} (skipping {ref_place})")
                continue

            try:
                actual_ref_dt = event_dt_marq.astimezone(ref_tz)
                actual_diff_seconds = (
                    event_dt_marq.astimezone(datetime.timezone.utc) -
                    actual_ref_dt.astimezone(datetime.timezone.utc)
                ).total_seconds()
                actual_diff_hours = actual_diff_seconds / 3600.0

                actual_diff_str = diff_to_hhmm(actual_diff_seconds)
                actual_reference_time_str = fmt_iso_with_offset(actual_ref_dt)
                #correct_label = f"difference={actual_diff_str}; reference_time={actual_reference_time_str}"
                correct_label = f"{actual_reference_time_str}"

                # --- Create a distractor that is numerically different ---
                if abs(actual_diff_hours) < 1e-6:
                    # Correct difference is zero → force ±1 hour distractor
                    wrong_hours = 1
                else:
                    # usual rounding
                    wrong_hours = int(round(actual_diff_hours))
                    if wrong_hours == int(actual_diff_hours):
                        # Ensure distractor differs from correct
                        wrong_hours += 1 if wrong_hours > 0 else -1

                wrong_ref_dt = (event_dt_marq - datetime.timedelta(hours=wrong_hours)).astimezone(ref_tz)
                wrong_diff_seconds = wrong_hours * 3600
                wrong_diff_str = diff_to_hhmm(wrong_diff_seconds)
                wrong_reference_time_str = fmt_iso_with_offset(wrong_ref_dt)
                distractor_label = f"difference={wrong_diff_str}; reference_time={wrong_reference_time_str}"

                input_text = (
                    f"Someone says that The event starts at {fmt_iso_with_offset(event_dt_marq)} Marquesas Islands time, "
                    f"which is {abs(wrong_hours)} hour{'s' if abs(wrong_hours) != 1 else ''} "
                    f"after {fmt_iso_with_offset(wrong_ref_dt)} in {ref_place}. "
                    "However, their calculation is incorrect. "
                    f"What is the actual time difference, what time is it actually in {ref_place} when the event starts?Think step by step. NO EXPLANATION."
                )

                entry = {
                    "input": input_text,
                    "target_scores": {
                        correct_label: 1.0,
                        distractor_label: 0.0
                    }
                }

                prompts.append(entry)
                prompt_counter += 1

            except Exception as e:
                print(f"[WARN] Skipping pair Marquesas -> {ref_place} due to error: {e}")
                continue

    return prompts

# -------------------------
# Run generation and save
# -------------------------
def main():
    df = load_places_dataframe(IN_FILE)
    prompts = generate_prompts(df, MAX_COUNT)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Generated {len(prompts)} prompts -> {OUT_FILE}")
    if prompts:
        print("[INFO] Example (first entry):")
        print(json.dumps(prompts[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
