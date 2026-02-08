import sys
import subprocess
subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "--quiet"])

import os
import json
import re
import random
from datetime import date, datetime, timedelta, time
import pandas as pd
from typing import List, Dict
from global_config import MAX_COUNT,PLACES_FILE



# -------------------------
# Config
# -------------------------
IN_PLACES = PLACES_FILE  # optional input file
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]



# ---------------- CONFIG ----------------
MAX_COUNT = 1000
PROMPTS_FILE = "prompt22_shipping_businessdays_"+PLACES+".json"
TEST_FILE = "prompt22_shipping_businessdays_test.json"
SCORED_FILE = "prompt22_shipping_businessdays_scored.json"

# Work‑week structures (0=Mon ... 6=Sun)
WORKWEEK_STRUCTURES = {
    "Monday–Friday": [0, 1, 2, 3, 4],
    "Sunday–Thursday": [6, 0, 1, 2, 3],
    "Monday–Saturday": [0, 1, 2, 3, 4, 5]
}

# Expanded durations + bias weights (favor short durations)
DURATIONS = [1, 2, 3, 4, 5, 7, 10, 12, 14, 21, 30]
DURATION_WEIGHTS = {
    1: 10, 2: 10, 3: 9, 4: 8, 5: 7, 7: 6,
    10: 4, 12: 3, 14: 2, 21: 1, 30: 1
}

# Expanded cut‑off times (local 24h format)
CUTOFFS = ["10:00", "12:00", "14:00", "15:30", "16:00", "17:00", "18:00", "20:00"]


# ---------------- UTILITIES ----------------
def greg_str(g_date: date) -> str:
    return g_date.strftime("%Y-%m-%d")

def time_from_str(t: str) -> time:
    return datetime.strptime(t, "%H:%M").time()

def add_business_days(start_dt: datetime, business_days: int,
                      workweek: list[int], cutoff: time) -> datetime:
    """Add business days to start_dt, respecting cutoff and skipping non‑workdays."""
    current = start_dt

    # Apply cut‑off rule
    if current.time() > cutoff or current.weekday() not in workweek:
        # move to next business day 09:00
        current += timedelta(days=1)
        while current.weekday() not in workweek:
            current += timedelta(days=1)
        current = datetime.combine(current.date(), time(9, 0))

    days_added = 0
    while days_added < business_days:
        current += timedelta(days=1)
        if current.weekday() in workweek:
            days_added += 1

    return datetime.combine(current.date(), time(18, 0))


def weighted_sample_durations(k: int) -> list[int]:
    """Return k random durations biased toward shorter times."""
    weighted = []
    for d, w in DURATION_WEIGHTS.items():
        weighted += [d] * w
    return random.sample(weighted, k)


# ---------------- PROMPT GENERATION ----------------
def generate_prompts() -> List[Dict]:
    LTR, POP = "\u202a", "\u202c"
    prompts = []
    idx = 0

    print("--- BUSINESS‑DAY SHIPPING PROMPT GENERATION (weighted durations) ---")

    base_years = list(range(2020, 2026))
    order_times = ["08:10", "09:15", "11:45", "13:30", "15:10", "17:50", "19:05"]

    combinations = []
    for year in base_years:
        for month in [1, 3, 6, 9, 12]:
            for day in [5, 12, 19, 26]:
                combinations.append((year, month, day))

    random.seed(42)
    random.shuffle(combinations)

    for (year, month, day) in combinations:
        if idx >= MAX_COUNT:
            break
        try:
            base_dt = datetime(year, month, day)
        except ValueError:
            continue

        sample_durations = weighted_sample_durations(k=min(4, len(DURATIONS)))
        sample_cutoffs = random.sample(CUTOFFS, k=min(3, len(CUTOFFS)))
        sample_workweeks = random.sample(list(WORKWEEK_STRUCTURES.items()), k=2)
        sample_times = random.sample(order_times, k=min(3, len(order_times)))

        for duration in sample_durations:
            for ww_label, workdays in sample_workweeks:
                for cutoff_str in sample_cutoffs:
                    for order_t in sample_times:
                        if idx >= MAX_COUNT:
                            break

                        order_time = time_from_str(order_t)
                        cutoff = time_from_str(cutoff_str)
                        start_dt = datetime.combine(base_dt.date(), order_time)

                        correct_dt = add_business_days(start_dt, duration, workdays, cutoff)
                        wrong_dt = start_dt + timedelta(days=duration)
                        correct_ans = greg_str(correct_dt.date())
                        wrong_ans = greg_str(wrong_dt.date())

                        prompt = (
                            f"{LTR}I am ordering a package on [{greg_str(start_dt.date())}] "
                            f"at [{order_t}]. The shipping takes {duration} business days to arrive, "
                            f"bearing in mind that the work week follows a [{ww_label}] schedule. "
                            f"Crucially, the shipping company has a strict policy that any order placed "
                            f"after [{cutoff_str}] is not processed until the following business day. "
                            f"Please calculate the arrival day and provide the final answer as a Gregorian "
                            f"Date, ensuring that you apply the cut‑off rule before counting the days.Think step by step. NO EXPLANATIONS.{POP}"
                        )

                        entry = {
                            "input": prompt,
                            "target_scores": {
                                correct_ans: 1.0,
                                wrong_ans: 0.0
                            },
                            "metadata": {
                                "order_date": greg_str(start_dt.date()),
                                "order_time": order_t,
                                "duration_days": duration,
                                "work_week": ww_label,
                                "cutoff": cutoff_str,
                                "arrival_date_greg": correct_ans
                            }
                        }
                        prompts.append(entry)
                        idx += 1

                        if idx % 100 == 0:
                            print(f"Generated {idx} prompts ✓")

    print(f"✓ SUCCESS: {len(prompts)} weighted shipping prompts generated!")
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
        correct_key = None
        for k, v in scores.items():
            if v == 1.0:
                correct_key = k
                break
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
    print("=== SHIPPING BUSINESS‑DAYS × CUTOFF RULE DATASET ===\n")

    prompts = generate_prompts()
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"✓ {PROMPTS_FILE} ({len(prompts)} prompts)")

    # Mock evaluation set alternating correct/wrong
    test_data = []
    for i, p in enumerate(prompts[:MAX_COUNT]):
        scores = p["target_scores"]
        correct, wrong = None, None
        for k, v in scores.items():
            if v == 1.0:
                correct = k
            elif v == 0.0:
                wrong = k
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
    print(f"✓ {TEST_FILE} ({len(test_data)} tests)")

    scored, acc = score_accuracy(test_data)
    with open(SCORED_FILE, "w", encoding="utf-8") as f:
        json.dump(scored, f, ensure_ascii=False, indent=4)

    print(f"\n✓ {SCORED_FILE}")
    print(f"Mock accuracy baseline: {acc:.1f}% ✓ FULLY WORKING")
    print(
        f"Coverage: weighted durations × {len(WORKWEEK_STRUCTURES)} workweeks × {len(CUTOFFS)} cutoffs"
    )


if __name__ == "__main__":
    main()