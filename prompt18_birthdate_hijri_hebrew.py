import os
import json
import datetime
import pandas as pd
import re
from typing import List, Dict
from datetime import date
from global_config import MAX_COUNT,PLACES_FILE
from pyluach import dates


# -------------------------
# Config
# -------------------------
IN_PLACES = PLACES_FILE  # optional input file
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]

# ---------------- CONFIG ----------------
BASE_YEAR = 1990

PROMPTS_FILE = "prompt18_birthdate_hijri_hebrew_"+PLACES+".json"
TEST_FILE = "prompt18_birthdate_hijri_hebrew_test.json"
SCORED_FILE = "prompt18_birthdate_hijri_hebrew_scored.json"

# BiDi cleanup
BIDI_CHARS = re.compile(r'[\u200f\u202a-\u202e]')
def clean_rtl(text: str) -> str:
    return BIDI_CHARS.sub('', str(text)).strip() if isinstance(text, str) else str(text)

def get_gregorian_date(year: int, month: int, day: int) -> str:
    return f"{year}-{month:02d}-{day:02d}"

# ---------------- HIJRI ----------------
def greg_to_hebrew(year: int, month: int, day: int) -> tuple[int, int, int]:
    greg_date = dates.GregorianDate(year, month, day)  # Validate date
    hebrew_date = greg_date.to_heb() ##dates.HebrewDate.from_gregorian(greg_date.year, greg_date.month, greg_date.day)
    return hebrew_date.year, hebrew_date.month, hebrew_date.day


# ---------------- GENERATE PROMPTS (NO LUNAR) ----------------
def generate_prompts() -> List[Dict]:
    prompts: List[Dict] = []
    LTR, POP = "\u202a", "\u202c"
    
    print("--- GENERATING 1000 BIRTHDATE PROMPTS (Hijri+Hebrew ONLY) ---\n")
    
    years = list(range(1950, 2011, 3))  # Step for speed
    months = list(range(1, 13))
    days = [1, 15, 28]
    
    idx = 0
    for year in years:
        for month in months:
            for day in days:
                if idx >= MAX_COUNT: break
                try:
                    #greg = get_gregorian_date(year, month, day)
                    greg = dates.GregorianDate(year, month, day)
                    hebrew = greg_to_hebrew(year, month, day)
                    
                    # CORRECT (1.0): Hijri then Hebrew
                    #correct_ans = f"Hijri: {clean_rtl(hijri)}, Hebrew: {clean_rtl(hebrew)}"
                    correct_ans = f"{hebrew[0]}-{hebrew[1]}-{hebrew[2]}"
                    
                    # WRONG (0.0): Swapped
                    wrong_ans = f" Hebrew: {clean_rtl(hebrew)}"
                    
                    prompt = (
                        f"{LTR}I was born on [{clean_rtl(greg)}]. "
                        # f"What is my date in the [Hijri and Hebrew Calendar]?{POP}"
                        f"What is my date in the Hebrew Calendar in YYY-MM-DD format?Think step by step. NO EXPLANATIONS.{POP}"
                    )
                    
                    entry = {
                        "input": prompt,
                        "target_scores": {
                            correct_ans: 1.0,    # Line 1: Correct order
                            wrong_ans: 0.0       # Line 2: Swapped
                        }
                    }
                    prompts.append(entry)
                    idx += 1
                    
                    if idx % 100 == 0:
                        print(f"Generated {idx}/{MAX_COUNT}...")
                except Exception as e:
                    print(f"Skipping invalid date: {year}-{month}-{day} ({e})")
                    continue
        if idx >= MAX_COUNT: break
    
    print(f"✓ {len(prompts)} prompts (Hijri+Hebrew, 2 targets each)")
    return prompts

# ---------------- SCORER ----------------
def score_accuracy(data: List[Dict]) -> tuple[List[Dict], float]:
    def calendar_match(resp: str, target: str) -> bool:
        resp_lower, target_lower = resp.lower().strip(), target.lower().strip()
        # Must have both "hijri" and "hebrew" + substantial date match
        if "hijri" in resp_lower and "hebrew" in resp_lower:
            resp_words = set(resp_lower.replace(",", "").split())
            target_words = set(target_lower.replace(",", "").split())
            return len(resp_words & target_words) / len(target_words) >= 0.75
        return False
    
    total_correct = 0
    for ex in data:
        resp = ex.get("response", "")
        scores = ex["target_scores"]
        correct_key = next(k for k,v in scores.items() if v==1.0)
        is_correct = calendar_match(resp, correct_key)
        ex["isModelResponseCorrect"] = is_correct
        if is_correct: total_correct += 1
    
    acc = total_correct / len(data) * 100 if data else 0
    return data, acc

# ---------------- MAIN ----------------
def main():
    print("=== BIRTHDATE HIJRI+HEBREW (NO LUNAR) ===\n")
    
    prompts = generate_prompts()
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"✓ {PROMPTS_FILE}")
    
    test_data = []
    for i, p in enumerate(prompts[:MAX_COUNT]):
        scores = p["target_scores"]
        correct = next(k for k,v in scores.items() if v==1.0)
        wrong = next(k for k,v in scores.items() if v==0.0)
        resp = correct if i % 2 == 0 else wrong
        test_data.append({"input": p["input"], "response": resp, "target_scores": scores})
    
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    print(f"✓ {TEST_FILE}")
    
    scored, acc = score_accuracy(test_data)
    with open(SCORED_FILE, "w", encoding="utf-8") as f:
        json.dump(scored, f, ensure_ascii=False, indent=4)
    
    print(f"\n✓ {SCORED_FILE} | Accuracy: {acc:.1f}%")
    print("Lunar removed - Hijri+Hebrew only!")

if __name__ == "__main__":
    main()