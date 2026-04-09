#!/bin/bash

source ~/myenv/bin/activate

prompt_1_types_files=(
    "prompt1_gen_data_dst_iso_accessible_places_gpt.json"
    "prompt1_gen_data_dst_iso_remote_places_gpt.json"
)

for file in "${prompt_1_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt1_accuracy.py "$file"
done

prompt_2_types_files=(
    "prompt2_gen_data_hebrew_accessible_places_gpt.json"
    "prompt2_gen_data_hebrew_remote_places_gpt.json"
    "prompt2_gen_data_hijri_accessible_places_gpt.json"
    "prompt2_gen_data_hijri_remote_places_gpt.json"
    "prompt22_shipping_businessdays_accessible_places_gpt.json"
    "prompt22_shipping_businessdays_remote_places_gpt.json"
    "prompt22_shipping_businessdays_scored_gpt.json"
    "prompt22_shipping_businessdays_test_gpt.json"
)

for file in "${prompt_2_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt2_accuracy.py "$file"
done

prompt_3_types_files=(
    "prompt3_gen_data_hebrew_accessible_places_gpt.json"
    "prompt3_gen_data_hebrew_remote_places_gpt.json"
    "prompt15_dst_calendar_accessible_places_gpt.json"
    "prompt15_dst_calendar_remote_places_gpt.json"
    "prompt16_hijri_hebrew_dates_accessible_places_gpt.json"
    "prompt16_hijri_hebrew_dates_remote_places_gpt.json"
    "prompt16_hijri_hebrew_dates_scored_gpt.json"
    "prompt16_hijri_hebrew_dates_test_gpt.json"
    "prompt17_ramadhan_estimate_accessible_places_gpt.json"
    "prompt17_ramadhan_estimate_remote_places_gpt.json"
    "prompt17_ramadhan_estimate_scored_gpt.json"
    "prompt17_ramadhan_estimate_test_gpt.json"
    "prompt18_birthdate_hijri_hebrew_accessible_places_gpt.json"
    "prompt18_birthdate_hijri_hebrew_remote_places_gpt.json"
    "prompt18_birthdate_hijri_hebrew_scored_gpt.json"
    "prompt18_birthdate_hijri_hebrew_test_gpt.json"
    "prompt19_holiday_deadline_accessible_places_gpt.json"
    "prompt19_holiday_deadline_remote_places_gpt.json"
    "prompt24_meeting_time_accessible_places_gpt.json"
    "prompt24_meeting_time_remote_places_gpt.json"
    "prompt24_meeting_time_scored_gpt.json"
    "prompt24_meeting_time_test_gpt.json"
)

for file in "${prompt_3_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt3_accuracy.py "$file"
done

prompt_4_types_files=(
    "prompt4_gen_data_dst_end_accessible_places_gpt.json"
    "prompt4_gen_data_dst_end_remote_places_gpt.json"
    "prompt5_chinese_lunar_time_accessible_places_gpt.json"
    "prompt5_chinese_lunar_time_remote_places_gpt.json"
    "prompt5_chinese_lunar_time_test_gpt.json"
    "prompt9_timezone_miscalculation_accessible_places_gpt.json"
    "prompt9_timezone_miscalculation_remote_places_gpt.json"
)

for file in "${prompt_4_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt4_accuracy.py "$file"
done

prompt_6_types_files=(
    "prompt6_gen_data_accessible_places_gpt.json"
    "prompt6_gen_data_remote_places_gpt.json"
)

for file in "${prompt_6_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt7_accuracy.py "$file"
done

prompt_7_types_files=(
    "prompt7_dynamic_location_meeting_accessible_places_gpt.json"
    "prompt7_dynamic_location_meeting_places_gpt.json"
    "prompt7_dynamic_location_meeting_remote_places_gpt.json"
)

for file in "${prompt_7_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt7_accuracy.py "$file"
done

prompt_8_types_files=(
    "prompt8_chatham_dst_accessible_places_gpt.json"
    "prompt8_chatham_dst_remote_places_gpt.json"
)

for file in "${prompt_8_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt8_accuracy.py "$file"
done

prompt_10_types_files=(
    "prompt10_lord_howe_dst_accessible_places_gpt.json"
    "prompt10_lord_howe_dst_remote_places_gpt.json"
)

for file in "${prompt_10_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt10_accuracy.py "$file"
done

prompt_11_types_files=(
    "prompt11_greg_events_accessible_places_gpt.json"
    "prompt11_greg_events_remote_places_gpt.json"
)

for file in "${prompt_11_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt11_accuracy.py "$file"
done

prompt_12_types_files=(
    "prompt12_caracas_meeting_accessible_places_gpt.json"
    "prompt12_caracas_meeting_remote_places_gpt.json"
)

for file in "${prompt_12_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt12_accuracy.py "$file"
done

prompt_13_types_files=(
    "prompt13_marquesas_time_difference_gen_accessible_places_gpt.json"
    "prompt13_marquesas_time_difference_gen_remote_places_gpt.json"
)

for file in "${prompt_13_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt13_accuracy.py "$file"
done

prompt_14_types_files=(
    "prompt14_multi_calendar_baker_kiribati_accessible_places_gpt.json"
    "prompt14_multi_calendar_baker_kiribati_remote_places_gpt.json"
)

for file in "${prompt_14_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt14_accuracy.py "$file"
done

prompt_20_types_files=(
    "prompt20_hijri_subscription_accessible_places_gpt.json"
    "prompt20_hijri_subscription_remote_places_gpt.json"
    "prompt20_hijri_subscription_scored_gpt.json"
    "prompt20_hijri_subscription_test_gpt.json"
    "prompt20_hijri_subscription_trial_accessible_places_gpt.json"
    "prompt20_hijri_subscription_trial_remote_places_gpt.json"
    "prompt20_hijri_subscription_trial_scored_gpt.json"
    "prompt20_hijri_subscription_trial_test_gpt.json"
    "prompt21_hebrew_subscription_accessible_places_gpt.json"
    "prompt21_hebrew_subscription_remote_places_gpt.json"
    "prompt21_hebrew_subscription_scored_gpt.json"
    "prompt21_hebrew_subscription_test_gpt.json"
)

for file in "${prompt_20_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt21_accuracy.py "$file"
done

prompt_23_types_files=(
    "prompt23_flight_time_accessible_places_gpt.json"
    "prompt23_flight_time_remote_places_gpt.json"
    "prompt23_flight_time_scored_gpt.json"
    "prompt23_flight_time_test_gpt.json"
)

for file in "${prompt_23_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt23_accuracy.py "$file"
done

prompt_25_types_files=(
    "prompt25_sunrise_photo_accessible_places_gpt.json"
    "prompt25_sunrise_photo_remote_places_gpt.json"
    "prompt25_sunrise_photo_scored_gpt.json"
    "prompt25_sunrise_photo_test_gpt.json"
)

for file in "${prompt_25_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt25_accuracy.py "$file"
done

prompt_26_types_files=(
    "prompt26_international_airports_gpt.json"
    "prompt26_international_airports_scored_gpt.json"
    "prompt26_international_airports_test_gpt.json"
)

for file in "${prompt_26_types_files[@]}"; do
    echo "Processing $file ..."
    python3 prompt26_accuracy.py "$file"
done

deactivate
