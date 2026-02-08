from hijridate import Gregorian
import pandas as pd
import json
from itertools import permutations
import datetime
import pytz
from global_config import MAX_COUNT,PLACES_FILE



prompt_counter = 0

# Convert Gregorian date to Hijri calendar
gregorian_date = Gregorian(2002, 4, 1)
hijri_date = gregorian_date.to_hijri()
print(hijri_date.year)
print(hijri_date.month_name(language='ar'))
print(hijri_date.day)

#print(hijri_date.date_string(language = 'ar'))
# Load places from JSON file
df_places = pd.read_json(PLACES_FILE)
#place_list = df_places['place'].tolist()
place_list = df_places[['place','tz']]

# Define times to generate prompts for
times = ["10:01", "14:01"]

# Generate prompts
prompts = []

for idx, place1 in place_list.iterrows():
    for idx, place2 in place_list.iterrows():
        for time in times:
            if place2['place'] != place1['place'] and prompt_counter < MAX_COUNT:
                prompt_counter+=1
                greg_date_time = datetime.datetime(gregorian_date.year, gregorian_date.month, gregorian_date.day, int(time.split(':')[0]), int(time.split(':')[1]), 0)
                TZ_PLACE1 = pytz.timezone(place1['tz'])
                TZ_PLACE2 = pytz.timezone(place2['tz'])
                t_place1 = TZ_PLACE1.localize(greg_date_time)
                t_place2 = t_place1.astimezone(TZ_PLACE2)

                prompt = {
                    "input": f"Today is {hijri_date.month_name(language='ar')} 18 {hijri_date.year}. "
                            f"It is currently {time} in {place1['place']}. "
                            f"What time and date is it in {place2['place']} in Gregorian Calendar? GIVE RESPONSE IN YYYY-MM-DD HH:MI:SS format.Think step by step. NO EXPLANATIONS.",
                    "target_scores": {
                        f"{t_place2}": 1.0,
                        f"{t_place1}": 0.0
                    }
                }
                if len(prompt.get("target_scores")) == 1:
                    #print("Warning: prompt target_scores is badly formed: skipping", t_place2, t_place1)
                    continue
                prompts.append(prompt)
            elif prompt_counter == MAX_COUNT:
                PLACES=PLACES_FILE[:PLACES_FILE.index('.')]
                OUTPUT_FILE = "prompt2_gen_data_hijri_" + PLACES + ".json"

                # Save prompts to JSON file
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(prompts, f, ensure_ascii=False, indent=2)

                print(f"Generated {len(prompts)} prompts")
                print(f"Saved to {OUTPUT_FILE}")

                # Print first prompt as example
                if prompts:
                    print("\nExample prompt:")
                    print(json.dumps(prompts[0], ensure_ascii=False, indent=2))
                exit()
            else:
                continue






