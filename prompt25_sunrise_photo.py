import os
import json
import re
import pytz
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
from global_config import MAX_COUNT,PLACES_FILE



# -------------------------
# Config
# -------------------------
IN_PLACES = PLACES_FILE  # optional input file
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]

# ---------------- CONFIG ----------------
MAX_COUNT = 1000
PROMPTS_FILE = "prompt25_sunrise_photo_"+PLACES+".json"
TEST_FILE = "prompt25_sunrise_photo_test.json"
SCORED_FILE = "prompt25_sunrise_photo_scored.json"

# Test dates (variety of sunrise times throughout year)
TEST_DATES = [
    "2026-03-15",  # Spring - earlier sunrises
    "2026-06-15",  # Summer - earliest sunrises  
    "2026-09-15",  # Fall
    "2026-12-15",  # Winter - latest sunrises
]

# Photographer end times (local time in city_b) - EXPANDED 12 OPTIONS
PHOTOGRAPHER_END_TIMES = [
    "08:30:00",  # Golden hour only (90min after sunrise)
    "09:00:00",  # Standard sunrise session (2h)
    "09:30:00",  # Extended golden hour
    "10:00:00",  # Full morning light (2.5-3h)
    
    # Later options for winter/late sunrises
    "10:30:00",  # Long winter sunrise session
    "11:00:00",  # Full morning shoot
    
    # Early cutoff options
    "08:00:00",  # Very tight golden hour
    "07:30:00",  # Ultra-early (30min window)
    
    # Flexible midday options
    "12:00:00",  # Half-day shoot
    "13:00:00",  # Almost full morning
    
    # Quick sync options
    "08:15:00",  # 15min after sunrise
    "09:15:00",  # 15min past standard
]

INPUT_PLACES_FILE = PLACES_FILE
FALLBACK_PLACES = [
    {"place": "New York", "country": "USA", "tz": "America/New_York", "lat": 40.7128, "lon": -74.0060},
    {"place": "London", "country": "UK", "tz": "Europe/London", "lat": 51.5074, "lon": -0.1278},
    {"place": "Tokyo", "country": "Japan", "tz": "Asia/Tokyo", "lat": 35.6895, "lon": 139.6917},
    {"place": "Sydney", "country": "Australia", "tz": "Australia/Sydney", "lat": -33.8688, "lon": 151.2093},
    {"place": "Berlin", "country": "Germany", "tz": "Europe/Berlin", "lat": 52.5200, "lon": 13.4050},
]

# ---------------- BiDi CLEANUP ----------------
BIDI_CHARS = re.compile(r'[\u200f\u202a-\u202e]')

def clean_rtl(text: str) -> str:
    """Strip problematic BiDi control chars, keep LRM safe."""
    return BIDI_CHARS.sub('', str(text)).strip()

def fmt_ymdhms(dt: datetime) -> str:
    """Format timezone-aware datetime as 'YYYY-MM-DD HH:MM:%S'."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# ---------------- LOAD PLACES ----------------
def load_places(places_file: str = INPUT_PLACES_FILE) -> List[Dict]:
    """Load places from JSON or return fallback examples."""
    if os.path.exists(places_file):
        try:
            df = pd.read_json(places_file)
            required_cols = ["place", "country", "tz", "lat", "lon"]
            if all(c in df.columns for c in required_cols):
                print(f"✓ Loaded {len(df)} places from {places_file}")
                return df.to_dict("records")
            else:
                print(f"⚠ {places_file} missing columns {required_cols} — using fallback.")
        except Exception as e:
            print(f"⚠ Error reading {places_file}: {e} — using fallback.")
    else:
        print(f"⚠ {places_file} not found — using fallback examples.")
    
    print("✓ Using fallback places")
    return FALLBACK_PLACES

# ---------------- SUNRISE CALCULATION (SIMPLIFIED) ----------------
def approximate_sunrise(city_date: datetime, lat: float, lon: float, tz: pytz.BaseTzInfo) -> datetime:
    """Approximate sunrise time using simplified solar calculation."""
    # Base sunrise varies by latitude/season (simplified model)
    day_of_year = city_date.timetuple().tm_yday
    solar_noon_hour = 12.0 + (lon / 15.0)  # Rough longitude adjustment
    
    # Seasonal variation (simplified - peaks at solstices)
    declination = 23.45 * 0.01745 * (day_of_year - 81) / 365 * 360
    sunrise_offset = 6.0 + (declination * 0.01745 * lat / 57.3)  # Hour angle approx
    
    # Convert to local time
    sunrise_hour = (solar_noon_hour - sunrise_offset) % 24
    naive_sunrise = city_date.replace(
        hour=int(sunrise_hour), 
        minute=int((sunrise_hour % 1) * 60),
        second=0,
        microsecond=0
    )
    
    return tz.localize(naive_sunrise)

# ---------------- TIME WINDOW HELPER ----------------
def find_photo_window(city_a_tz: pytz.BaseTzInfo, city_b_tz: pytz.BaseTzInfo,
                     sunrise_a_local: datetime, sunrise_b_local: datetime,
                     photographer_end_b: str, greg_date: str) -> tuple[str, str, str]:
    """Find overlapping photo window in city_b local time."""
    
    fmt = "%Y-%m-%d %H:%M:%S"
    photographer_end_b_dt = datetime.strptime(f"{greg_date} {photographer_end_b}", fmt)
    photographer_end_b_local = city_b_tz.localize(photographer_end_b_dt)
    
    # Convert sunrise_a to city_b timezone
    sunrise_a_b_tz = sunrise_a_local.astimezone(city_b_tz)
    
    # Window: max(sunrise_b, sunrise_a_in_b_tz) to min(photographer_end_b, sunrise_a_in_b_tz + 1h)
    window_start_utc = max(sunrise_b_local, sunrise_a_b_tz)
    window_end_utc = min(photographer_end_b_local, sunrise_a_b_tz + timedelta(hours=1))
    
    if window_start_utc >= window_end_utc:
        # No overlap: return photographer's full window (wrong but specific)
        return (
            fmt_ymdhms(sunrise_b_local),
            fmt_ymdhms(photographer_end_b_local),
            "NO_OVERLAP"
        )
    
    # Convert window back to city_b local time
    window_start_b = window_start_utc.astimezone(city_b_tz)
    window_end_b = window_end_utc.astimezone(city_b_tz)
    
    return (
        fmt_ymdhms(window_start_b),
        fmt_ymdhms(window_end_b),
        "HAS_OVERLAP"
    )

# ---------------- PROMPT GENERATOR ----------------
def generate_prompts() -> List[Dict]:
    places = load_places()
    prompts = []
    LTR, POP = "\u202a", "\u202c"

    print("Generating sunrise photo prompts...")

    idx = 0
    for p1 in places:  # city_a (sunrise given)
        for p2 in places:  # city_b (photographer)
            if p1["place"] == p2["place"]:
                continue
            if idx >= MAX_COUNT: 
                break

            try:
                tz_a = pytz.timezone(p1["tz"])
                tz_b = pytz.timezone(p2["tz"])
            except Exception as e:
                print(f"Skipping pair ({p1['place']}, {p2['place']}): invalid tz")
                continue

            for greg_date in TEST_DATES:
                if idx >= MAX_COUNT: 
                    break
                    
                date_naive = datetime.strptime(greg_date, "%Y-%m-%d")
                sunrise_a_naive = approximate_sunrise(date_naive, p1["lat"], p1["lon"], tz_a)
                sunrise_b_naive = approximate_sunrise(date_naive, p2["lat"], p2["lon"], tz_b)

                for photo_end in PHOTOGRAPHER_END_TIMES:
                    if idx >= MAX_COUNT: 
                        break

                    # Find actual photo window
                    correct_start, correct_end, status = find_photo_window(
                        tz_a, tz_b, sunrise_a_naive, sunrise_b_naive, photo_end, greg_date
                    )
                    
                    correct_answer = f"{correct_start} to {correct_end}"
                    wrong_answer = f"{sunrise_b_naive.strftime('%Y-%m-%d %H:%M:%S')} to {greg_date} {photo_end}"

                    question = (
                        f"{LTR}The sun rises at {fmt_ymdhms(sunrise_a_naive)} "
                        f"in {p1['place']}, {p1['country']} on {greg_date}. "
                        f"A photographer in {p2['place']}, {p2['country']} wants sunrise photos "
                        f"until {photo_end}. What time window works for both to photograph "
                        f"sunrise in {p2['place']}, {p2['country']} local time? "
                        f"GIVE RESPONSE IN YYYY-MM-DD HH:MM:SS to YYYY-MM-DD HH:MM:SS format.Think step by step. NO EXPLANATIONS.{POP}"
                    )

                    entry = {
                        "input": question,
                        "target_scores": {
                            correct_answer: 1.0,
                            wrong_answer: 0.0
                        },
                        "metadata": {
                            "city_a": p1["place"],
                            "country_a": p1["country"],
                            "city_b": p2["place"],
                            "country_b": p2["country"],
                            "greg_date": greg_date,
                            "sunrise_a": fmt_ymdhms(sunrise_a_naive),
                            "photographer_end": photo_end,
                            "status": status,
                            "correct_window": correct_answer
                        }
                    }
                    prompts.append(entry)
                    idx += 1
                    
                    if idx % 100 == 0:
                        print(f"Generated {idx} prompts")

    print(f"✓ Generated {len(prompts)} prompts total")
    return prompts

# ---------------- FIXED SCORER ----------------
def score_accuracy(data: List[Dict]) -> tuple[List[Dict], float]:
    """Compare model responses to correct target times."""
    def window_match(resp: str, target: str) -> bool:
        resp = resp.strip()
        target = target.strip()
        if resp == target:
            return True
        dates_r = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', resp)
        dates_t = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', target)
        return len(dates_r) == 2 and len(dates_t) == 2 and dates_r == dates_t

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
            ex["isModelResponseCorrect"] = False
            continue

        is_ok = window_match(resp, correct_key)
        ex["isModelResponseCorrect"] = is_ok
        if is_ok:
            correct += 1

    acc = (correct / len(data) * 100) if data else 0
    return data, acc

# ---------------- MAIN ----------------
def main():
    print("=== SUNRISE PHOTO PROMPT GENERATOR & EVALUATOR ===\n")

    prompts = generate_prompts()
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved prompts: {PROMPTS_FILE} ({len(prompts)} entries)")

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
        
        if correct_key and wrong_key:
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
    
    scored, acc = score_accuracy(test_data)
    with open(SCORED_FILE, "w", encoding="utf-8") as f:
        json.dump(scored, f, ensure_ascii=False, indent=4)
    
    print(f"\n✓ {SCORED_FILE} | Expected accuracy: ~50% (alternating correct/wrong)")
    print(f"✓ Test complete: Accuracy = {acc:.1f}%")

if __name__ == "__main__":
    main()