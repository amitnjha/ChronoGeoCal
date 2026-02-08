#!/bin/bash

#source ~/myenv/bin/activate

model=$1

/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt1_gen_data_dst_iso_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt10_lord_howe_dst_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt11_greg_islamic_events_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt12_caracas_meeting_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt13_marquesas_time_difference_gen_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt14_multi_calendar_baker_kiribati_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt15_dst_calendar_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt16_hijri_hebrew_dates_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt17_ramadhan_estimate_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt18_birthdate_hijri_hebrew_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt19_holiday_deadline_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt2_gen_data_hebrew_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt20_hijri_subscription_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt21_hebrew_subscription_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt22_shipping_businessdays_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt23_flight_time_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt24_meeting_time_remote_places.json
#/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt25_sunrise_photo_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt3_gen_data_hebrew_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt4_gen_data_dst_end_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt5_chinese_lunar_time_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt6_gen_data_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt7_bangkok_meeting_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt8_chatham_dst_improved_remote_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt9_marquesas_event_remote_places.json

/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt1_gen_data_dst_iso_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt10_lord_howe_dst_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt11_greg_islamic_events_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt12_caracas_meeting_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt13_marquesas_time_difference_gen_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt14_multi_calendar_baker_kiribati_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt15_dst_calendar_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt16_hijri_hebrew_dates_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt17_ramadhan_estimate_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt18_birthdate_hijri_hebrew_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt19_holiday_deadline_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt2_gen_data_hebrew_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt20_hijri_subscription_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt21_hebrew_subscription_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt22_shipping_businessdays_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt23_flight_time_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt24_meeting_time_accessible_places.json
#/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt25_sunrise_photo_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt3_gen_data_hebrew_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt4_gen_data_dst_end_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt5_chinese_lunar_time_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt6_gen_data_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt7_bangkok_meeting_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt8_chatham_dst_improved_accessible_places.json
/home/llm-amitjha/myenv/bin/python3 evaluate_prompts.py $model prompts/prompt9_marquesas_event_accessible_places.json


# python evaluate_prompts.py Qwen/Qwen2.5-72B-Instruct  prompt2_gen_data_hijri.json
# python evaluate_prompts.py Qwen/Qwen2.5-72B-Instruct  prompt2_gen_data_hebrew.json
# python evaluate_prompts.py Qwen/Qwen2.5-72B-Instruct  prompt1_gen_data_dst_iso.json
# python evaluate_prompts.py Qwen/Qwen2.5-72B-Instruct  prompt3_gen_data_hebrew.json
# python evaluate_prompts.py Qwen/Qwen2.5-72B-Instruct  prompt10_lord_howe_dst.json
# python evaluate_prompts.py Qwen/Qwen2.5-72B-Instruct  prompt12_caracas_meeting.json
# python evaluate_prompts.py Qwen/Qwen2.5-72B-Instruct  prompt2_gen_data_greek.json
# python evaluate_prompts.py Qwen/Qwen2.5-72B-Instruct  prompt4_gen_data_dst_end.json
# python evaluate_prompts.py Qwen/Qwen2.5-72B-Instruct  prompt6_gen_data.json
# python evaluate_prompts.py Qwen/Qwen2.5-72B-Instruct  prompt7_bangkok_meeting.json
# python evaluate_prompts.py Qwen/Qwen2.5-72B-Instruct  prompt8_gen_data_dst_Chatham_Islands.json
# python evaluate_prompts.py Qwen/Qwen2.5-72B-Instruct  prompt9_marquesas_event.json
# python evaluate_prompts.py Qwen/Qwen2.5-72B-Instruct  prompt8_chatham_dst.json

# python evaluate_prompts.py CohereLabs/aya-expanse-32b  prompt2_gen_data_hijri.json
# python evaluate_prompts.py CohereLabs/aya-expanse-32b  prompt2_gen_data_hebrew.json
# python evaluate_prompts.py CohereLabs/aya-expanse-32b  prompt1_gen_data_dst_iso.json
# python evaluate_prompts.py CohereLabs/aya-expanse-32b  prompt3_gen_data_hebrew.json
# python evaluate_prompts.py CohereLabs/aya-expanse-32b  prompt10_lord_howe_dst.json
# python evaluate_prompts.py CohereLabs/aya-expanse-32b  prompt12_caracas_meeting.json
# python evaluate_prompts.py CohereLabs/aya-expanse-32b  prompt2_gen_data_greek.json
# python evaluate_prompts.py CohereLabs/aya-expanse-32b  prompt4_gen_data_dst_end.json
# python evaluate_prompts.py CohereLabs/aya-expanse-32b  prompt6_gen_data.json
# python evaluate_prompts.py CohereLabs/aya-expanse-32b  prompt7_bangkok_meeting.json
# python evaluate_prompts.py CohereLabs/aya-expanse-32b  prompt8_gen_data_dst_Chatham_Islands.json
# python evaluate_prompts.py CohereLabs/aya-expanse-32b  prompt9_marquesas_event.json
# python evaluate_prompts.py CohereLabs/aya-expanse-32b  prompt8_chatham_dst.json

# python evaluate_prompts.py meta-llama/Llama-3.3-70B-Instruct  prompt2_gen_data_hijri.json
# python evaluate_prompts.py meta-llama/Llama-3.3-70B-Instruct  prompt2_gen_data_hebrew.json
# python evaluate_prompts.py meta-llama/Llama-3.3-70B-Instruct  prompt1_gen_data_dst_iso.json
# python evaluate_prompts.py meta-llama/Llama-3.3-70B-Instruct  prompt3_gen_data_hebrew.json
# python evaluate_prompts.py meta-llama/Llama-3.3-70B-Instruct  prompt10_lord_howe_dst.json
# python evaluate_prompts.py meta-llama/Llama-3.3-70B-Instruct  prompt12_caracas_meeting.json
# python evaluate_prompts.py meta-llama/Llama-3.3-70B-Instruct  prompt2_gen_data_greek.json
# python evaluate_prompts.py meta-llama/Llama-3.3-70B-Instruct  prompt4_gen_data_dst_end.json
# python evaluate_prompts.py meta-llama/Llama-3.3-70B-Instruct  prompt6_gen_data.json
# python evaluate_prompts.py meta-llama/Llama-3.3-70B-Instruct  prompt7_bangkok_meeting.json
# python evaluate_prompts.py meta-llama/Llama-3.3-70B-Instruct  prompt8_gen_data_dst_Chatham_Islands.json
# python evaluate_prompts.py meta-llama/Llama-3.3-70B-Instruct  prompt9_marquesas_event.json
# python evaluate_prompts.py meta-llama/Llama-3.3-70B-Instruct  prompt8_chatham_dst.json

