import os
import json
import datetime
import pandas as pd
import pytz
import re
from typing import List, Dict
from global_config import MAX_COUNT,PLACES_FILE
CURRENT_YEAR = 2025
CURRENT_MONTH = 12
CURRENT_DAY = 29
CURRENT_HOUR = 14  # 2:42 PM
CURRENT_MINUTE = 42

INPUT_PLACES_FILE = PLACES_FILE
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]

PROMPTS_FILE = "prompt5_chinese_lunar_time_"+PLACES+".json"

TEST_FILE = "prompt5_chinese_lunar_time_test.json"
SCORED_FILE = "prompt5_chinese_lunar_time_scored.json"

# ---------------- FILES AFTER EXECUTION ----------------
# prompt5_chinese_lunar_time.json      ← Raw prompts only (1000+)
# prompt5_chinese_lunar_time_test.json ← Prompts + mock responses (1000+)  
# prompt5_chinese_lunar_time_scored.json ← Scored with isModelResponseCorrect (1000+)

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

# ---------------- GENERATE PROMPTS ----------------
def generate_prompts():
    prompts: List[Dict] = []
    prompt_counter = 0

    def fmt_time(dt: datetime.datetime) -> str:
        return dt.strftime("%I:%M %p").lstrip('0')

    def get_chinese_lunar_date(year: int, month: int, day: int) -> str:
        animals = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake", "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"]
        animal = animals[(year - 4) % 12]
        return f"{day}th day of the {month}th lunar month in the Year of the {animal}"

    LTR_EMBED_START = "\u202a"
    POP_DIRECTIONAL = "\u202c"
    LRM = "\u200e"

    base_date = datetime.date(CURRENT_YEAR, CURRENT_MONTH, CURRENT_DAY)
    lunar_date_str = get_chinese_lunar_date(CURRENT_YEAR, 11, 12)
    lunar_text = clean_rtl(lunar_date_str)
    naive_dt = datetime.datetime(CURRENT_YEAR, CURRENT_MONTH, CURRENT_DAY, CURRENT_HOUR, CURRENT_MINUTE, 0)

    print(f"--- GENERATING {MAX_COUNT}+ SAMPLES ---\n")

    for p1 in places:  # reference
        for p2 in places:  # target
            if p1["place"] == p2["place"]:
                continue
            if prompt_counter >= MAX_COUNT:
                break

            try:
                tz1 = pytz.timezone(p1["tz"])
                tz2 = pytz.timezone(p2["tz"])
                dt_ref = tz1.localize(naive_dt)
                dt_target = dt_ref.astimezone(tz2)
                
                input_text = (
                    f"{LTR_EMBED_START}"
                    f"Today is the Chinese lunar date {lunar_text}{LRM}. "
                    f"Using the current global time zone system, if it is 2:42 PM in {p1['place']}, "
                    f"what is the current local time in {p2['place']}?Think step by step. NO EXPLANATIONS."
                    f"{POP_DIRECTIONAL}"
                )

                correct_answer = f"{fmt_time(dt_target)}"
                distractor_time = dt_ref + datetime.timedelta(hours=3)
                distractor_answer = f"{fmt_time(distractor_time.astimezone(tz2))}"

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
            
            if score == 1.0 and (norm_response == norm_key or norm_response in norm_key or norm_key in norm_response):
                is_correct = True
                break
            elif score == 0.0 and (norm_response == norm_key or norm_response in norm_key):
                is_correct = False
                break

        example["isModelResponseCorrect"] = is_correct
        if is_correct:
            correct_count += 1

    accuracy = (correct_count / total * 100) if total > 0 else 0
    return data, accuracy

# ---------------- MAIN WORKFLOW ----------------
def main():
    print("=== CHINESE LUNAR TIME ZONE PROMPT WORKFLOW (1000+) ===\n")
    
    # 1. Generate 1000+ prompts
    prompts = generate_prompts()
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"✓ Generated {len(prompts)} prompts → {PROMPTS_FILE}")
    
    # 2. Create test file with mock responses (half correct, half wrong)
    test_data = []
    for i, prompt in enumerate(prompts[:MAX_COUNT]):
        # Alternate correct/wrong responses
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
    
    # Show first example
    if scored_data:
        print(f"\nExample (first):")
        print(json.dumps(scored_data[0], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
