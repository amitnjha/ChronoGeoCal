import json
from dateutil import parser
from datetime import timezone
import sys
from global_config import PROMPT_WITH_ACCURACY, PROMPT_WITH_INFER

def update_correctness(example):
    response = example.get("response")
    target_scores = example.get("target_scores", {})

    is_correct = False

    try:
        # Parse response and make it timezone-aware (UTC if naive)
        response_dt = parser.parse(response)
        if response_dt.tzinfo is None:
            response_dt = response_dt.replace(tzinfo=timezone.utc)
        else:
            response_dt = response_dt.astimezone(timezone.utc)

        # Compare response to each key in target_scores
        for key, score in target_scores.items():
            try:
                if response in key:
                    is_correct = float(score) == 1.0
                    break
                    
                key_dt = parser.parse(key)
                if key_dt.tzinfo is None:
                    key_dt = key_dt.replace(tzinfo=timezone.utc)
                else:
                    key_dt = key_dt.astimezone(timezone.utc)

                # If the datetimes match exactly (allow 1 sec tolerance)
                if abs((response_dt - key_dt).total_seconds()) < 1:
                    # Only True if score == 1.0
                    is_correct = float(score) == 1.0
                    break  # stop checking after first match
            except Exception as e:
                print('exception 1 from prompt2_accuracy.py', e)
                continue
    except Exception as e:
        print('exception 2 from prompt2_accuracy.py', e)
        pass

    example["isModelResponseCorrect"] = is_correct
    return example

#def main():
if __name__ == "__main__":
    if len(sys.argv) > 1:
        INPUT_FILE = f"{PROMPT_WITH_INFER}/{sys.argv[1]}"
        OUTPUT_FILE = f"{PROMPT_WITH_ACCURACY}/{sys.argv[1].replace('.json', '_with_accuracy.json')}"
        #OUTPUT_FILE = sys.argv[2]
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = update_correctness(data)
    elif isinstance(data, list):
        data = [update_correctness(item) for item in data]
    else:
        raise ValueError("Unsupported JSON structure")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)