#!/usr/bin/env python3
"""
Validate DST/meeting LLM responses and produce a new JSON file with boolean
isModelResponseCorrect values.

Usage:
    python validate_dst_responses.py --file in.json
    python validate_dst_responses.py --file in.json --out out.json
"""

from pathlib import Path
import json
import re
import argparse
from datetime import datetime, timezone

# --- Utilities (same as earlier validator) -------------------------------

_OFFSET_RE = re.compile(r'([+-])(\d{2})(\d{2})\b')
def normalize_offset(s: str) -> str:
    return _OFFSET_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}:{m.group(3)}", s)

def parse_datetime_to_utc_seconds(s: str):
    if not isinstance(s, str):
        return None
    s = s.strip()
    s = s.replace('Z', '+00:00')
    s = normalize_offset(s)
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.astimezone(timezone.utc).timestamp())
    except Exception:
        fmts = [
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d %H:%M%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]
        for f in fmts:
            try:
                dt = datetime.strptime(s, f)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return int(dt.astimezone(timezone.utc).timestamp())
            except Exception:
                continue
    return None

def collect_strings(obj):
    out = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            out.extend(collect_strings(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(collect_strings(v))
    return out

def extract_json_block(text):
    m = re.search(r'```(?:json)?\s*(\{[\s\S]*\}|\[[\s\S]*\])\s*```', text, re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    for start_char in ('[', '{'):
        start_idx = text.find(start_char)
        if start_idx == -1:
            continue
        for end_idx in range(len(text)-1, start_idx, -1):
            if text[end_idx] not in (']', '}'):
                continue
            candidate = text[start_idx:end_idx+1]
            try:
                return json.loads(candidate)
            except Exception:
                continue
    return None

DATETIME_REGEX = re.compile(
    r'\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?(?:[ ]?[+-]\d{2}:?\d{2}|Z)?\b'
)
JD_REGEX = re.compile(r'\b2\d{5,6}\.\d+\b')  # crude JD matcher

EXPLANATION_KEYWORDS = [
    r"\bI\b", r"\bI've\b", r"\bI have\b", r"\bI've made\b", r"\bassum",
    r"\bAssumptions?\b", r"\bTo provide\b", r"\bI'll\b", r"\bwe assume\b",
    r"\bthis means\b", r"\btherefore\b", r"\bNote\b", r"\bexplain(ed)?\b"
]
EXPL_RE = re.compile('|'.join(EXPLANATION_KEYWORDS), re.IGNORECASE)

# --- Core logic ----------------------------------------------------------

def collect_canonical_utc_seconds(correct_block):
    utc_seconds = set()
    if not isinstance(correct_block, dict):
        return utc_seconds
    for loc, events in correct_block.items():
        if not isinstance(events, list):
            continue
        for ev in events:
            for side in ('start', 'end'):
                sideobj = ev.get(side, {})
                if isinstance(sideobj, dict):
                    utc_field = sideobj.get('utc')
                    if isinstance(utc_field, str):
                        sec = parse_datetime_to_utc_seconds(utc_field)
                        if sec is not None:
                            utc_seconds.add(sec)
                    greg = sideobj.get('gregorian') or sideobj.get('Gregorian')
                    if isinstance(greg, str):
                        sec = parse_datetime_to_utc_seconds(greg)
                        if sec is not None:
                            utc_seconds.add(sec)
                    jd = sideobj.get('jd') or sideobj.get('JD')
                    try:
                        if jd is not None:
                            jd_float = float(jd)
                            unix_sec = int((jd_float - 2440587.5) * 86400.0)
                            utc_seconds.add(unix_sec)
                    except Exception:
                        pass
    return utc_seconds

def extract_response_utc_seconds_and_jds(response_text, parsed_json=None):
    secs = set()
    jds = set()
    text_to_scan = ""
    try:
        if parsed_json is not None:
            text_to_scan = json.dumps(parsed_json) + "\n" + (response_text or "")
        else:
            text_to_scan = response_text or ""
    except Exception:
        text_to_scan = response_text or ""

    for m in DATETIME_REGEX.finditer(text_to_scan):
        dtstr = m.group(0)
        sec = parse_datetime_to_utc_seconds(dtstr)
        if sec is not None:
            secs.add(sec)

    for m in JD_REGEX.finditer(text_to_scan):
        try:
            jds.add(float(m.group(0)))
        except Exception:
            continue

    if parsed_json is not None:
        def walk(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)
            elif isinstance(obj, (int, float)):
                if 2_000_000 < obj < 3_000_000:
                    jds.add(float(obj))
            elif isinstance(obj, str):
                try:
                    f = float(obj)
                    if 2_000_000 < f < 3_000_000:
                        jds.add(f)
                except Exception:
                    pass
        walk(parsed_json)

    return secs, jds

def has_explanatory_prose(response_text, parsed_json):
    if not response_text:
        return False
    if not EXPL_RE.search(response_text):
        return False
    json_block = extract_json_block(response_text)
    if json_block is None:
        return True
    m = re.search(r'```(?:json)?\s*(\{[\s\S]*\}|\[[\s\S]*\])\s*```', response_text, re.IGNORECASE)
    if m:
        remaining = (response_text[:m.start()] + response_text[m.end():]).strip()
        if re.search(r'[A-Za-z]', remaining):
            return True
        return False
    start = min((idx for idx in (response_text.find('['), response_text.find('{')) if idx != -1), default=None)
    end = max((response_text.rfind(']'), response_text.rfind('}')))
    if start is None or end is None or start >= end:
        return True
    remaining = (response_text[:start] + response_text[end+1:]).strip()
    if re.search(r'[A-Za-z]', remaining):
        return True
    return False

def decide_truth(canonical_secs, resp_secs, canonical_jds, resp_jds, has_explain, threshold=0.75):
    if has_explain:
        return False
    if canonical_secs:
        matched = 0
        for cs in canonical_secs:
            if any(abs(cs - rs) <= 1 for rs in resp_secs):
                matched += 1
        frac = matched / len(canonical_secs)
        return frac >= threshold
    if canonical_jds:
        matched = 0
        for cj in canonical_jds:
            if any(abs(cj - rj) < 1e-6 for rj in resp_jds):
                matched += 1
        frac = matched / len(canonical_jds)
        return frac >= threshold
    return False

# --- File validation -----------------------------------------------------

def validate_and_write(input_path: Path, output_path: Path, threshold=0.75):
    raw = input_path.read_text(encoding="utf-8")
    data = json.loads(raw)

    top_is_list = isinstance(data, list)
    items = data if top_is_list else [data]

    report = []
    for idx, item in enumerate(items):
        prompt = item.get("input", "")
        correct = item.get("answers", {}).get("correct")
        response_text = item.get("response", "") or ""
        prev = item.get("isModelResponseCorrect")

        canonical_secs = collect_canonical_utc_seconds(correct) if correct else set()
        canonical_jds = set()
        if correct:
            for loc_events in correct.values():
                for ev in loc_events:
                    for side in ('start','end'):
                        sd = ev.get(side, {})
                        if sd:
                            jd = sd.get('jd') or sd.get('JD')
                            try:
                                if jd is not None:
                                    canonical_jds.add(float(jd))
                            except Exception:
                                pass

        parsed_json = extract_json_block(response_text)
        resp_secs, resp_jds = extract_response_utc_seconds_and_jds(response_text, parsed_json=parsed_json)
        explained = has_explanatory_prose(response_text, parsed_json)

        truth = decide_truth(canonical_secs, resp_secs, canonical_jds, resp_jds, explained, threshold=threshold)
        item["isModelResponseCorrect"] = bool(truth)

        report.append({
            "index": idx,
            "canonical_utc_count": len(canonical_secs),
            "response_utc_count": len(resp_secs),
            "canonical_jd_count": len(canonical_jds),
            "response_jd_count": len(resp_jds),
            "explanatory_prose_detected": bool(explained),
            "final_decision": bool(truth),
            "previous_value": prev
        })

    out_data = items if top_is_list else items[0]
    output_path.write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # print short summary
    print(f"Validation complete. Wrote {output_path}. Summary:")
    for r in report:
        print(f" - item[{r['index']}]: canonical_utcs={r['canonical_utc_count']} "
              f"resp_utcs={r['response_utc_count']} canonical_jds={r['canonical_jd_count']} "
              f"resp_jds={r['response_jd_count']} explain={r['explanatory_prose_detected']} "
              f"-> decision={r['final_decision']} (was {r['previous_value']})")

# --- CLI -----------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Validate DST meeting LLM outputs and save a new file.")
    ap.add_argument("--file", "-f", required=True, help="input JSON file")
    ap.add_argument("--out", "-o", required=False, help="output JSON file (default: <input>.validated.json)")
    ap.add_argument("--threshold", type=float, default=0.75, help="matching threshold (default 0.75)")
    args = ap.parse_args()

    inp = Path(args.file)
    if not inp.exists():
        raise SystemExit(f"Input file not found: {inp}")
    out = Path(args.out) if args.out else inp.with_suffix('.validated.json')
    validate_and_write(inp, out, threshold=args.threshold)

if __name__ == "__main__":
    main()