#!/bin/bash

#source ~/myenv/bin/activate

model=$1
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt22_shipping_businessdays_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt9_timezone_miscalculation_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt12_caracas_meeting_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt6_gen_data_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt2_gen_data_hebrew_remote_places.json
#/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt23_flight_time_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt10_lord_howe_dst_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt1_gen_data_dst_iso_remote_places.json
#/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt25_sunrise_photo_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt5_chinese_lunar_time_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt8_chatham_dst_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt4_gen_data_dst_end_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt18_birthdate_hijri_hebrew_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt14_multi_calendar_baker_kiribati_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt15_dst_calendar_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt11_greg_events_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt21_hebrew_subscription_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt17_ramadhan_estimate_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt3_gen_data_hebrew_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt24_meeting_time_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt7_dynamic_location_meeting_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt19_holiday_deadline_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt13_marquesas_time_difference_gen_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt16_hijri_hebrew_dates_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt20_hijri_subscription_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt5_chinese_lunar_time_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt24_meeting_time_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt7_dynamic_location_meeting_accessible_places.json
#/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt25_sunrise_photo_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt9_timezone_miscalculation_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt18_birthdate_hijri_hebrew_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt11_greg_events_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt22_shipping_businessdays_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt13_marquesas_time_difference_gen_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt8_chatham_dst_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt10_lord_howe_dst_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt14_multi_calendar_baker_kiribati_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt16_hijri_hebrew_dates_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt20_hijri_subscription_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt1_gen_data_dst_iso_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt12_caracas_meeting_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt15_dst_calendar_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt17_ramadhan_estimate_accessible_places.json
#/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt23_flight_time_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt19_holiday_deadline_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt3_gen_data_hebrew_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt21_hebrew_subscription_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt6_gen_data_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt4_gen_data_dst_end_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt2_gen_data_hebrew_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt2_gen_data_hijri_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts_cot/prompt2_gen_data_hijri_accessible_places.json
