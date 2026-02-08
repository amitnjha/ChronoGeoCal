import heniautos as ha
import pandas as pd
import datetime
import pytz
from global_config import MAX_COUNT,PLACES_FILE



prompt_counter = 0


#prompt_string = 

# gregorian_date = dates.GregorianDate(2002, 4, 1)

year_431 = ha.athenian_festival_calendar(-430, name_as=ha.MonthNameOptions.GREEK)
#year_431 = ha.athenian_festival_calendar(1430, name_as=ha.MonthNameOptions.GREEK)
months_431 = ha.by_months(year_431)
#print(year_431)
#print(months_431)

# for i in range(13):
#     #print(months_431[i][0])
#     print(months_431[i][0].year, months_431[i][0].month_name, 1)
#     print(ha.as_gregorian(year_431[i]))




df_places = pd.read_json(PLACES_FILE)

place_list = df_places[['place','tz']]


for idx, place1 in place_list.iterrows():
    for idx, place2 in place_list.iterrows():
        #print(place1['place'], place1['tz'])
        for i in range(1,13):
            heniautos_date = f"{months_431[i][0].year} {months_431[i][0].month_name} 1"
            greg_date = ha.as_gregorian(months_431[i][0])
            time = "10:01"
            template = """
                        {{
                        "input" : "Today is {}. It is currently {} in {}. What time and date and time is it in {} in Gregorian Calendar?",
                        "target_scores": {{
                            "{}": 1.0,
                            "{}": 0.0
                            }}
                        }},
                    """ 
            template = """
                        {{
                        "input" : "Today is {}. It is currently {} in {}. What date is it in {} in Gregorian Calendar?",
                        "target_scores": {{
                            "{}": 1.0,
                            "{}": 0.0
                            }}
                        }},
                    """ 
            if place2['place'] != place1['place'] and prompt_counter < MAX_COUNT:
                format_code = "BCE %Y-%b-%d"
                #greg_date_time = datetime.datetime(greg_date, 10, 1, 0)
                #greg_date_time = datetime.datetime(greg_date.year, greg_date.month, greg_date.day, 10, 1, 0)
                parsed_date = datetime.datetime.strptime(greg_date, format_code)
                greg_date_time = datetime.datetime(parsed_date.year, parsed_date.month, parsed_date.day, 10, 1, 0)

                TZ_PLACE1 = pytz.timezone(place1['tz'])
                TZ_PLACE2 = pytz.timezone(place2['tz'])
                t_place1 = TZ_PLACE1.localize(greg_date_time)
                prompt1 = template.format(heniautos_date, time, place1['place'], place2['place'], t_place1.astimezone(TZ_PLACE2),t_place1)
                print(prompt1)
                time = "2:01"
                #greg_date_time = datetime.datetime(greg_date.year, greg_date.month, greg_date.day, 2, 1, 0)
                parsed_date = datetime.datetime.strptime(greg_date, format_code)
                greg_date_time = datetime.datetime(parsed_date.year, parsed_date.month, parsed_date.day, 10, 1, 0)

                
                TZ_PLACE1 = pytz.timezone(place1['tz'])
                TZ_PLACE2 = pytz.timezone(place2['tz'])
                t_place1 = TZ_PLACE1.localize(greg_date_time)
                prompt1 = template.format(heniautos_date, time, place1['place'], place2['place'], t_place1.astimezone(TZ_PLACE2),t_place1)
                print(prompt1)
                prompt_counter += 1
            elif prompt_counter == MAX_COUNT:
                exit()
            else:
                continue



