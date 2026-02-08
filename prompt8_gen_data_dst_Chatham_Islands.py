from global_config import MAX_COUNT,PLACES_FILE
import datetime
import pandas as pd
from zoneinfo import ZoneInfo

prompt_counter = 0


# Define locations and timezones
chatham_islands = "Chatham Islands"
chatham_tz = "Pacific/Chatham"

PLACES_FILE = PLACES_FILE
INPUT_PLACES_FILE = PLACES_FILE
PLACES=PLACES_FILE[:PLACES_FILE.index('.')]
OUTPUT_FILE = "prompt8_chatham_dst_improved_"+PLACES+".json"



df_places = pd.read_json(PLACES_FILE)

place_list = df_places[['place','tz']]

for idx, place2 in place_list.iterrows():
      location2 = place2['place']  # Example location for Event B
      location2_tz = place2['tz']

      # DST transition in Chatham Islands: September 28, 2025
      # Note: The time 2:45 AM is a symbolic "skipped" moment (clocks jump to 3:45 AM)
      dst_transition = datetime.datetime(2025, 9, 28, 2, 45, 0, tzinfo=ZoneInfo(chatham_tz))

      # Event B runs in Auckland from a given start to end time
      event_b_start = datetime.datetime(2025, 9, 28, 3, 0, 0, tzinfo=ZoneInfo(location2_tz))
      event_b_end = datetime.datetime(2025, 9, 28, 5, 0, 0, tzinfo=ZoneInfo(location2_tz))

      # Duration of Event A is the same as Event B
      event_a_duration = event_b_end - event_b_start

      # Event A ends exactly when Event B finishes, but in Chatham Islands local time
      event_a_end_chatham = event_b_end.astimezone(ZoneInfo(chatham_tz))

      # Calculate Event A start time in Chatham Islands time
      event_a_start_chatham = event_a_end_chatham - event_a_duration

      # Template for descriptive output
      template = """
      On {date_dst} in {chatham_islands}, clocks spring forward at {time_transition}.
      Event A starts before the transition and must finish exactly when Event B finishes in {location2}.
      Event B runs from {time_b_start} to {time_b_end} in {location2}.
      When does Event A actually start in {chatham_islands} time, accounting for the DST transition during its duration?
      """
      if prompt_counter < MAX_COUNT:
            # Print the scenario description
            print(template.format(
            date_dst=dst_transition.strftime("%Y-%m-%d"),
            chatham_islands=chatham_islands,
            time_transition="2:45 AM (skipped, jumps to 3:45 AM)",
            location2=location2,
            time_b_start=event_b_start.strftime("%H:%M"),
            time_b_end=event_b_end.strftime("%H:%M")
            ))
            prompt_counter += 1
            # Print the calculated start time and end time for Event A
            #print(f"Event A actually starts and ends in {chatham_islands} time at: {event_a_start_chatham:%Y-%m-%d %H:%M}) and {event_a_end_chatham:%Y-%m-%d %H:%M})
      else:
            exit()
  
            


