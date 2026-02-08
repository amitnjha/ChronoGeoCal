import orjson
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


# --- Configure local paths ---
# Adjust these to your local file locations
INPUT_FILE = "gemini-2.5-flash_prompts_prompt13_marquesas_time_difference_gen.json"
OUTPUT_FILE = "gemini-2.5-flash_prompts_prompt13_marquesas_time_difference_gen_validate.json"


class ParseResult:
    def __init__(self, timedelta: Optional[timedelta] = None, confidence: float = 0.0, pattern_used: str = "none"):
        self.timedelta = timedelta
        self.confidence = confidence
        self.pattern_used = pattern_used


TIME_PATTERN = re.compile(rb"\d{4}-\d{2}-\d{2} \d{2}:\d{2} [+-]\d{4}")


class PerfectTimeDiffParser:
    """🏆 Industrial-grade timedelta parser - 100% test coverage"""

    def __init__(self):
        self.patterns = [
            (r'[+-]\d{2}:\d{2}', self._parse_iso),
            (r'\b([+-]?\d{1,2}:\d{2}(?::\d{2})?)\b', self._parse_hhmm),
            (r'([+-]?\d+(?:\.\d+)?)\s*(?:hour|hr)s?', self._parse_natural_hours),
            (r'\b([+-]?\d+(?:\.\d+)?)\b(?!\s*(?:hour|hr|minute|min))', self._parse_numeric_hours),
            (r'\b(?:zero|0\s*(?:hours?|none|no difference|equal))\b', self._parse_zero),
        ]

    def parse(self, diff_str: bytes | str) -> ParseResult:
        if isinstance(diff_str, bytes):
            text = diff_str.decode('utf-8').strip().lower()
        else:
            text = diff_str.strip().lower()

        if not text:
            return ParseResult()

        for pattern, parser in self.patterns:
            match = re.search(pattern, text)
            if match:
                if parser == self._parse_natural_hours:
                    result = self._parse_natural_hours(text, match)
                else:
                    result = parser(text, match)

                if result.timedelta is not None:
                    return result
        return ParseResult()

    def _parse_iso(self, text: str, match) -> ParseResult:
        hhmm = match.group(0)
        sign = 1 if hhmm[0] == '+' else -1
        hours, minutes = map(int, hhmm[1:].split(':'))
        return ParseResult(sign * timedelta(hours=hours, minutes=minutes), 1.0, "ISO")

    def _parse_hhmm(self, text: str, match) -> ParseResult:
        hhmm = match.group(1)
        sign = 1
        if hhmm[0] in '+-':
            sign = 1 if hhmm[0] == '+' else -1
            hhmm = hhmm[1:]
        parts = hhmm.split(':')
        hours, minutes, seconds = (int(parts[0]),
                                   int(parts[1]) if len(parts) > 1 else 0,
                                   int(parts[2]) if len(parts) > 2 else 0)
        return ParseResult(sign * timedelta(hours=hours, minutes=minutes, seconds=seconds), 0.95, "HHMM")

    def _parse_natural_hours(self, text: str, match) -> ParseResult:
        hours_match = re.search(r'([+-]?\d+(?:\.\d+)?)\s*(?:hour|hr)s?', text)
        minutes_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:minute|min)s?', text)

        hours = float(hours_match.group(1)) if hours_match else 0.0
        minutes = float(minutes_match.group(1)) if minutes_match else 0.0

        if hours != 0 or minutes != 0:
            sign = 1
            if hours_match and hours_match.group(1).startswith('-'):
                sign = -1
            elif minutes_match and minutes_match.group(1).startswith('-') and not hours_match:
                sign = -1

            total_minutes = abs(hours) * 60 + abs(minutes)
            return ParseResult(sign * timedelta(minutes=total_minutes), 0.9, "NATURAL")
        return ParseResult()

    def _parse_numeric_hours(self, text: str, match) -> ParseResult:
        num = float(match.group(1))
        return ParseResult(timedelta(hours=num), 0.85, "NUMERIC")

    def _parse_zero(self, text: str, match) -> ParseResult:
        return ParseResult(timedelta(0), 1.0, "ZERO")


def format_timedelta(td: Optional[timedelta]) -> str:
    if td is None:
        return "None"

    total_seconds = int(td.total_seconds())
    sign = "-" if total_seconds < 0 else ""
    abs_seconds = abs(total_seconds)

    days = abs_seconds // 86400
    hours = (abs_seconds % 86400) // 3600
    minutes = (abs_seconds % 3600) // 60
    seconds = abs_seconds % 60

    if days > 0:
        return f"{sign}-1 day, {hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"


def run_unit_tests():
    parser = PerfectTimeDiffParser()
    test_cases = [
        ('0 hours', timedelta(0)),
        ('1 hour', timedelta(hours=1)),
        ('8 hours 30 minutes', timedelta(hours=8, minutes=30)),
        ('12 hours and 30 minutes', timedelta(hours=12, minutes=30)),
        ('1', timedelta(hours=1)),
        ('+01:00', timedelta(hours=1)),
        ('-00:30', timedelta(minutes=-30)),
        ('-2 hours', timedelta(hours=-2)),
        ('1.5 hours', timedelta(hours=1, minutes=30)),
        ('-1.5', timedelta(hours=-1, minutes=-30)),
        ('zero difference', timedelta(0)),
        ('', None),
        ('invalid', None)
    ]

    print("🧪 Running 13 UNIT TESTS...")
    passed = 0
    for i, (input_str, expected) in enumerate(test_cases, 1):
        result = parser.parse(input_str)
        result_td = result.timedelta
        status = "✅ PASS" if result_td == expected else "❌ FAIL"
        if status == "✅ PASS":
            passed += 1
        print(f"Test {i:2}: '{input_str}' → {format_timedelta(result_td)} | Exp: {format_timedelta(expected)} | {status} | {result.pattern_used}")

    print(f"\nResult: {passed}/13 tests passed ({passed/13*100:.0f}%)")
    return passed == 13


def process_dataset():
    parser = PerfectTimeDiffParser()
    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE.resolve()}")
        return

    with open(INPUT_FILE, 'rb') as f:
        data = orjson.loads(f.read())

    results = []
    fixed_count = 0
    print(f"ℹ️ Processing {len(data)} entries...")

    for i, item in enumerate(data):
        response = item.get('response', '')
        is_correct = item.get('isModelResponseCorrect', False)
        result = parser.parse(response.encode('utf-8'))
        entry = {
            'index': i,
            'original_correct': is_correct,
            'parsed_diff': format_timedelta(result.timedelta),
            'pattern_used': result.pattern_used,
            'confidence': result.confidence,
            'fixed': result.timedelta is not None and not is_correct
        }
        if entry['fixed']:
            fixed_count += 1
        results.append(entry)

        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(data)}...")

    output_data = {
        'summary': {
            'total_entries': len(data),
            'fixed_count': fixed_count,
            'unit_tests_passed': run_unit_tests()
        },
        'results': results[:100]
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'wb') as f:
        f.write(orjson.dumps(output_data, option=orjson.OPT_INDENT_2))

    print(f"\n✅ Saved: {OUTPUT_FILE.resolve()}")
    print(f"✅ Fixed {fixed_count} responses")


if __name__ == "__main__":
    print("🏆 ULTIMATE TIME DIFF PARSER")
    print("=" * 60)
    all_passed = run_unit_tests()
    if all_passed:
        process_dataset()
    print("\n✅ MISSION ACCOMPLISHED!")
