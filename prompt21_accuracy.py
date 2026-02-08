import json
from dateutil import parser
from datetime import timezone
import sys
from global_config import PROMPT_WITH_ACCURACY, PROMPT_WITH_INFER

def within_window(target_str, response_str, window_days=7):
    try:
        target_date = parser.parse(target_str)
        response_date = parser.parse(response_str)
        diff = abs((response_date - target_date).days)
        #print(f"Target date: {target_date}, Response date: {response_date}, Difference in days: {diff}")
        return diff <= window_days
    except Exception:
        return False

def update_correctness(example):
    response = example.get("response")
    target_scores = example.get("target_scores", {})

    is_correct = False

    try:
        # Parse response and make it timezone-aware (UTC if naive)
        # Compare response to each key in target_scores
        for key, score in target_scores.items():
            try:
                #print(f"Comparing response '{response}' to key '{key}' with score {score}")
                if key == response or within_window(key, response):
                    is_correct = float(score) == 1.0
                    if is_correct:
                        break
                else:
                    is_correct = False
            except Exception:
                print('exception 1')
                continue
    except Exception:
        print('exception 2')
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
