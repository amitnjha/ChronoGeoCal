from __future__ import annotations
import os
import json
import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import List, Dict, Any
import pandas as pd
from global_config import MAX_COUNT,PLACES_FILE

# -------------------------
# Config
# -------------------------
IN_PLACES = PLACES_FILE  # optional input file
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]
OUT_FILE = "prompt15_dst_calendar_"+PLACES+".json"

# -------------------------
# Calendar helpers
# -------------------------
def fmt_gregorian(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M %z")

def fmt_iso_week(dt: datetime.datetime) -> str:
    iso = dt.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}-{iso[2]} {dt.strftime('%H:%M %z')}"

def jdn_from_gregorian(y: int, m: int, d: int) -> int:
    a = (14 - m)//12
    y2 = y + 4800 - a
    m2 = m + 12*a - 3
    return d + (153*m2 +2)//5 + 365*y2 + y2//4 - y2//100 + y2//400 - 32045

def jdn_to_julian(jdn: int) -> tuple[int,int,int]:
    c = jdn + 32082
    d = (4*c + 3)//1461
    e = c - (1461*d)//4
    m = (5*e + 2)//153
    day = e - (153*m +2)//5 +1
    month = m +3 -12*(m//10)
    year = d - 4800 + (m//10)
    return year, month, day

def julian_calendar_date_string(dt: datetime.datetime) -> str:
    dt_utc = dt.astimezone(datetime.timezone.utc)
    yj, mj, dj = jdn_to_julian(jdn_from_gregorian(dt_utc.year, dt_utc.month, dt_utc.day))
    return f"{yj:04d}-{mj:02d}-{dj:02d} {dt.strftime('%H:%M %z')} (Julian)"

def julian_date_jd(dt: datetime.datetime) -> float:
    dt_utc = dt.astimezone(datetime.timezone.utc)
    jdn = jdn_from_gregorian(dt_utc.year, dt_utc.month, dt_utc.day)
    return round(jdn + (dt_utc.hour-12)/24 + dt_utc.minute/1440 + dt_utc.second/86400, 6)

def make_calendar_fields(dt: datetime.datetime) -> Dict[str, Any]:
    return {
        "gregorian": fmt_gregorian(dt),
        "iso_week": fmt_iso_week(dt),
        "julian": julian_calendar_date_string(dt),
        "jd": julian_date_jd(dt),
        "utc": dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }

# -------------------------
# DST jump helper
# -------------------------
def dst_jump_time(naive: datetime.datetime, tz_name: str, jump_hours: int=1) -> datetime.datetime:
    tz = ZoneInfo(tz_name)
    jumped = naive + datetime.timedelta(hours=jump_hours)
    return jumped.replace(tzinfo=tz)

# -------------------------
# Load places
# -------------------------
def load_places(path: str) -> pd.DataFrame:
    if os.path.exists(path):
        df = pd.read_json(path)
    else:
        mock = [
            {"place":"London","tz":"Europe/London","dst":{"start":"2025-03-30","transition_time":"01:00"}},
            {"place":"New York","tz":"America/New_York","dst":{"start":"2025-03-09","transition_time":"02:00"}},
            {"place":"Tokyo","tz":"Asia/Tokyo","dst":False},
            {"place":"Sydney","tz":"Australia/Sydney","dst":{"start":"2025-10-05","transition_time":"02:00"}}
        ]
        df = pd.DataFrame(mock)
    return df.reset_index(drop=True)

# -------------------------
# Prompt generation - CAPITALIZED IMPORTANT LAST SENTENCE
# -------------------------
def generate_prompts(df_places: pd.DataFrame, max_count: int=4) -> List[Dict[str, Any]]:
    prompts = []
    counter = 0

    df_dst = df_places[df_places["dst"] != False].reset_index(drop=True)

    for _, rec1 in df_dst.iterrows():
        if counter >= max_count: break
        loc1, tz1 = rec1["place"], rec1["tz"]
        dst_info = rec1.get("dst", {})
        start_date = dst_info.get("start")
        trans_time = dst_info.get("transition_time","02:00")

        try:
            ymd = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            hm = datetime.datetime.strptime(trans_time, "%H:%M").time()
        except Exception:
            continue

        naive_transition = datetime.datetime.combine(ymd, hm)

        for _, rec2 in df_places.iterrows():
            if rec2["place"]==loc1: continue
            loc2, tz2 = rec2["place"], rec2["tz"]
            
            try:
                # correct time with DST jump (single meeting)
                correct_start = dst_jump_time(naive_transition, tz1, 1)
                
                # distractor: naive time without DST jump
                naive_start = naive_transition.replace(tzinfo=ZoneInfo(tz1))

                input_text = (
                    f"On {start_date} at {trans_time}, DST begins in {loc1}. "
                    f"Video conference with {loc2}. "
                    f"What time does the meeting start in {loc1} time zone? "
                    f"USE GREGORIAN CALENDAR IN YYYY-MM-DD HH:MM:SS FORMAT. "
                    f"Think step by step. NO EXPLANATIONS."
                )

                correct_str = correct_start.astimezone(ZoneInfo(tz1)).strftime("%Y-%m-%d %H:%M:%S")
                naive_str = naive_start.astimezone(ZoneInfo(tz1)).strftime("%Y-%m-%d %H:%M:%S")
                
                prompts.append({
                    "input": input_text,
                    "target_scores": {
                        correct_str: 1.0,
                        naive_str: 0.0
                    }
                })
                counter +=1
                if counter >= max_count: break

            except Exception:
                continue
        if counter >= max_count: break

    return prompts

# -------------------------
# Main
# -------------------------
def main():
    df_places = load_places(IN_PLACES)
    prompts = generate_prompts(df_places, MAX_COUNT)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"Generated {len(prompts)} prompts -> {OUT_FILE}")
    if prompts:
        print("Example (first entry):")
        print(json.dumps(prompts[0], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()