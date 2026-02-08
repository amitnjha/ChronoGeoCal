import os
import json
import datetime
import pandas as pd
import pytz
import re
from typing import List, Dict
from datetime import timedelta
from itertools import combinations

# ---------------- CONFIG ----------------
try:
    from global_config import MAX_COUNT,PLACES_FILE
except ImportError:
    MAX_COUNT = 1000

CURRENT_YEAR = 2026
CURRENT_MONTH = 1
CURRENT_DAY = 8
CURRENT_HOUR = 20
CURRENT_MINUTE = 28

INPUT_PLACES_FILE = PLACES_FILE if 'PLACES_FILE' in locals() else "places.json"
PLACES=INPUT_PLACES_FILE[:INPUT_PLACES_FILE.index('.') if '.' in INPUT_PLACES_FILE else len(INPUT_PLACES_FILE)]
PROMPTS_FILE = "prompt11_greg_events_"+PLACES+".json"
TEST_FILE = "prompt11_greg_events_test.json"
SCORED_FILE = "prompt11_greg_events_scored.json"

# ---------------- LOAD PLACES ----------------
FILE = INPUT_PLACES_FILE
if os.path.exists(FILE):
    df_places = pd.read_json(FILE)
else:
    print(f"[WARN] {FILE} not found – using mock data")
    mock_data = {
        "place": [
            "New York", "London", "Jerusalem", "Tokyo", "Sydney", "Beijing", "Paris", "Dubai",
            "Los Angeles", "Chicago", "Toronto", "Mumbai", "Singapore", "Hong Kong", "Seoul",
            "Moscow", "Istanbul", "Cape Town", "Rio de Janeiro", "Mexico City", "Buenos Aires"
        ],
        "tz": [
            "America/New_York", "Europe/London", "Asia/Jerusalem", "Asia/Tokyo", "Australia/Sydney", 
            "Asia/Shanghai", "Europe/Paris", "Asia/Dubai", "America/Los_Angeles", "America/Chicago",
            "America/Toronto", "Asia/Kolkata", "Asia/Singapore", "Asia/Hong_Kong", "Asia/Seoul",
            "Europe/Moscow", "Europe/Istanbul", "Africa/Johannesburg", "America/Sao_Paulo", 
            "America/Mexico_City", "America/Argentina/Buenos_Aires"
        ],
    }
    df_places = pd.DataFrame(mock_data)

df_places = df_places[['place', 'tz']]
places = df_places.to_dict("records")
print(f"Loaded {len(places)} places")

# ---------------- CALENDAR HELPERS ----------------
def get_gregorian_date(year, month, day):
    return f"{year}-{month:02d}-{day:02d}"

def fmt_time(dt: datetime.datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip('0')

# ---------------- GENERATE SENTENCE-BASED PROMPTS ----------------
def generate_prompts():
    prompts: List[Dict] = []
    prompt_counter = 0

    greg_date = get_gregorian_date(CURRENT_YEAR, CURRENT_MONTH, CURRENT_DAY)
    
    place_pairs = list(combinations(places, 2))
    print(f"--- GENERATING {MAX_COUNT}+ GREGORIAN TIMEZONE SAMPLES ({len(place_pairs)} pairs) ---\n")

    for pair in place_pairs:
        loc1, loc2 = pair
        if prompt_counter >= MAX_COUNT:
            break
            
        try:
            # Event A: 2-4 AM in loc1
            tz1 = pytz.timezone(loc1["tz"])
            a_start_naive = datetime.datetime(CURRENT_YEAR, CURRENT_MONTH, CURRENT_DAY, 2, 0, 0)
            a_end_naive = datetime.datetime(CURRENT_YEAR, CURRENT_MONTH, CURRENT_DAY, 4, 0, 0)
            dt_a_start = tz1.localize(a_start_naive)
            dt_a_end = tz1.localize(a_end_naive)

            # Event B: starts when A ends, runs 2 hours in loc2
            tz2 = pytz.timezone(loc2["tz"])
            dt_b_start = dt_a_end.astimezone(tz2)
            dt_b_end = dt_b_start + timedelta(hours=2)

            # GREGORIAN + TIMEZONE CHAINING TEST
            input_text = (
                f"Today is {greg_date}. " 
                f"Event A happens in {loc1['place']} from {fmt_time(dt_a_start)} to {fmt_time(dt_a_end)}. "
                f"Event B in {loc2['place']} starts exactly when Event A ends and lasts 2 hours. "
                f"What time does Event B happen in {loc2['place']} time? " 
                f"GIVE RESPONSE IN HH:MM AM/PM - HH:MM AM/PM format. "
                f"Think step by step. NO EXPLANATIONS."
                
            )

            # Both correct AND distractor answers
            correct_answer = f"{fmt_time(dt_b_start)} - {fmt_time(dt_b_end)}"
            distractor_answer = f"{fmt_time(dt_a_start)} - {fmt_time(dt_a_end)}"  # Event A times (wrong)

            entry = {
                "input": input_text,
                "target_scores": {
                    correct_answer: 1.0,      # Correct: Event B times in loc2 timezone
                    distractor_answer: 0.0    # Wrong: Event A times from loc1 timezone
                }
            }
            prompts.append(entry)
            prompt_counter += 1
            
            if prompt_counter % 100 == 0:
                print(f"Generated {prompt_counter}/{MAX_COUNT} prompts...")

        except Exception as e:
            print(f"Error with {loc1['place']}-{loc2['place']}: {e}")
            continue

    print(f"✓ Final count: {len(prompts)} prompts generated")
    return prompts

# ---------------- SCORING ----------------
def score_accuracy(data):
    correct_count = 0
    total = len(data)
    
    for example in data:
        response = example.get("response", "").strip()
        target_scores = example.get("target_scores", {})
        is_correct = False

        for key, score in target_scores.items():
            if score == 1.0 and key in response:
                is_correct = True
                break
            elif score == 0.0 and key in response:
                is_correct = False
                break

        example["isModelResponseCorrect"] = is_correct
        if is_correct:
            correct_count += 1

    accuracy = (correct_count / total * 100) if total > 0 else 0
    return data, accuracy

# ---------------- MAIN WORKFLOW ----------------
def main():
    print("=== GREGORIAN TWO-PLACE TIMEZONE WORKFLOW (1000+) ===\n")
    
    # 1. Generate 1000+ prompts
    prompts = generate_prompts()
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"✓ Generated {len(prompts)} prompts → {PROMPTS_FILE}")
    
    # 2. Create test file with mock responses (half correct, half wrong)
    test_data = []
    for i, prompt in enumerate(prompts[:MAX_COUNT]):
        target_scores = prompt["target_scores"]
        if i % 2 == 0:
            correct_key = next(k for k, v in target_scores.items() if v == 1.0)
            response = correct_key
        else:
            wrong_key = next(k for k, v in target_scores.items() if v == 0.0)
            response = wrong_key
            
        test_data.append({
            **prompt,
            "response": response
        })
    
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    print(f"✓ Created {len(test_data)} test examples → {TEST_FILE}")
    
    # 3. Score accuracy
    scored_data, accuracy = score_accuracy(test_data)
    with open(SCORED_FILE, "w", encoding="utf-8") as f:
        json.dump(scored_data, f, ensure_ascii=False, indent=4)
    
    print(f"\n=== RESULTS (1000+ SCALE) ===")
    print(f"✓ Scored {len(scored_data)} examples → {SCORED_FILE}")
    print(f"Accuracy: {accuracy:.1f}% ({accuracy>50 and 'PASS' or 'FAIL'})")
    print(f"Files ready for model testing!")
    print("\nSample:")
    print("-" * 50)
    if prompts:
        print(prompts[0]["input"])
        print(f"\nCorrect: {next(k for k,v in prompts[0]['target_scores'].items() if v==1.0)}")
        print(f"Wrong:   {next(k for k,v in prompts[0]['target_scores'].items() if v==0.0)}")

if __name__ == "__main__":
    main()