import os
import json
import datetime
import pandas as pd
import re
from typing import List, Dict
from datetime import date, timedelta
from global_config import MAX_COUNT,PLACES_FILE
import hijridate


# -------------------------
# Config
# -------------------------
IN_PLACES = PLACES_FILE  # optional input file
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]

# ---------------- CONFIG ----------------
CURRENT_YEAR, CURRENT_MONTH, CURRENT_DAY = 2025, 12, 29

PROMPTS_FILE = "prompt16_hijri_hebrew_dates_"+PLACES+".json"
TEST_FILE = "prompt16_hijri_hebrew_dates_test.json"
SCORED_FILE = "prompt16_hijri_hebrew_dates_scored.json"

# BiDi cleanup
BIDI_CHARS = re.compile(r'[\u200f\u202a-\u202e]')
def clean_rtl(text: str) -> str:
    return BIDI_CHARS.sub('', str(text)).strip() if isinstance(text, str) else str(text)

def greg_to_hijri(g_year: int, g_month: int, g_day: int) -> tuple[int, int, int]:
    gregorian_date = hijridate.Gregorian(g_year, g_month, g_day)
    hijri_date = gregorian_date.to_hijri()
    #print(hijri_date)
    return hijri_date.year, hijri_date.month, hijri_date.day

# ---------------- HIJRI CONVERSION ----------------
# def greg_to_hijri(g_year: int, g_month: int, g_day: int) -> tuple[int, int, int]:
#     if g_month <= 2: g_year -= 1; g_month += 12
#     A = g_year // 100; B = 2 - A + A//4
#     JD = int(365.25*(g_year+4716)) + int(30.6001*(g_month+1)) + g_day + B - 1524
#     hijri_days = JD - 1948084
#     h_year = int(hijri_days // 354.36667) + 1
#     rem = hijri_days % 354.36667
#     h_month = int(rem / 29.53056) + 1
#     h_day = int(rem % 29.53056) + 1
#     return h_year, h_month, h_day

HIJRI_MONTHS = ["Muharram", "Safar", "Rabi' al-awwal", "Rabi' al-thani", "Jumada al-awwal", 
                "Jumada al-thani", "Rajab", "Sha'ban", "Ramadan", "Shawwal", 
                "Dhu al-Qi'dah", "Dhu al-Hijjah"]

def get_hijri_date(g_year: int, g_month: int, g_day: int) -> str:
    y, m, d = greg_to_hijri(g_year, g_month, g_day)
    #return f"{d} {HIJRI_MONTHS[m-1]} {y} AH"
    return f"{y}-{m}-{d}"

# ---------------- HEBREW CONVERSION ----------------
def is_leap_hebrew_year(year: int) -> bool:
    return ((year * 7 + 1) % 19) < 7

def hebrew_year_length(year: int) -> int:
    base = 353
    if is_leap_hebrew_year(year): base += 30
    if year % 19 in [0,3,6,11,14,17]: base += 1
    if year % 19 in [2,5,8,13,16]: base += 1
    return base

def greg_to_jd(g_year: int, g_month: int, g_day: int) -> int:
    if g_month <= 2: g_year -= 1; g_month += 12
    A = g_year // 100; B = 2 - A + A//4
    return int(365.25*(g_year+4716)) + int(30.6001*(g_month+1)) + g_day + B - 1524

MONTH_DAYS = [30,29,29,30,29,30,29,30,30,29,30,29,29]  # Adar II=13
def greg_to_hebrew(g_year: int, g_month: int, g_day: int) -> tuple[int, int, int]:
    jd = greg_to_jd(g_year, g_month, g_day)
    h_epoch = greg_to_jd(3761, 1, 1)
    days = jd - h_epoch
    h_year = 3761
    while days >= hebrew_year_length(h_year): 
        days -= hebrew_year_length(h_year)
        h_year += 1
    leap = is_leap_hebrew_year(h_year)
    m_days = MONTH_DAYS.copy()
    if leap: m_days[12] = 29
    h_month, h_day = 7, 1  # Tishri
    while days > m_days[h_month-1]:
        days -= m_days[h_month-1]
        h_month += 1
        if h_month > 13: h_month = 1
    h_day = days
    return h_year, h_month, h_day

HEBREW_MONTHS = ["Nisan", "Iyar", "Sivan", "Tamuz", "Av", "Elul", "Tishrei", "Cheshvan", 
                 "Kislev", "Tevet", "Shevat", "Adar", "Adar II"]
def get_hebrew_date(g_year: int, g_month: int, g_day: int) -> str:
    y, m, d = greg_to_hebrew(g_year, g_month, g_day)
    return f"{d} {HEBREW_MONTHS[m-1]} {y}"

def get_gregorian_date(y: int, m: int, d: int) -> str:
    return f"{y}-{m:02d}-{d:02d}"

# ---------------- GENERATE PROMPTS (EXACTLY TWO TARGETS) ----------------
def generate_prompts() -> List[Dict]:
    prompts = []
    base = date(CURRENT_YEAR, CURRENT_MONTH, CURRENT_DAY)
    LTR, POP, LRM = "\u202a", "\u202c", "\u200e"
    print("--- GENERATING 1000 PROMPTS (2 targets each) ---\n")
    for offset in range(-500, 500):
        if len(prompts) >= MAX_COUNT: break
        tgt = base + timedelta(days=offset)
        greg = get_gregorian_date(tgt.year, tgt.month, tgt.day)
        hijri_correct = get_hijri_date(tgt.year, tgt.month, tgt.day)
        heb_correct = get_hebrew_date(tgt.year, tgt.month, tgt.day)
        
        # CORRECT (1.0)
        correct_ans = f"Hijri: {clean_rtl(hijri_correct)}, Hebrew: {clean_rtl(heb_correct)}"
        correct_ans = f"{clean_rtl(hijri_correct)}"
        
        # DISTRACTOR (0.0) - swapped calendars
        distractor_ans = f"Hijri: {clean_rtl(heb_correct)}, Hebrew: {clean_rtl(hijri_correct)}"
        
        #prompt = f"{LTR}Today is {clean_rtl(greg)}.{LRM} What is the current date in the Hijri calendar and the Hebrew calendar?{POP}"
        prompt = f"{LTR}Today is {clean_rtl(greg)}.{LRM} What is the current date in the Hijri calendar?Think step by step. NO EXPLANATIONS.{POP}"
        
        # EXACTLY TWO LINES IN target_scores
        entry = {
            "input": prompt,
            "target_scores": {
                correct_ans: 1.0,      # Line 1: Correct
                distractor_ans: 0.0    # Line 2: Distractor
            }
        }
        prompts.append(entry)
        if len(prompts) % 100 == 0: print(f"Generated {len(prompts)}...")
    print(f"✓ {len(prompts)} prompts (2 targets each)")
    return prompts

# ---------------- SCORER ----------------
def score_accuracy(data: List[Dict]) -> tuple[List[Dict], float]:
    def fuzzy_match(r: str, t: str) -> bool:
        r_lower, t_lower = r.lower().strip(), t.lower().strip()
        if t_lower in r_lower or r_lower in t_lower: return True
        wr, wt = set(r_lower.split()), set(t_lower.split())
        return len(wr & wt) / max(len(wt), 1) >= 0.8

    total_correct = 0
    for ex in data:
        resp = ex.get("response", "").strip()
        scores = ex["target_scores"]
        # Check correct first (1.0), then distractor (0.0)
        is_correct = fuzzy_match(resp, next(k for k,v in scores.items() if v==1.0))
        ex["isModelResponseCorrect"] = is_correct
        if is_correct: total_correct += 1
    acc = total_correct / len(data) * 100
    return data, acc

# ---------------- MAIN ----------------
def main():
    print("=== HIJRI+HEBREW (2 TARGETS/PROMPT) ===\n")
    
    # Generate prompts (exactly 2 targets each)
    prompts = generate_prompts()
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"✓ {PROMPTS_FILE} ({len(prompts)} prompts, 2 targets each)")
    
    # Test data (50/50 correct/wrong)
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
    
    # Score
    scored, acc = score_accuracy(test_data)
    with open(SCORED_FILE, "w", encoding="utf-8") as f:
        json.dump(scored, f, ensure_ascii=False, indent=4)
    
    print(f"\n✓ {SCORED_FILE}")
    print(f"Mock Accuracy: {acc:.1f}% (PASS/FAIL: {'PASS' if acc>50 else 'FAIL'})")
    print("Ready for LLM evaluation!")

if __name__ == "__main__":
    main()