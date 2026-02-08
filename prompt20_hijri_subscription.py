# AUTO-INSTALL (Colab/Jupyter)
import sys
import subprocess
# Using hijri-converter as it provides accurate Umm al-Qura calculations
subprocess.check_call([sys.executable, "-m", "pip", "install", "hijri-converter", "pandas", "--quiet"])

import json
import datetime
import pandas as pd
import re
from typing import List, Dict
from datetime import date, timedelta
from hijri_converter import Hijri, Gregorian
from global_config import MAX_COUNT,PLACES_FILE
# -------------------------
# Config
# -------------------------
IN_PLACES = PLACES_FILE  # optional input file
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]


PROMPTS_FILE = f"prompt20_hijri_subscription_trial_{PLACES}.json"
TEST_FILE = f"prompt20_hijri_subscription_trial_test.json"
SCORED_FILE = f"prompt20_hijri_subscription_trial_scored.json"

def clean_prompt(text: str) -> str:
    """Clean ALL bidirectional and formatting characters from prompts."""
    bidi_chars = re.compile(r'[\u200e\u200f\u202a-\u202e\u2066-\u2069]')
    zero_width = re.compile(r'[\u200b-\u200d\uFEFF]')
    cleaned = bidi_chars.sub('', str(text))
    cleaned = zero_width.sub('', cleaned)
    return cleaned.strip()

def hijri_str(h: Hijri) -> str:
    # hijri-converter uses 1-based months
    months = ["Muharram", "Safar", "Rabi' al-awwal", "Rabi' al-thani",
              "Jumada al-awwal", "Jumada al-thani", "Rajab", "Sha'ban",
              "Ramadan", "Shawwal", "Dhu al-Qi'dah", "Dhu al-Hijjah"]
    return f"{h.day} {months[h.month - 1]} {h.year} AH"

def greg_str(g_date) -> str:
    if hasattr(g_date, 'year'):
        return f"{g_date.year}-{g_date.month:02d}-{g_date.day:02d}"
    return g_date.strftime("%Y-%m-%d")

# ---------------- LOGIC & VALIDATION ----------------

def get_billing_date(start_h: Hijri, trial_days: int, bill_no: int) -> date:
    """
    Calculates the Nth payment date.
    Logic: 
    1. Trial End is calculated.
    2. Payment N is targeted for (Trial_End_Month + N - 1).
    3. The day is the Anchor Day (Start Day).
    4. If the calculated date is BEFORE the trial end (e.g. catch-up for 1st bill),
       the payment happens ON the trial end date.
    """
    anchor_day = start_h.day
    
    # 1. Calculate actual Gregorian end of trial
    g_start = start_h.to_gregorian()
    g_trial_end = g_start + datetime.timedelta(days=trial_days)
    
    # 2. Convert trial end back to Hijri to find the "Active Month"
    # FIXED: Use Gregorian().to_hijri()
    h_trial_end = Gregorian(g_trial_end.year, g_trial_end.month, g_trial_end.day).to_hijri()
    
    # 3. Determine Month/Year of Nth Payment
    # We do NOT skip the month even if trial_end_day > anchor_day. 
    # That scenario results in an immediate 'catch-up' bill, counting as Bill #1.
    total_months_to_add = bill_no - 1
    
    current_month_total = h_trial_end.month + total_months_to_add
    
    # Calculate year offset and new month (1-based)
    year_offset = (current_month_total - 1) // 12
    final_year = h_trial_end.year + year_offset
    final_month = (current_month_total - 1) % 12 + 1
    
    # 4. Handle End-of-Month Clamping
    days_in_final_month = Hijri(final_year, final_month, 1).month_length()
    final_day = min(anchor_day, days_in_final_month)
    
    final_gregorian = Hijri(final_year, final_month, final_day).to_gregorian()

    # 5. Handle Catch-up Logic
    # If the calculated billing date is before the trial actually ended,
    # the bill occurs on the trial end date.
    if final_gregorian < g_trial_end:
        return g_trial_end
        
    return final_gregorian

def validate_billing_calculation(start_h: Hijri, trial_days: int, bill_no: int) -> Dict:
    """Validates the calculation."""
    try:
        correct_g = get_billing_date(start_h, trial_days, bill_no)
        
        # Sanity check
        greg_sane = 1900 <= correct_g.year <= 2100
        
        return {
            "calculation": True,
            "gregorian_sane": greg_sane,
            "correct_date": greg_str(correct_g),
        }
    except Exception as e:
        return {"calculation": False, "error": str(e)}

# ---------------- PARAMETERS ----------------
TRIAL_DURATIONS = [7, 14, 21, 30, 45, 60]
BILL_NUMBERS = [1, 2, 3, 4, 6, 9, 12]

# ---------------- GENERATE PROMPTS ----------------
def generate_prompts() -> List[Dict]:
    prompts: List[Dict] = []

    print("--- FIXED HIJRI SUBSCRIPTION PROMPTS (ANCHOR = START DAY) ---\n")
    
    hijri_years = [1443, 1444, 1445, 1446]
    hijri_months = list(range(1, 13))
    hijri_days = [1, 15, 20, 25, 30] 

    idx = 0
    skipped = 0
    
    for hy in hijri_years:
        for hm in hijri_months:
            for hd in hijri_days:
                if idx >= MAX_COUNT: break
                
                try:
                    month_len = Hijri(hy, hm, 1).month_length()
                    if hd > month_len: 
                        continue 
                    start_h = Hijri(hy, hm, hd)
                except ValueError:
                    continue

                start_h_str = hijri_str(start_h)

                for trial in TRIAL_DURATIONS:
                    for bill_no in BILL_NUMBERS:
                        if idx >= MAX_COUNT: break

                        # Generate WRONG Answer (Naive Gregorian logic)
                        start_g = start_h.to_gregorian()
                        naive_end = start_g + timedelta(days=trial)
                        naive_bill = naive_end + timedelta(days=(bill_no - 1) * 30)
                        wrong_ans = greg_str(naive_bill)

                        # Generate CORRECT Answer
                        validation = validate_billing_calculation(start_h, trial, bill_no)
                        
                        if not validation["calculation"] or not validation["gregorian_sane"]:
                            skipped += 1
                            continue

                        correct_ans = validation["correct_date"]
                        
                        if correct_ans == wrong_ans:
                            skipped += 1
                            continue

                        suffix = {1:'st', 2:'nd', 3:'rd'}.get(bill_no if bill_no < 20 else bill_no%10, 'th')
                        
                        base_prompt = (
                            f"I started a subscription on {clean_prompt(start_h_str)}. "
                            f"It has a {trial}-day free trial. After the trial, I am billed monthly "
                            f"on the same Hijri day. Please calculate the Gregorian date for the "
                            f"{bill_no}{suffix} payment. "
                            f"Give answer in YYYY-MM-DD format. "
                            f"Think step by step. NO EXPLANATIONS."
                        )
                        prompt = clean_prompt(base_prompt)

                        entry = {
                            "input": prompt,
                            "target_scores": {
                                correct_ans: 1.0,
                                wrong_ans: 0.0
                            },
                            "metadata": {
                                "start_hijri": start_h_str,
                                "trial_days": trial,
                                "bill_number": bill_no,
                                "logic": "Anchor Day"
                            }
                        }
                        prompts.append(entry)
                        idx += 1

                        if idx % 100 == 0:
                            print(f"Generated {idx}/{MAX_COUNT} prompts...")

    print(f"✓ {len(prompts)} prompts ✓ {skipped} skipped")
    return prompts

# ---------------- SCORER ----------------
def score_accuracy(data: List[Dict]) -> tuple[List[Dict], float]:
    def date_match(resp: str, target: str) -> bool:
        r = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', resp)
        t = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', target)
        return bool(r and t and r.group(1) == t.group(1))

    total_correct = 0
    for ex in data:
        resp = ex.get("response", "").strip()
        scores = ex.get("target_scores", {})
        
        correct_key = next((k for k, v in scores.items() if v == 1.0), None)
        
        if not correct_key:
            ex["isModelResponseCorrect"] = False
            continue

        is_correct = date_match(resp, correct_key)
        ex["isModelResponseCorrect"] = is_correct
        if is_correct:
            total_correct += 1

    acc = total_correct / len(data) * 100 if data else 0
    return data, acc

# ---------------- MAIN ----------------
def main():
    print("=== HIJRI SUBSCRIPTION GEN (FIXED LOGIC) ===\n")
    
    # Verification Cases
    print("Verification:")
    
    # Case 1: 1 Jumada al-thani 1443, 7 day trial, 4th Payment
    # Expected: 2022-04-02 (1 Ramadan 1443)
    c1 = get_billing_date(Hijri(1443, 6, 1), 7, 4)
    print(f"  Case 1 (1 Jumada II, 7d trial, 4th pay) -> {c1} [{'PASS' if str(c1)=='2022-04-02' else 'FAIL'}]")

    # Case 2: 15 Safar 1443, 30 day trial, 2nd Payment
    # Expected: 2021-11-20 (15 Rabi II 1443)
    c2 = get_billing_date(Hijri(1443, 2, 15), 30, 2)
    print(f"  Case 2 (15 Safar, 30d trial, 2nd pay) -> {c2} [{'PASS' if str(c2)=='2021-11-20' else 'FAIL'}]")
    print("")

    prompts = generate_prompts()
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"✓ {PROMPTS_FILE}")

    # Generate Test Set
    test_data = []
    for i, p in enumerate(prompts[:MAX_COUNT]):
        scores = p["target_scores"]
        correct = next((k for k, v in scores.items() if v == 1.0), None)
        wrong = next((k for k, v in scores.items() if v == 0.0), None)
        
        if correct and wrong:
            resp = correct if i % 2 == 0 else wrong
            test_data.append({
                "input": p["input"], 
                "response": resp, 
                "target_scores": scores,
                "metadata": p.get("metadata", {})
            })

    with open(TEST_FILE, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    print(f"✓ {TEST_FILE}")

    scored, acc = score_accuracy(test_data)
    with open(SCORED_FILE, "w", encoding="utf-8") as f:
        json.dump(scored, f, ensure_ascii=False, indent=4)
    
    print(f"\n✓ {SCORED_FILE}")
    print(f"Mock baseline: {acc:.1f}%")

if __name__ == "__main__":
    main()
