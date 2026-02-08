import os
import datetime
import json
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import List, Dict
from global_config import MAX_COUNT,PLACES_FILE
import pandas as pd

# -------------------------
# Safe loader (Option 1)
# -------------------------
#FILE = "places_DST.json"
FILE = PLACES_FILE

if os.path.exists(FILE):
    df_places_all = pd.read_json(FILE)
else:
    print(f"[WARN] {FILE} not found – using mock data")
    mock_data = [
        {"place": "London", "tz": "Europe/London", "dst": {"start": "2025-03-30", "transition_time": "01:00"}},
        {"place": "New York", "tz": "America/New_York", "dst": {"start": "2025-03-09", "transition_time": "02:00"}},
        {"place": "Tokyo", "tz": "Asia/Tokyo", "dst": False},
        {"place": "Sydney", "tz": "Australia/Sydney", "dst": {"start": "2025-10-05", "transition_time": "02:00"}}]
    df_places_all = pd.DataFrame(mock_data)

# Keep only rows that exist (defensive)
df_places_all = df_places_all.reset_index(drop=True)

# DST trigger locations (rows where 'dst' is not False)
df_places_dst = df_places_all[df_places_all["dst"] != False].reset_index(drop=True)

# Durations for meetings
dur_1_delta = datetime.timedelta(hours=2)
dur_2_delta = datetime.timedelta(hours=2)
dur_1_str = "2 hours"
dur_2_str = "2 hours"

# Helper utilities
def dst_jump_time(naive: datetime.datetime, tz_name: str, jump_hours: int = 1) -> datetime.datetime:
    """
    Apply a deterministic 'spring forward' jump: add jump_hours to naive time,
    then attach tzinfo using ZoneInfo. This matches the prompt-generation semantics.
    """
    tz = ZoneInfo(tz_name)  # may raise ZoneInfoNotFoundError
    jumped = naive + datetime.timedelta(hours=jump_hours)
    return jumped.replace(tzinfo=tz)

def fmt_iso(dt: datetime.datetime) -> str:
    """Format aware datetime to ISO-like string YYYY-MM-DD HH:MM:SS"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

prompts: List[Dict] = []
prompt_counter = 0

# -------------------------
# Generation loop
# -------------------------
for _, rec1 in df_places_dst.iterrows():
    if prompt_counter >= MAX_COUNT:
        break

    loc1 = rec1["place"]
    tz1_name = rec1["tz"]
    dst_info = rec1.get("dst", {}) or {}

    start_date = dst_info.get("start", None)
    trans_time = dst_info.get("transition_time", "02:00")

    # Validate date/time strings
    try:
        ymd = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        hm = datetime.datetime.strptime(trans_time, "%H:%M").time()
    except Exception:
        # skip invalid DST info
        continue

    naive_transition = datetime.datetime.combine(ymd, hm)

    # iterate over location2 and location3 (any places, including DST or non-DST)
    for _, rec2 in df_places_all.iterrows():
        if prompt_counter >= MAX_COUNT:
            break
        loc2 = rec2["place"]
        if loc2 == loc1:
            continue
        tz2_name = rec2["tz"]

        for _, rec3 in df_places_all.iterrows():
            if prompt_counter >= MAX_COUNT:
                break
            loc3 = rec3["place"]
            if loc3 in (loc1, loc2):
                continue
            tz3_name = rec3["tz"]

            try:
                # Correct answer: apply DST jump at location1 (spring-forward)
                m1_start = dst_jump_time(naive_transition, tz1_name, jump_hours=1)
                m1_end = m1_start + dur_1_delta
                m2_start = m1_end
                m2_end = m2_start + dur_2_delta

                # ZoneInfo objects for conversions
                tz1 = ZoneInfo(tz1_name)
                tz2 = ZoneInfo(tz2_name)
                tz3 = ZoneInfo(tz3_name)

                def times_for_zone(tz):
                    return (
                        fmt_iso(m1_start.astimezone(tz)),
                        fmt_iso(m1_end.astimezone(tz)),
                        fmt_iso(m2_start.astimezone(tz)),
                        fmt_iso(m2_end.astimezone(tz)),
                    )

                t1 = times_for_zone(tz1)
                t2 = times_for_zone(tz2)
                t3 = times_for_zone(tz3)

                # correct = (
                #     f"Meeting 1: {loc1} [{t1[0]}–{t1[1]}], "
                #     f"{loc2} [{t2[0]}–{t2[1]}], "
                #     f"{loc3} [{t3[0]}–{t3[1]}]. "
                #     f"Meeting 2: {loc1} [{t1[2]}–{t1[3]}], "
                #     f"{loc2} [{t2[2]}–{t2[3]}], "
                #     f"{loc3} [{t3[2]}–{t3[3]}]."
                # )
                correct = (
                    f"{t3[0]}–{t3[1]}"
                )

                # Distractor: forget the jump (use naive transition time attached to tz1)
                bad_start = naive_transition.replace(tzinfo=ZoneInfo(tz1_name))
                bad_end = bad_start + dur_1_delta
                bad_m2_start = bad_end
                bad_m2_end = bad_m2_start + dur_2_delta

                def bad_times_for_zone(tz):
                    return (
                        fmt_iso(bad_start.astimezone(tz)),
                        fmt_iso(bad_end.astimezone(tz)),
                        fmt_iso(bad_m2_start.astimezone(tz)),
                        fmt_iso(bad_m2_end.astimezone(tz)),
                    )

                bt1 = bad_times_for_zone(tz1)
                bt2 = bad_times_for_zone(tz2)
                bt3 = bad_times_for_zone(tz3)

                distractor = (
                    f"Meeting 1: {loc1} [{bt1[0]}–{bt1[1]}], "
                    f"{loc2} [{bt2[0]}–{bt2[1]}], "
                    f"{loc3} [{bt3[0]}–{bt3[1]}]. "
                    f"Meeting 2: {loc1} [{bt1[2]}–{bt1[3]}], "
                    f"{loc2} [{bt2[2]}–{bt2[3]}], "
                    f"{loc3} [{bt3[2]}–{bt3[3]}]."
                )

                # Build input text (keeps the human-friendly phrasing)
                input_text = (
                    f"On {start_date} at {trans_time}, daylight saving time (DST) begins in {loc1}. "
                    f"A video conference with {loc2} starts exactly when DST takes effect and ends {dur_1_str} later. "
                    f"Another meeting in {loc3} begins the moment the first meeting ends and lasts for {dur_2_str}. "
                    f"What are the start and end times of first meeting  in {loc3} in DST? Think step by step. NO EXPLANATIONS."
                )

                entry = {
                    "input": input_text,
                    "target_scores": {
                        correct: 1.0,
                        distractor: 0.0
                    }
                }

                prompts.append(entry)
                prompt_counter += 1

            except ZoneInfoNotFoundError:
                # skip triples where timezone string is invalid
                continue
            except Exception:
                # be robust: skip any triple that raises an unexpected error
                continue

# -------------------------
# Save output JSON
# -------------------------
POSTFIX=FILE[:FILE.index('.')]

OUT_FILE = "prompt1_gen_data_dst_iso_"+ POSTFIX+ ".json"

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(prompts, f, ensure_ascii=False, indent=2)

print(f"Generated {len(prompts)} prompts -> {OUT_FILE}")
if prompts:
    print("\nExample (first entry):")
    print(json.dumps(prompts[0], ensure_ascii=False, indent=2))
