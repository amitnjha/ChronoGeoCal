import os
import json
import re
import pytz
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
# from global_config import MAX_COUNT,PLACES_FILE

# Local config fallback (replaces global_config)
MAX_COUNT = 1000
PLACES_FILE = "places.json"

# -------------------------
# Config
# -------------------------
IN_PLACES = PLACES_FILE  # optional input file
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]

# ---------------- CONFIG ----------------
PROMPTS_FILE = "prompt23_flight_time_"+PLACES+".json"
TEST_FILE = "prompt23_flight_time_test.json"
SCORED_FILE = "prompt23_flight_time_scored.json"

TIMES_TO_TEST = ["2024-03-01 10:00:00", "2024-07-15 23:30:00"]
FLIGHT_DURATIONS_HOURS = [2, 5, 11]  # short, medium, long-haul

INPUT_PLACES_FILE = PLACES_FILE
FALLBACK_PLACES = [
    {"place": "New York", "tz": "America/New_York"},
    {"place": "London", "tz": "Europe/London"},
    {"place": "Tokyo", "tz": "Asia/Tokyo"},
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
            df.columns = [str(c).strip() for c in df.columns]  # Added column normalization
            if all(c in df.columns for c in ["place", "tz"]):
                print(f"✓ Loaded {len(df)} places from {places_file}")
                return df.to_dict("records")
            else:
                print(f"⚠ {places_file} missing 'place'/'tz' columns (found: {list(df.columns)}) — using fallback.")
        except Exception as e:
            print(f"⚠ Error reading {places_file}: {e} — using fallback.")
    else:
        print(f"⚠ {places_file} not found — using fallback examples.")
    
    print(f"✓ Using fallback places ({len(FALLBACK_PLACES)} entries)")  # Fixed count
    return FALLBACK_PLACES

# ---------------- PROMPT GENERATOR WITH VALIDATION ----------------
def generate_prompts() -> List[Dict]:
    places = load_places()
    prompts = []
    LTR, POP = "\u202a", "\u202c"

    print("Generating flight time prompts...")

    def validate_flight_calc(  # NEW: Double-check validation
        dep_dt: datetime, 
        arrival_local: datetime, 
        tz1_name: str, 
        tz2_name: str, 
        hours: float
    ) -> bool:
        """Double-check the timezone calculation makes sense."""
        try:
            # Recalculate independently to verify
            dep_utc = dep_dt.astimezone(pytz.UTC)
            expected_utc = dep_utc + timedelta(hours=hours)
            recalc_local = expected_utc.astimezone(pytz.timezone(tz2_name))
            
            # Check if results match exactly (down to second)
            if arrival_local != recalc_local:
                print(f"⚠ CALC MISMATCH: {tz1_name}→{tz2_name} "
                      f"{dep_dt} +{hours}h = {arrival_local} vs {recalc_local}")
                return False
            
            # Sanity: flight shouldn't arrive before departure (in UTC)
            if expected_utc <= dep_utc:
                print(f"⚠ TIME TRAVEL: {dep_utc} → {expected_utc}")
                return False
                
            return True
            
        except Exception as e:
            print(f"⚠ Validation failed ({tz1_name}→{tz2_name}): {e}")
            return False

    idx = 0
    error_count = 0  # NEW: Track validation failures
    for p1 in places:
        for p2 in places:
            if p1["place"] == p2["place"]:
                continue
            if idx >= MAX_COUNT: 
                break

            tz1_name, tz2_name = p1["tz"], p2["tz"]  # Capture names for validation
            try:
                tz1 = pytz.timezone(tz1_name)
                tz2 = pytz.timezone(tz2_name)
            except Exception as e:
                print(f"Skipping pair ({p1['place']}, {p2['place']}): invalid tz")
                continue

            for dep_time_str in TIMES_TO_TEST:
                dep_naive = datetime.strptime(dep_time_str, "%Y-%m-%d %H:%M:%S")
                dep_dt = tz1.localize(dep_naive)

                for hours in FLIGHT_DURATIONS_HOURS:
                    if idx >= MAX_COUNT: 
                        break

                    arrival_utc = dep_dt.astimezone(pytz.UTC) + timedelta(hours=hours)
                    arrival_local = arrival_utc.astimezone(tz2)

                    # NEW: Double-check validation before creating prompt
                    if not validate_flight_calc(dep_dt, arrival_local, tz1_name, tz2_name, hours):
                        error_count += 1
                        continue

                    question = (
                        f"{LTR}If I fly from {p1['place']} to {p2['place']} "
                        f"(a {hours}-hour flight) and take off at {fmt_ymdhms(dep_dt)} "
                        f"local time, what is the local time in {p2['place']} when I land? "
                        f"GIVE RESPONSE IN YYYY-MM-DD HH:MM:SS format.Think step by step. NO EXPLANATIONS.{POP}"
                    )

                    entry = {
                        "input": question,
                        "target_scores": {
                            fmt_ymdhms(arrival_local): 1.0,
                            fmt_ymdhms(dep_dt): 0.0  # deliberate wrong answer
                        },
                        "metadata": {
                            "from": p1["place"],
                            "to": p2["place"],
                            "departure": fmt_ymdhms(dep_dt),
                            "flight_hours": hours,
                            "correct_arrival": fmt_ymdhms(arrival_local),
                            "validated": True  # NEW: Validation marker
                        }
                    }
                    prompts.append(entry)
                    idx += 1
                    
                    if idx % 100 == 0:
                        print(f"Generated {idx} prompts ({error_count} skipped)")  # Show skipped count

    print(f"✓ Generated {len(prompts)} prompts total ({error_count} invalid calculations skipped)")  # Show final stats
    return prompts

# ---------------- FIXED SCORER WITH FLEXIBLE PARSING ----------------
def score_accuracy(data: List[Dict]) -> tuple[List[Dict], float]:
    """Compare model responses to correct target times."""
    def time_match(resp: str, target: str) -> bool:  # ENHANCED: Multiple formats
        """Flexible datetime matching with multiple formats."""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S %Z",  # with timezone name
            "%Y-%m-%dT%H:%M:%S",     # ISO format
            "%m/%d/%Y %H:%M:%S",     # US format
        ]
        
        def try_parse(text: str):
            text = text.strip()
            for fmt in formats:
                try:
                    return datetime.strptime(text, fmt)
                except ValueError:
                    continue
            return None
        
        r_dt = try_parse(resp)
        t_dt = try_parse(target)
        
        if r_dt is None or t_dt is None:
            return False
        
        return r_dt == t_dt

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

        is_ok = time_match(resp, correct_key)
        ex["isModelResponseCorrect"] = is_ok
        if is_ok:
            correct += 1

    acc = (correct / len(data) * 100) if data else 0
    return data, acc

# ---------------- MAIN ----------------
def main():
    print("=== FLIGHT TIME PROMPT GENERATOR & EVALUATOR ===\n")

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
        
        if not correct_key or not wrong_key:
            continue
        
        # Alternate: even indices = correct, odd = wrong
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
