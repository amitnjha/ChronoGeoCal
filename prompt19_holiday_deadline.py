import os
import json
import datetime
import pandas as pd
import re
from typing import List, Dict
from datetime import date, timedelta
from datetime import datetime as dt
from global_config import MAX_COUNT,PLACES_FILE



# -------------------------
# Config
# -------------------------
IN_PLACES = PLACES_FILE  # optional input file
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]

CURRENT_YEAR = 2026

PROMPTS_FILE = "prompt19_holiday_deadline_"+PLACES+".json"
TEST_FILE = "prompt19_holiday_deadline_test.json"
SCORED_FILE = "prompt19_holiday_deadline_scored.json"
# 2026 Holidays
from datetime import date

HOLIDAY_DATES = {
    # ISLAMIC (lunar, approx first day)
    "Ramadan": date(2026, 2, 17),
    "Laylat al-Qadr": date(2026, 3, 16),      # 27th Ramadan
    "Eid al-Fitr": date(2026, 3, 19),
    "Eid al-Adha": date(2026, 5, 26),
    "Islamic New Year": date(2026, 6, 16),    # Muharram 1 [web:47]
    "Ashura": date(2026, 6, 25),               # Muharram 10
    "Mawlid al-Nabi": date(2026, 8, 25),      # Prophet's Birthday

    # JEWISH
    "Passover": date(2026, 4, 1),             # First day
    "Shavuot": date(2026, 5, 21),
    "Rosh Hashanah": date(2026, 9, 11),
    "Yom Kippur": date(2026, 9, 20),
    "Sukkot": date(2026, 9, 25),
    "Shemini Atzeret": date(2026, 10, 2),
    "Simchat Torah": date(2026, 10, 3),
    "Hanukkah": date(2026, 12, 14),
    "Tu B'Shevat": date(2026, 2, 1),         # New Shevat [web:50]

    # CHRISTIAN (Western)
    "Epiphany": date(2026, 1, 6),
    "Ash Wednesday": date(2026, 2, 18),
    "Palm Sunday": date(2026, 4, 5),
    "Good Friday": date(2026, 3, 29),
    "Easter": date(2026, 4, 5),
    "Pentecost": date(2026, 5, 24),
    "Corpus Christi": date(2026, 6, 7),       # [web:47]
    "Christmas": date(2026, 12, 25),

    # HINDU
    "Holi": date(2026, 3, 4),                 # Spring festival [web:48]
    "Rama Navami": date(2026, 3, 26),
    "Raksha Bandhan": date(2026, 8, 28),       # [web:48]
    "Janmashtami": date(2026, 9, 4),
    "Ganesh Chaturthi": date(2026, 9, 13),
    "Navaratri": date(2026, 10, 19),
    "Diwali": date(2026, 11, 8),
    "Dussehra": date(2026, 10, 19),

    # BUDDHIST
    "Magha Puja": date(2026, 3, 3),
    "Songkran": date(2026, 4, 13),            # Thai New Year
    "Vesak": date(2026, 5, 1),               # Buddha's Birthday
    "Asalha Puja": date(2026, 7, 29),
    "Obon": date(2026, 8, 13),                # Ancestor festival [web:53]

    # SIKH
    "Vaisakhi": date(2026, 4, 14),
    "Gurpurab": date(2026, 11, 24),           # Guru Nanak Birthday approx

    # BAHÁ'Í
    "Naw-Rúz": date(2026, 3, 20),             # New Year
    "Ridván": date(2026, 4, 20),              # First day

    # ZOROASTRIAN
    "Nowruz": date(2026, 3, 20),              # Persian New Year

    # PAGAN/WICCAN
    "Imbolc": date(2026, 2, 1),
    "Ostara": date(2026, 3, 20),              # Spring equinox
    "Beltane": date(2026, 5, 1),
    "Litha": date(2026, 6, 21),               # Summer solstice [web:47]
    "Lammas": date(2026, 8, 1),
    "Mabon": date(2026, 9, 22),               # Autumn equinox
    "Samhain": date(2026, 10, 31),
    "Yule": date(2026, 12, 21),               # Winter solstice

    # UNIVERSAL
    "Chinese New Year": date(2026, 2, 17),
    "International Women's Day": date(2026, 3, 8),  # Global observance
}



BIDI_CHARS = re.compile(r'[\u200f\u202a-\u202e]')
def clean_rtl(text: str) -> str:
    return BIDI_CHARS.sub('', str(text)).strip()

def get_gregorian_date(dt_obj: date) -> str:
    return dt_obj.strftime("%Y-%m-%d")

def workday_countdown(holiday_date: date, business_days: int) -> date:
    current = holiday_date
    days_back = 0
    while days_back < business_days:
        current -= timedelta(days=1)
        if current.weekday() < 5:  # Mon-Fri
            days_back += 1
    return current

def naive_countdown(holiday_date: date, business_days: int) -> date:
    return holiday_date - timedelta(days=business_days)

# ---------------- GENERATE PROMPTS ----------------
def generate_prompts() -> List[Dict]:
    prompts = []
    LTR, POP = "\u202a", "\u202c"
    
    print("Generating prompts...")
    #business_days_list = [3, 5, 7, 10, 14, 20, 25, 30]

    business_days_list = [
    1, 2, 3, 4, 5,      # very short tasks (up to one workweek)
    7, 8, 9, 10,        # about 1–2 weeks
    12, 14, 15, 18, 20, # 2–4 weeks
    25, 30, 35, 40,     # 1–2 months
    45, 50, 60          # longer projects
    ]
    holidays = list(HOLIDAY_DATES.keys())
    
    idx = 0
    for holiday in holidays:
        holiday_date = HOLIDAY_DATES[holiday]
        for bdays in business_days_list:
            if idx >= MAX_COUNT: break
            
            correct_date_str = get_gregorian_date(workday_countdown(holiday_date, bdays))
            wrong_date_str = get_gregorian_date(naive_countdown(holiday_date, bdays))
            
            prompt = (
                f"{LTR}My client requires the project to be delivered exactly on the first day "
                f"of {holiday} this year. "
                f"The work requires {bdays} business days, and I take Saturday and Sunday off. "
                f"Please determine the date of that holiday, and then calculate the latest Gregorian date "
                f"I must start the work.Give answer in YYYY-MM-DD format.Think step by step. NO EXPLANATIONS.{POP}"
            )
            
            entry = {
                "input": prompt,
                "target_scores": {
                    correct_date_str: 1.0,
                    wrong_date_str: 0.0
                },
                "metadata": {
                    "holiday": holiday,
                    "holiday_date": get_gregorian_date(holiday_date),
                    "business_days": bdays
                }
            }
            prompts.append(entry)
            idx += 1
            
            if idx % 100 == 0:
                print(f"Generated {idx} prompts")
    
    print(f"✓ Generated {len(prompts)} prompts")
    return prompts

# ---------------- FIXED SCORER (No StopIteration) ----------------
def score_accuracy(data: List[Dict]) -> tuple[List[Dict], float]:
    def date_match(resp: str, target: str) -> bool:
        resp_date = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', resp)
        target_date = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', target)
        return bool(resp_date and target_date and resp_date.group(1) == target_date.group(1))
    
    total_correct = 0
    for ex in data:
        response = ex.get("response", "").strip()
        scores = ex.get("target_scores", {})
        
        # SAFE: Use get() with default, no next() iteration
        correct_key = None
        for k, v in scores.items():
            if v == 1.0:
                correct_key = k
                break
        
        if correct_key is None:
            print(f"WARNING: No 1.0 score found in {scores}")
            ex["isModelResponseCorrect"] = False
            continue
        
        is_correct = date_match(response, correct_key)
        ex["isModelResponseCorrect"] = is_correct
        if is_correct:
            total_correct += 1
    
    acc = total_correct / len(data) * 100 if data else 0
    return data, acc

# ---------------- MAIN (SAFE) ----------------
def main():
    print("=== FIXED HOLIDAY WORKBACK (No StopIteration) ===\n")
    
    prompts = generate_prompts()
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"✓ {PROMPTS_FILE}")
    
    # test_data = []
    # for i, p in enumerate(prompts[:MAX_COUNT]):
    #     scores = p["target_scores"]
        
    #     # SAFE EXTRACTION - no StopIteration
    #     correct_key = None
    #     wrong_key = None
    #     for k, v in scores.items():
    #         if v == 1.0:
    #             correct_key = k
    #         elif v == 0.0:
    #             wrong_key = k
        
    #     if not correct_key or not wrong_key:
    #         print(f"ERROR: Invalid scores in prompt {i}: {scores}")
    #         continue
            
    #     response = correct_key if i % 2 == 0 else wrong_key
    #     test_data.append({
    #         "input": p["input"],
    #         "response": response,
    #         "target_scores": scores,
    #         "metadata": p.get("metadata", {})
    #     })
    
    # print(f"✓ Created {len(test_data)} test cases")
    # with open(TEST_FILE, "w", encoding="utf-8") as f:
    #     json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    # scored, acc = score_accuracy(test_data)
    # with open(SCORED_FILE, "w", encoding="utf-8") as f:
    #     json.dump(scored, f, ensure_ascii=False, indent=4)
    
    # print(f"\n✓ {SCORED_FILE} | Accuracy: {acc:.1f}% ✓ FIXED")

if __name__ == "__main__":
    main()