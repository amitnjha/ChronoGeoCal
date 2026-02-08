import orjson
import re
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from global_config import PROMPT_WITH_ACCURACY, PROMPT_WITH_INFER
import sys
import os

INPUT_FILE = "gpt-5.1_prompts_prompt14_multi_calendar_baker_kiribati.json"
OUTPUT_FILE = "gpt-5.1_prompts_prompt14_multi_calendar_baker_kiribati_validate.json"

# String regex pattern (matches example["response"] type) [web:2]
TIME_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} [+-]\d{4}")

def parse_utc(ts: bytes | str) -> datetime:
    if isinstance(ts, bytes): ts = ts.decode()
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def parse_local(dt_str: bytes | str) -> datetime:
    if isinstance(dt_str, bytes): dt_str = dt_str.decode()
    date_part, time_part, offset_part = dt_str.split()
    dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
    sign = 1 if offset_part[0] == '+' else -1
    offset = timezone(sign * timedelta(hours=int(offset_part[1:3]), minutes=int(offset_part[3:5])))
    return dt.replace(tzinfo=offset).astimezone(timezone.utc)

def replace_tbd(example: dict):
    """Replace 'TBD' with true/false based on time matching logic"""
    try:
        # Get ground truth UTC from Baker Island
        true_utc = parse_utc(example["answers"]["correct"]["baker"]["utc"])
        
        # Find last matching time pattern in response (now string-safe)
        matches = TIME_PATTERN.findall(example["response"])
        if matches:
            model_utc = parse_local(matches[-1])
            # Replace TBD → true/false
            example["isModelResponseCorrect"] = model_utc == true_utc
        else:
            # No matching time found → false
            example["isModelResponseCorrect"] = False
            
    except (KeyError, ValueError, IndexError):
        # Any parsing error → false
        example["isModelResponseCorrect"] = False

def main(input_path: str, output_path: str):
    path = Path(input_path)
    
    if not path.exists():
        raise FileNotFoundError(f"{path}: File not found")
    if path.stat().st_size == 0:
        raise ValueError(f"{path}: Empty file")
    
    # Fast binary JSON load
    with open(path, 'rb') as f:
        data = orjson.loads(f.read())
    
    if not isinstance(data, list):
        raise ValueError("Expected JSON array at root")
    
    # Process each example: replace "TBD" → true/false
    for example in data:
        replace_tbd(example)
    
    # Fast binary JSON dump with indent
    with open(output_path, 'wb') as f:
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
    
    # Count results
    correct_count = sum(1 for ex in data if ex["isModelResponseCorrect"])
    print(f"Processed {len(data)} examples → {correct_count} correct → {output_path}")

if __name__ == "__main__":
    INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE
    INPUT_FILE = INPUT_FILE[INPUT_FILE.index("/")+1:]
    OUTPUT_FILE = INPUT_FILE.replace(".json", "_validate.json")
    main(PROMPT_WITH_INFER + "/" + INPUT_FILE, PROMPT_WITH_ACCURACY + "/" + OUTPUT_FILE)
