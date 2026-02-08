import os
import json
import re
import pytz
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
from global_config import MAX_COUNT,PLACES_FILE



# -------------------------
# Config
# -------------------------
IN_PLACES = PLACES_FILE  # optional input file
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]

# ---------------- CONFIG ----------------
PROMPTS_FILE = "prompt24_meeting_time_"+PLACES+".json"
TEST_FILE = "prompt24_meeting_time_test.json"
SCORED_FILE = "prompt24_meeting_time_scored.json"

# Test date/times (weekday) - 12 DIVERSE SLOTS
TIMESLOTS = [
    # Morning slots
    ("09:00", "11:00"),  # Standard morning (2h)
    ("08:00", "10:00"),  # Early morning (2h)  
    ("10:00", "12:00"),  # Late morning (2h)
    
    # Afternoon slots
    ("14:00", "16:00"),  # Standard afternoon (2h)
    ("13:00", "15:00"),  # Early afternoon (2h)
    ("15:00", "17:00"),  # Late afternoon (2h)
    
    # Extended workday slots
    ("09:00", "12:00"),  # Full morning (3h)
    ("13:00", "17:00"),  # Full afternoon (4h)
    
    # Short meeting slots (30-60 min)
    ("10:30", "11:00"),  # 30min quick sync
    ("14:30", "15:00"),  # 30min check-in
    
    # Lunch-adjacent
    ("11:30", "13:00"),  # Pre-lunch (1.5h)
    ("16:00", "17:30"),  # End-of-day (1.5h)
]

TEST_DATE = "2026-04-15"  # Wednesday (weekday)

INPUT_PLACES_FILE = PLACES_FILE
FALLBACK_PLACES = [
    {"place": "New York", "country": "USA", "tz": "America/New_York"},
    {"place": "London", "country": "UK", "tz": "Europe/London"},
    {"place": "Tokyo", "country": "Japan", "tz": "Asia/Tokyo"},
    {"place": "Sydney", "country": "Australia", "tz": "Australia/Sydney"},
    {"place": "Berlin", "country": "Germany", "tz": "Europe/Berlin"},
]

# ---------------- BiDi CLEANUP ----------------
BIDI_CHARS = re.compile(r'[\u200f\u202a-\u202e]')

def clean_rtl(text: str) -> str:
    """Strip problematic BiDi control chars, keep LRM safe."""
    return BIDI_CHARS.sub('', str(text)).strip()

def fmt_ymdhms(dt: datetime) -> str:
    """Format timezone-aware datetime as 'YYYY-MM-DD HH:MM:SS'."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# ---------------- LOAD PLACES ----------------
def load_places(places_file: str = INPUT_PLACES_FILE) -> List[Dict]:
    """Load places from JSON or return fallback examples."""
    if os.path.exists(places_file):
        try:
            df = pd.read_json(places_file)
            required_cols = ["place", "country", "tz"]
            if all(c in df.columns for c in required_cols):
                print(f"✓ Loaded {len(df)} places from {places_file}")
                return df.to_dict("records")
            else:
                print(f"⚠ {places_file} missing columns {required_cols} — using fallback.")
        except Exception as e:
            print(f"⚠ Error reading {places_file}: {e} — using fallback.")
    else:
        print(f"⚠ {places_file} not found — using fallback examples.")
    
    print("✓ Using fallback places")
    return FALLBACK_PLACES

# ---------------- FIND OVERLAP HELPER (FIXED) ----------------
def find_time_overlap(tz_a: pytz.BaseTzInfo, tz_b: pytz.BaseTzInfo, 
                     start_a: str, end_a: str, start_b: str, end_b: str,
                     test_date: str) -> tuple[str, str, str]:
    """Find overlapping time slot. ALWAYS returns specific timestamps."""
    
    fmt = "%Y-%m-%d %H:%M:%S"
    
    # Parse times for both locations (add seconds)
    times_a = [datetime.strptime(f"{test_date} {t}:00", fmt) for t in [start_a, end_a]]
    times_b = [datetime.strptime(f"{test_date} {t}:00", fmt) for t in [start_b, end_b]]
    
    # Localize to respective timezones
    local_a_start, local_a_end = tz_a.localize(times_a[0]), tz_a.localize(times_a[1])
    local_b_start, local_b_end = tz_b.localize(times_b[0]), tz_b.localize(times_b[1])
    
    # Convert to UTC for comparison
    utc_a_start, utc_a_end = local_a_start.astimezone(pytz.UTC), local_a_end.astimezone(pytz.UTC)
    utc_b_start, utc_b_end = local_b_start.astimezone(pytz.UTC), local_b_end.astimezone(pytz.UTC)
    
    # Find overlap in UTC
    overlap_start = max(utc_a_start, utc_b_start)
    overlap_end = min(utc_a_end, utc_b_end)
    
    if overlap_start >= overlap_end:
        # NO OVERLAP: Return City B's local times converted to City A timezone (specific but wrong)
        b_start_a_tz = local_b_start.astimezone(tz_a)
        b_end_a_tz = local_b_end.astimezone(tz_a)
        return (
            fmt_ymdhms(b_start_a_tz),    # Specific: B's start time in A's timezone
            fmt_ymdhms(b_end_a_tz),      # Specific: B's end time in A's timezone
            "NO_OVERLAP"
        )
    
    # HAS OVERLAP: Return actual overlap in City A timezone
    overlap_a_local = overlap_start.astimezone(tz_a)
    overlap_a_end_local = overlap_end.astimezone(tz_a)
    
    return (
        fmt_ymdhms(overlap_a_local),
        fmt_ymdhms(overlap_a_end_local),
        "HAS_OVERLAP"
    )

# ---------------- PROMPT GENERATOR ----------------
def generate_prompts() -> List[Dict]:
    places = load_places()
    prompts = []
    LTR, POP = "\u202a", "\u202c"

    print("Generating meeting time prompts...")

    idx = 0
    for p1 in places:
        for p2 in places:
            if p1["place"] == p2["place"]:
                continue
            if idx >= MAX_COUNT: 
                break

            try:
                tz1 = pytz.timezone(p1["tz"])
                tz2 = pytz.timezone(p2["tz"])
            except Exception as e:
                print(f"Skipping pair ({p1['place']}, {p2['place']}): invalid tz")
                continue

            for start_time, end_time in TIMESLOTS:
                if idx >= MAX_COUNT: 
                    break

                # Find actual overlap (returns specific timestamps)
                correct_start, correct_end, status = find_time_overlap(
                    tz1, tz2, start_time, end_time, start_time, end_time, TEST_DATE
                )
                
                # ALWAYS specific timestamps - never vague strings
                if status == "NO_OVERLAP":
                    correct_answer = "No Overlap"
                else:
                    correct_answer = f"{correct_start} to {correct_end}"

                wrong_answer = f"{TEST_DATE} {start_time}:00 to {TEST_DATE} {end_time}:00"  # Ignores timezone diff

                question = (
                    f"{LTR}On {TEST_DATE} I need to schedule a meeting between a colleague in "
                    f"{p1['place']}, {p1['country']} and a colleague in "
                    f"{p2['place']}, {p2['country']}. What is a reasonable time slot "
                    f"where it is between {start_time} and {end_time} for both of them? "
                    f"GIVE RESPONSE IN YYYY-MM-DD HH:MM:SS to YYYY-MM-DD HH:MM:SS format for {p1['place']}, {p1['country']} time. If there is no overlap answer 'No Overlap'.Pleawe think step by step. RESPOND IN THE FOLLOWING FORMAT"
                    f"{{Answer: YYYY-MM-DD HH:MM:SS to YYYY-MM-DD HH:MM:SS , \nExplanation: your_explanation\n}}"
                )

                entry = {
                    "input": question,
                    "target_scores": {
                        correct_answer: 1.0,           # e.g. "2026-04-15 09:00:00 to 2026-04-15 10:00:00"
                        wrong_answer: 0.0              # e.g. "2026-04-15 09:00:00 to 2026-04-15 11:00:00"
                    },
                    "metadata": {
                        "city_a": p1["place"],
                        "country_a": p1["country"],
                        "city_b": p2["place"],
                        "country_b": p2["country"],
                        "time_slot": f"{start_time}-{end_time}",
                        "test_date": TEST_DATE,
                        "status": status,
                        "correct_overlap": correct_answer,
                        "wrong_overlap": wrong_answer
                    }
                }
                prompts.append(entry)
                idx += 1
                
                if idx % 100 == 0:
                    print(f"Generated {idx} prompts")

    print(f"✓ Generated {len(prompts)} prompts total")
    return prompts

# ---------------- FIXED SCORER ----------------
def score_accuracy(data: List[Dict]) -> tuple[List[Dict], float]:
    """Compare model responses to correct target times."""
    def overlap_match(resp: str, target: str) -> bool:
        resp = resp.strip()
        target = target.strip()
        # Exact match first
        if resp == target:
            return True
        # Extract and compare datetime pairs
        dates_r = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', resp)
        dates_t = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', target)
        return len(dates_r) == 2 and len(dates_t) == 2 and dates_r == dates_t

    correct = 0
    for ex in data:
        resp = ex.get("response", "").strip()
        targets = ex.get("target_scores", {})

        correct_key = None
        for k, v in targets.items():
            if v == 1.0:
                correct_key = k
                break

        if not correct_key:
            print(f"WARNING: No 1.0 entry found")
            ex["isModelResponseCorrect"] = False
            continue

        is_ok = overlap_match(resp, correct_key)
        ex["isModelResponseCorrect"] = is_ok
        if is_ok:
            correct += 1

    acc = (correct / len(data) * 100) if data else 0
    return data, acc

# ---------------- MAIN ----------------
def main():
    print("=== MEETING TIME PROMPT GENERATOR & EVALUATOR ===\n")

    # Generate and save prompts
    prompts = generate_prompts()
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved prompts: {PROMPTS_FILE} ({len(prompts)} entries)")

    # Generate synthetic test data (alternating correct/incorrect responses)
    test_data = []
    for i, p in enumerate(prompts[:MAX_COUNT]):
        scores = p["target_scores"]
        correct_key = None
        wrong_key = None
        for k, v in scores.items():
            if v == 1.0: 
                correct_key = k
            elif v == 0.0: 
                wrong_key = k
        
        if correct_key and wrong_key:
            response = correct_key if i % 2 == 0 else wrong_key
            test_data.append({
                "input": p["input"],
                "response": response,
                "target_scores": scores,
                "metadata": p.get("metadata", {})
            })
    
    print(f"✓ Created {len(test_data)} synthetic test responses")
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    # Score the synthetic responses
    scored, acc = score_accuracy(test_data)
    with open(SCORED_FILE, "w", encoding="utf-8") as f:
        json.dump(scored, f, ensure_ascii=False, indent=4)
    
    print(f"\n✓ {SCORED_FILE} | Expected accuracy: ~50% (alternating correct/wrong)")
    print(f"✓ Test complete: Accuracy = {acc:.1f}%")

if __name__ == "__main__":
    main()