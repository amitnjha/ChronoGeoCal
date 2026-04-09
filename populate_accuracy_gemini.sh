#!/bin/bash

source ~/myenv/bin/activate

prompt_2_types_files=(
    "prompt2_gen_data_hebrew_accessible_places_gemini.json"
    "prompt2_gen_data_hebrew_remote_places_gemini.json"
    "prompt22_shipping_businessdays_accessible_places_gemini.json"
)

for file in "${prompt_2_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt2_accuracy.py "$file"
done

prompt_3_types_files=(
    "prompt15_dst_calendar_remote_places_gemini.json"
    "prompt18_birthdate_hijri_hebrew_accessible_places_gemini.json"
    "prompt19_holiday_deadline_remote_places_gemini.json"
    "prompt24_meeting_time_accessible_places_gemini.json"
)

for file in "${prompt_3_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt3_accuracy.py "$file"
done

prompt_4_types_files=(
    "prompt5_chinese_lunar_time_remote_places_gemini.json"
    "prompt5_chinese_lunar_time_scored_gemini.json"
    "prompt9_timezone_miscalculation_remote_places_gemini.json"
)

for file in "${prompt_4_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt4_accuracy.py "$file"
done

prompt_7_types_files=(
    "prompt7_dynamic_location_meeting_places_gemini.json"
    "prompt7_dynamic_location_meeting_remote_places_gemini.json"
)

for file in "${prompt_7_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt7_accuracy.py "$file"
done

prompt_12_types_files=(
    "prompt12_caracas_meeting_remote_places_gemini.json"
)

for file in "${prompt_12_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt12_accuracy.py "$file"
done

prompt_13_types_files=(
    "prompt13_marquesas_time_difference_gen_accessible_places_gemini.json"
)

for file in "${prompt_13_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt13_accuracy.py "$file"
done

prompt_20_types_files=(
    "prompt20_hijri_subscription_accessible_places_gemini.json"
    "prompt20_hijri_subscription_test_gemini.json"
    "prompt20_hijri_subscription_trial_remote_places_gemini.json"
)

for file in "${prompt_20_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt21_accuracy.py "$file"
done

prompt_23_types_files=(
    "prompt23_flight_time_scored_gemini.json"
)

for file in "${prompt_23_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt23_accuracy.py "$file"
done

prompt_26_types_files=(
    "prompt26_international_airports_gemini.json"
    "prompt26_international_airports_scored_gemini.json"
)

for file in "${prompt_26_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt26_accuracy.py "$file"
done

deactivate
