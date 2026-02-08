import os
import json
import datetime
import pandas as pd
import pytz
import re
from typing import List, Dict
from datetime import timedelta

# ---------------- CONFIG ----------------
try:
    from global_config import MAX_COUNT,PLACES_FILE
except ImportError:
    MAX_COUNT = 1000  # Generate 1000+ prompts

CURRENT_YEAR = 2025
CURRENT_MONTH = 12
CURRENT_DAY = 29
CURRENT_HOUR = 14  # 2:53 PM
CURRENT_MINUTE = 53

INPUT_PLACES_FILE = PLACES_FILE
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]
PROMPTS_FILE = "prompt11_greg_islamic_events_"+PLACES+".json"
TEST_FILE = "prompt11_greg_islamic_events_test.json"
SCORED_FILE = "prompt11_greg_islamic_events_scored.json"

# ---------------- FILES AFTER EXECUTION ----------------
# prompt11_greg_islamic_events.json      ← Raw prompts only (1000+)
# prompt11_greg_islamic_events_test.json ← Prompts + mock responses (1000+)  
# prompt11_greg_islamic_events_scored.json ← Scored with isModelResponseCorrect (1000+)

# ---------------- BiDi cleanup ----------------
BIDI_CHARS = re.compile(r'[\u200f\u202a-\u202e]')

def clean_rtl(text: str) -> str:
    if not isinstance(text, str):
        return text
    return BIDI_CHARS.sub('', text).strip()

# ---------------- LOAD PLACES ----------------
FILE = INPUT_PLACES_FILE
if os.path.exists(FILE):
    df_places = pd.read_json(FILE)
else:
    print(f"[WARN] {FILE} not found – using expanded mock data")
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
print(f"Loaded {len(places)} places for combinations")

# ---------------- CALENDAR HELPERS ----------------
def get_gregorian_date(year, month, day):
    return f"{year}-{month:02d}-{day:02d}"

def get_islamic_date(year, month, day):
    months = ["Muharram", "Safar", "Rabi I", "Rabi II", "Jumada I", "Jumada II", 
              "Rajab", "Sha'ban", "Ramadan", "Shawwal", "Dhu al-Qi'dah", "Dhu al-Hijjah"]
    return f"{day} {months[(month-1)%12]} {year} AH"

# ---------------- GENERATE PROMPTS ----------------
def generate_prompts():
    prompts: List[Dict] = []
    prompt_counter = 0

    def fmt_time(dt: datetime.datetime) -> str:
        return dt.strftime("%I:%M %p").lstrip('0')

    LTR_EMBED_START = "\u202a"
    POP_DIRECTIONAL = "\u202c"
    LRM = "\u200e"

    base_date = datetime.date(CURRENT_YEAR, CURRENT_MONTH, CURRENT_DAY)
    greg_date = get_gregorian_date(CURRENT_YEAR, CURRENT_MONTH, CURRENT_DAY)
    islamic_date = get_islamic_date(1447, 5, 15)  # Mock Islamic date
    
    greg_text = clean_rtl(greg_date)
    islamic_text = clean_rtl(islamic_date)

    print(f"--- GENERATING {MAX_COUNT}+ SAMPLES ---\n")

    # Generate across all unique quadruples of locations
    for loc1 in places:
        for loc2 in places:
            if loc1["place"] == loc2["place"]: continue
            for loc3 in places:
                if loc3["place"] in (loc1["place"], loc2["place"]): continue
                for loc4 in places:
                    if loc4["place"] in (loc1["place"], loc2["place"], loc3["place"]): continue
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

                        # Event C: runs entire B duration in loc3  
                        tz3 = pytz.timezone(loc3["tz"])
                        dt_c_start = dt_b_start.astimezone(tz3)
                        dt_c_end = dt_b_end.astimezone(tz3)

                        # All events in loc4 timezone
                        tz4 = pytz.timezone(loc4["tz"])
                        final_start = max(dt_a_start.astimezone(tz4), dt_b_start.astimezone(tz4), dt_c_start)
                        final_end = min(dt_a_end.astimezone(tz4), dt_b_end.astimezone(tz4), dt_c_end)

                        input_text = (
                            f"{LTR_EMBED_START}"
                            f"Using both Gregorian ({greg_text}) and Islamic ({islamic_text}){LRM} calendars: "
                            f"Event A in {loc1['place']} starts at {fmt_time(dt_a_start)} and ends at {fmt_time(dt_a_end)}. "
                            f"Event B in {loc2['place']} starts when A ends (meets). "
                            f"Event C in {loc3['place']} runs during the entire duration of B (during). "
                            f"When do all three events occur in {loc4['place']} time, expressed in both calendar systems?"
                            f"{POP_DIRECTIONAL}"
                        )

                        # Correct: overlap period in loc4 time + dual calendar
                        correct_start = fmt_time(final_start)
                        correct_end = fmt_time(final_end)
                        correct_answer = f"Gregorian: {correct_start}-{correct_end}, Islamic: same period on {islamic_date}"

                        # Distractor: wrong overlap (A start time)
                        distractor_answer = f"{fmt_time(dt_a_start.astimezone(tz4))}-{fmt_time(dt_a_end.astimezone(tz4))}"

                        entry = {
                            "input": input_text,
                            "target_scores": {
                                correct_answer: 1.0,
                                distractor_answer: 0.0
                            }
                        }
                        prompts.append(entry)
                        prompt_counter += 1
                        
                        if prompt_counter % 100 == 0:
                            print(f"Generated {prompt_counter}/{MAX_COUNT} prompts...")

                    except Exception as e:
                        continue

    print(f"✓ Final count: {len(prompts)} prompts generated")
    return prompts

# ---------------- ACCURACY SCORER ----------------
def score_accuracy(data):
    def normalize_time(time_str):
        if not time_str or not isinstance(time_str, str):
            return ""
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', time_str.strip().upper())
        if time_match:
            hour, minute, ampm = time_match.groups()
            hour = int(hour)
            if ampm == 'PM' and hour != 12:
                hour += 12
            elif ampm == 'AM' and hour == 12:
                hour = 0
            return f"{hour:02d}:{minute}"
        return time_str.strip()

    correct_count = 0
    total = len(data)
    
    for example in data:
        response = example.get("response", "").strip()
        target_scores = example.get("target_scores", {})
        is_correct = False

        norm_response = normalize_time(response)
        
        for key, score in target_scores.items():
            norm_key = normalize_time(key)
            
            if score == 1.0 and (norm_response in norm_key or norm_key in norm_response or 
                               "Gregorian" in response or "Islamic" in response):
                is_correct = True
                break
            elif score == 0.0 and norm_response == norm_key:
                is_correct = False
                break

        example["isModelResponseCorrect"] = is_correct
        if is_correct:
            correct_count += 1

    accuracy = (correct_count / total * 100) if total > 0 else 0
    return data, accuracy

# ---------------- MAIN WORKFLOW ----------------
def main():
    print("=== GREGORIAN+ISLAMIC EVENTS PROMPT WORKFLOW (1000+) ===\n")
    
    # 1. Generate 1000+ prompts
    prompts = generate_prompts()
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"✓ Generated {len(prompts)} prompts → {PROMPTS_FILE}")
    
    # 2. Create test file with mock responses (half correct, half wrong)
    test_data = []
    for i, prompt in enumerate(prompts[:MAX_COUNT]):
        if i % 2 == 0:
            correct_key = next(k for k, v in prompt["target_scores"].items() if v == 1.0)
            response = correct_key
        else:
            wrong_key = next(k for k, v in prompt["target_scores"].items() if v == 0.0)
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

if __name__ == "__main__":
    main()