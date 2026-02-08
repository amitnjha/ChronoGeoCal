import datetime
from zoneinfo import ZoneInfo

# --- Locations and timezones ---
location1, tz1 = "Beijing", "Asia/Shanghai"
location2, tz2 = "New York", "America/New_York"

# --- Predefined Chinese New Year dates and zodiac years (YYYY: (MM, DD, zodiac)) ---
chinese_new_years = {
    2024: (2, 10, "Dragon"),
    2025: (1, 29, "Snake"),
    2026: (2, 17, "Horse"),
    2027: (2, 6, "Goat"),
    2028: (1, 26, "Monkey"),
    2029: (2, 13, "Rooster"),
    2030: (2, 3, "Dog"),
}

# --- Current year ---
current_year = datetime.datetime.now().year

# --- Get Chinese New Year date ---
if current_year in chinese_new_years:
    month, day, zodiac = chinese_new_years[current_year]
else:
    raise ValueError(f"Chinese New Year date not defined for {current_year}")

# --- Convert to datetime in Beijing timezone ---
lunar_new_year_dt = datetime.datetime(current_year, month, day, tzinfo=ZoneInfo(tz1))

# --- Event A: New Year's Eve in Beijing ---
event_a_start = lunar_new_year_dt - datetime.timedelta(days=1)
event_a_start = event_a_start.replace(hour=20, minute=0, second=0)
duration_a = datetime.timedelta(hours=4)
event_a_end = event_a_start + duration_a

# --- Event B: Same moment in New York ---
event_b_start = event_a_start.astimezone(ZoneInfo(tz2))
event_b_end = event_b_start + duration_a  # same duration

# --- Check if events span the same Gregorian calendar date (approximation for lunar) ---
span_same_date_location1 = event_a_start.date() == event_a_end.date()
span_same_date_location2 = event_b_start.date() == event_b_end.date()

# --- Template ---
template = f"""
Chinese Lunar New Year {current_year} begins on {lunar_new_year_dt.strftime('%Y-%m-%d')} (Year of the {zodiac}).

Event A in {location1} (Beijing) starts at {event_a_start.strftime('%H:%M')} on New Year's Eve and lasts 4 hours.
Event B in {location2} (New York) starts at the exact moment Event A starts in New York time and lasts 4 hours.

Do both events span the same calendar dates at their respective locations?
"""

print(template)
print(f"Event A in {location1} spans the same calendar date: {span_same_date_location1}")
print(f"Event B in {location2} spans the same calendar date: {span_same_date_location2}")
