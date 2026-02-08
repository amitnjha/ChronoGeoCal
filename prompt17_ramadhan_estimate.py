import os
import json
import datetime
import pandas as pd
import re
from typing import List, Dict
from datetime import date, timedelta
from global_config import MAX_COUNT,PLACES_FILE



# -------------------------
# Config
# -------------------------
IN_PLACES = PLACES_FILE  # optional input file
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]

# ---------------- CONFIG ----------------
BASE_YEAR = 2025

PROMPTS_FILE = "prompt17_ramadhan_estimate_"+PLACES+".json"
TEST_FILE = "prompt17_ramadhan_estimate_test.json"
SCORED_FILE = "prompt17_ramadhan_estimate_scored.json"

# BiDi cleanup
BIDI_CHARS = re.compile(r'[\u200f\u202a-\u202e]')
def clean_rtl(text: str) -> str:
    return BIDI_CHARS.sub('', str(text)).strip() if isinstance(text, str) else str(text)

def get_gregorian_date(year: int, month: int, day: int) -> str:
    return f"{year}-{month:02d}-{day:02d}"

# ---------------- RAMADHAN ESTIMATE ----------------
def estimate_ramadhan(start_date_str: str, target_year: int) -> str:
    """Correct: Ramadan moves EARLIER (-11 days per year)."""
    start_date = date.fromisoformat(start_date_str)
    years_diff = target_year - start_date.year
    estimated = start_date - timedelta(days=11 * years_diff)
    return get_gregorian_date(estimated.year, estimated.month, estimated.day)

def wrong_direction_estimate(start_date_str: str, target_year: int) -> str:
    """Distractor: wrong direction (+11 days/year)."""
    start_date = date.fromisoformat(start_date_str)
    years_diff = target_year - start_date.year
    wrong_estimated = start_date + timedelta(days=11 * years_diff)  # Wrong!
    return get_gregorian_date(wrong_estimated.year, wrong_estimated.month, wrong_estimated.day)

# ---------------- GENERATE PROMPTS ----------------
def generate_prompts() -> List[Dict]:
    prompts: List[Dict] = []
    LTR, POP, LRM = "\u202a", "\u202c", "\u200e"
    
    print("--- GENERATING 1000 RAMADHAN PROMPTS (2 targets each) ---\n")
    
    # Ramadan-like dates: March-May, various years
    base_configs = []
    for year_offset in [-2, 0, 2]:
        base_year = BASE_YEAR + year_offset
        for month in [3, 4, 5]:
            for day in range(1, 29):  # Safe days
                base_configs.append((base_year, month, day))
    
    prompt_idx = 0
    for base_year, base_month, base_day in base_configs:
        if prompt_idx >= MAX_COUNT: break
        
        greg_start = get_gregorian_date(base_year, base_month, base_day)
        
        # Vary target years: ±1 to ±5 years
        for target_offset in [-5, -3, -1, 1, 3, 5]:
            if prompt_idx >= MAX_COUNT: break
            target_year = BASE_YEAR + target_offset
            
            # CORRECT (1.0): moves earlier
            correct_date = estimate_ramadhan(greg_start, target_year)
            correct_ans = correct_date  # YYYY-MM-DD
            
            # WRONG (0.0): moves later (common mistake)
            wrong_date = wrong_direction_estimate(greg_start, target_year)
            wrong_ans = wrong_date
            
            prompt_text = (
                f"{LTR}Ramadan moves roughly 11 days earlier each Gregorian year. "
                f"If Ramadan started on {clean_rtl(greg_start)}, "
                f"provide an estimate for the start of Ramadan in {target_year}.Think step by step. NO EXPLANATIONS.{POP}"
            )
            
            entry = {
                "input": prompt_text,
                "target_scores": {
                    correct_ans: 1.0,     # Line 1: Correct (earlier)
                    wrong_ans: 0.0        # Line 2: Wrong (later)
                }
            }
            prompts.append(entry)
            prompt_idx += 1
            
            if prompt_idx % 100 == 0:
                print(f"Generated {prompt_idx}/{MAX_COUNT} prompts...")
    
    print(f"✓ Final: {len(prompts)} prompts (exactly 2 targets each)")
    return prompts

# ---------------- SCORER (Date regex matching) ----------------
def score_accuracy(data: List[Dict]) -> tuple[List[Dict], float]:
    def exact_date_match(response: str, target: str) -> bool:
        """Match YYYY-MM-DD format exactly."""
        resp_date = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', response)
        target_date = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', target)
        return bool(resp_date and target_date and resp_date.group(1) == target_date.group(1))
    
    total_correct = 0
    for ex in data:
        response = ex.get("response", "").strip()
        scores = ex["target_scores"]
        
        # Check correct target first
        correct_key = next(k for k, v in scores.items() if v == 1.0)
        is_correct = exact_date_match(response, correct_key)
        
        ex["isModelResponseCorrect"] = is_correct
        if is_correct:
            total_correct += 1
    
    accuracy = (total_correct / len(data) * 100) if data else 0
    return data, accuracy

# ---------------- MAIN WORKFLOW ----------------
def main():
    print("=== RAMADHAN ESTIMATE PROMPTS (1000+, 2 TARGETS) ===\n")
    
    # 1. Generate prompts
    prompts = generate_prompts()
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"✓ {PROMPTS_FILE}")
    
    # 2. Test data (50% correct, 50% wrong responses)
    test_data = []
    for i, prompt in enumerate(prompts[:MAX_COUNT]):
        scores = prompt["target_scores"]
        correct_key = next(k for k, v in scores.items() if v == 1.0)
        wrong_key = next(k for k, v in scores.items() if v == 0.0)
        
        response = correct_key if i % 2 == 0 else wrong_key
        test_data.append({
            "input": prompt["input"],
            "response": response,
            "target_scores": scores
        })
    
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    print(f"✓ {TEST_FILE} ({len(test_data)} examples)")
    
    # 3. Score accuracy
    scored_data, accuracy = score_accuracy(test_data)
    with open(SCORED_FILE, "w", encoding="utf-8") as f:
        json.dump(scored_data, f, ensure_ascii=False, indent=4)
    
    print(f"\n=== RESULTS ===")
    print(f"✓ {SCORED_FILE}")
    print(f"Mock Accuracy: {accuracy:.1f}% ({'PASS' if accuracy > 50 else 'FAIL'})")
    print("Files ready for LLM testing!")

if __name__ == "__main__":
    main()