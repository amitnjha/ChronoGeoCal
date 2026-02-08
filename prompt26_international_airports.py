import os
import json
import re
import pytz
import random
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict


# ---------------- CONFIG ----------------
MAX_COUNT = 1000
PLACES_FILE = "international_airports.json"
PROMPTS_FILE = "prompt26_international_airports.json"
TEST_FILE = "prompt26_international_airports_test.json"
SCORED_FILE = "prompt26_international_airports_scored.json"


TIMES_TO_TEST = ["2024-03-01 10:00:00", "2024-07-15 23:30:00"]
FLIGHT_DURATIONS_HOURS = [2, 5, 11]
FALLBACK_PLACES = [
    {"place": "New York", "tz": "America/New_York"},
    {"place": "London", "tz": "Europe/London"},
    {"place": "Tokyo", "tz": "Asia/Tokyo"},
]
BIDI_CHARS = re.compile(r'[\u200f\u202a-\u202e]')


# ---------------- HELPERS ----------------
def clean_rtl(text: str) -> str:
    return BIDI_CHARS.sub('', str(text)).strip()


def fmt_ymdhms(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def load_places() -> List[Dict]:
    """Load detailed airport info (including optional DST metadata)."""
    if os.path.exists(PLACES_FILE):
        try:
            df = pd.read_json(PLACES_FILE)
            if "place" in df.columns and "tz" in df.columns:
                print(f"✓ Loaded {len(df)} airports from {PLACES_FILE}")
                records = df.to_dict("records")
                for rec in records:
                    rec.setdefault("name", rec["place"])
                    rec.setdefault("country", "")
                    rec.setdefault("dst", {})
                return records
            else:
                print(f"⚠ {PLACES_FILE} missing 'place' or 'tz' columns — using fallback.")
        except Exception as e:
            print(f"⚠ Error reading {PLACES_FILE}: {e} — using fallback.")
    else:
        print(f"⚠ {PLACES_FILE} not found, reverting to fallback airports.")
    return FALLBACK_PLACES


# ---------------- PROMPT GENERATOR ----------------
def generate_prompts() -> List[Dict]:
    places = load_places()
    prompts = []
    idx = 0
    print("Generating DST‑aware flight arrival prompts (with DST info in text)...")

    for p1 in places:
        for p2 in places:
            if p1["place"] == p2["place"]:
                continue
            if idx >= MAX_COUNT:
                break

            try:
                tz1 = pytz.timezone(p1["tz"])
                tz2 = pytz.timezone(p2["tz"])
            except Exception:
                print(f"Skipping invalid tz pair: {p1['place']} → {p2['place']}")
                continue

            for dep_time_str in TIMES_TO_TEST:
                dep_naive = datetime.strptime(dep_time_str, "%Y-%m-%d %H:%M:%S")
                dep_dt = tz1.localize(dep_naive)

                for hours in FLIGHT_DURATIONS_HOURS:
                    if idx >= MAX_COUNT:
                        break

                    flight_num = f"{random.choice(['AA','BA','JL','DL'])}{random.randint(100,999)}"

                    # --- Compute UTC arrival ---
                    arrival_utc = dep_dt.astimezone(pytz.UTC) + timedelta(hours=hours)
                    arrival_local = arrival_utc.astimezone(tz2)

                    # --- Apply custom JSON DST rules (if provided) ---
                    dst_info = p2.get("dst")
                    dst_applied = False
                    dst_text = ""
                    if dst_info and dst_info.get("observed"):
                        try:
                            start = datetime.strptime(dst_info["start"], "%Y-%m-%d").date()
                            end = datetime.strptime(dst_info["end"], "%Y-%m-%d").date()
                            local_date = arrival_local.date()

                            if start <= local_date <= end:
                                offset_str = dst_info["summer"]
                                dst_text = " (Daylight Saving Time is in effect)"
                            else:
                                offset_str = dst_info["winter"]
                                dst_text = " (Standard Time is in effect)"

                            hours_offset = int(offset_str.replace("UTC", ""))
                            adjusted = arrival_utc + timedelta(hours=hours_offset)
                            arrival_local = adjusted.replace(tzinfo=pytz.FixedOffset(hours_offset * 60))
                            dst_applied = True
                        except Exception as e:
                            print(f"⚠ Could not apply custom DST adjustment for {p2['place']}: {e}")

                    elif hasattr(arrival_local.tzinfo, 'dst') and arrival_local.tzinfo.dst(arrival_local) != timedelta(0):
                        dst_text = " (Daylight Saving Time is in effect)"
                    else:
                        dst_text = " (Standard Time is in effect)"

                    question = (
                        f"Flight {flight_num} departs {p1['place']} at "
                        f"{dep_dt.strftime('%H:%M:%S')} local time on {dep_dt.strftime('%Y-%m-%d')}. "
                        f"It arrives {p2['place']} after {hours} hours. "
                        f"What is the exact arrival time and date in {p2['place']} local time{dst_text}, "
                        f"shown in both Gregorian calendar? "
                        f"GIVE RESPONSE IN YYYY-MM-DD HH:MM:SS to YYYY-MM-DD HH:MM:SS format. "
                        f"Think step by step. NO EXPLANATIONS."
                    )

                    entry = {
                        "input": question,
                        "target_scores": {
                            fmt_ymdhms(arrival_local): 1.0,
                            fmt_ymdhms(dep_dt): 0.0
                        },
                        "metadata": {
                            "flight_num": flight_num,
                            "from": p1["place"],
                            "to": p2["place"],
                            "departure_local": fmt_ymdhms(dep_dt),
                            "flight_hours": hours,
                            "tz_from": p1["tz"],
                            "tz_to": p2["tz"],
                            "dst_applied": dst_applied,
                            "from_country": p1.get("country"),
                            "to_country": p2.get("country"),
                            "from_dst": p1.get("dst"),
                            "to_dst": p2.get("dst"),
                            "correct_arrival": fmt_ymdhms(arrival_local)
                        }
                    }
                    prompts.append(entry)
                    idx += 1

                    if idx % 100 == 0:
                        print(f"Generated {idx} prompts")

    print(f"✓ Generated {len(prompts)} DST‑aware prompts total")
    return prompts


# ---------------- SCORER (FIXED) ----------------
def score_accuracy(data: List[Dict]) -> tuple[List[Dict], float]:
    fmt = "%Y-%m-%d %H:%M:%S"

    def match(a: str, b: str) -> bool:
        try:
            return datetime.strptime(a.strip(), fmt) == datetime.strptime(b.strip(), fmt)
        except Exception:
            return False

    correct = 0
    for ex in data:
        # ✅ FIXED: Handle None explicitly
        resp = ex.get("response")
        if resp is None:
            resp = ""
        else:
            resp = str(resp).strip()
            
        correct_target = next((k for k,v in ex["target_scores"].items() if v==1.0), None)
        ok = match(resp, correct_target) if correct_target else False
        ex["isModelResponseCorrect"] = ok
        if ok:
            correct += 1

    acc = correct / len(data) * 100 if data else 0.0
    return data, acc


# ---------------- MAIN ----------------
def main():
    print("=== FLIGHT ARRIVAL PROMPT GENERATOR & EVALUATOR ===\n")

    prompts = generate_prompts()
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved: {PROMPTS_FILE} ({len(prompts)} entries)")

    # Create alternating test dataset
    test_data = []
    for i, p in enumerate(prompts[:MAX_COUNT]):
        scores = p["target_scores"]
        correct, wrong = None, None
        for k,v in scores.items():
            if v == 1.0:
                correct = k
            elif v == 0.0:
                wrong = k
        response = correct if i % 2 == 0 else wrong
        test_data.append({
            "input": p["input"],
            "response": response,
            "target_scores": scores,
            "metadata": p["metadata"]
        })

    print(f"✓ Created {len(test_data)} test responses")
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    scored, acc = score_accuracy(test_data)
    with open(SCORED_FILE, "w", encoding="utf-8") as f:
        json.dump(scored, f, ensure_ascii=False, indent=4)

    print(f"\n✓ {SCORED_FILE} | Expected accuracy: ~50% (alternating correct/wrong)")
    print(f"✓ Test complete: Accuracy = {acc:.1f}%")


if __name__ == "__main__":
    main()
