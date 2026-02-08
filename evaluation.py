#!/usr/bin/env python3
import json
import time
import argparse
from pathlib import Path

import pandas as pd
import requests
import re


def call_llm(
    api_url: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout: int = 60,
) -> str:
    """
    Call the LLM completion endpoint and return the text output.
    """
    system_content = (
        system_prompt.strip() + "\n\n"
        "You MUST follow these answer format rules strictly:\n"
        "- If the question says '(TRUE/FALSE)', answer with exactly one word: TRUE or FALSE.\n"
        "- If the question is an MCQ with options A, B, C, D, answer with exactly one letter: A, B, C, or D.\n"
        "Do NOT write explanations, reasoning, or any other text.\n"
        "Do NOT repeat the question.\n"
        "Your entire response must be a single token: TRUE, FALSE, A, B, C, or D."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
    }

    headers = {
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        print(data)
        if "choices" in data and data["choices"]:
            choice = data["choices"][0]

            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"].strip()

            if "text" in choice:
                return choice["text"].strip()

            return json.dumps(choice)

        return json.dumps(data)

    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"

def extract_answer(raw_output: str) -> str:
    """
    Extract the final answer token (True, False, A, B, C, or D) from the model output.
    Falls back to a trimmed raw output if no token is found.
    """
    if not isinstance(raw_output, str):
        raw_output = str(raw_output)

    # Find all occurrences of valid tokens, case-insensitive
    matches = re.findall(r'\b(True|False|A|B|C|D)\b', raw_output, flags=re.IGNORECASE)

    if not matches:
        return raw_output.strip()

    token = matches[-1]

    token_upper = token.upper()
    if token_upper in ["A", "B", "C", "D"]:
        return token_upper

    if token_upper == "TRUE":
        return "True"
    if token_upper == "FALSE":
        return "False"

    return token.strip()

def read_qna_file(path: Path, encoding: str) -> pd.DataFrame:
    """
    Read the QNA file (CSV or Excel) into a DataFrame, with configurable encoding.
    """
    if path.suffix.lower() in [".xls", ".xlsx"]:
        return pd.read_excel(path)
    else:
        try:
            return pd.read_csv(path, sep=None, engine="python", encoding=encoding)
        except UnicodeDecodeError:
            for enc in ["cp1252", "latin1"]:
                try:
                    print(f"[warn] Failed with encoding={encoding}, retrying with encoding={enc}")
                    return pd.read_csv(path, sep=None, engine="python", encoding=enc)
                except UnicodeDecodeError:
                    continue
            print("[warn] Falling back to latin1 with errors='replace'")
            return pd.read_csv(
                path,
                sep=None,
                engine="python",
                encoding="latin1",
                on_bad_lines="skip"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Run LLM inference on each Question in a QNA file and save to Excel."
    )
    parser.add_argument(
        "--input_csv",
        type=str,
        required=True,
        help="Path to input QNA CSV/Excel file.",
    )
    parser.add_argument(
        "--output_xlsx",
        type=str,
        default=None,
        help=(
            "Path to output Excel file. "
            "If not provided, it will be derived from input file name."
        ),
    )
    parser.add_argument(
        "--api_url",
        type=str,
        default="http://192.168.0.218:80/v1/completions",
        help="LLM HTTP endpoint (completions).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen2.5-72B-Instruct",
        help="Model name to send in the request.",
    )
    parser.add_argument(
        "--system_prompt",
        type=str,
        default="You are an expert historical reasoning model. Answer carefully and logically.",
        help="System prompt string.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="Optional sleep (seconds) between requests to avoid overloading the server.",
    )
    parser.add_argument(
        "--question_column",
        type=str,
        default="Question",
        help="Name of the column containing the question text.",
    )
    parser.add_argument(
        "--encoding",
        type=str,
        default="utf-8",
        help="Text encoding for CSV files (e.g. 'utf-8', 'cp1252', 'latin1').",
    )

    args = parser.parse_args()

    input_path = Path(args.input_csv)

    if args.output_xlsx is None:
        safe_stem = input_path.stem.replace(" ", "_")
        output_path = input_path.with_name(f"{safe_stem}_with_LLM.xlsx")
    else:
        output_path = Path(args.output_xlsx)

    print(f"Input file : {input_path}")
    print(f"Output file: {output_path}")
    print(f"API URL    : {args.api_url}")
    print(f"Model      : {args.model}")
    print(f"Encoding   : {args.encoding}")

    df = read_qna_file(input_path, encoding=args.encoding)

    if args.question_column not in df.columns:
        raise ValueError(
            f"Question column '{args.question_column}' not found in file. "
            f"Available columns: {list(df.columns)}"
        )

    llm_results = []

    for idx, row in df.iterrows():
        question_text = str(row[args.question_column])
        print(f"[{idx+1}/{len(df)}] Calling LLM for question: {question_text[:80]!r}...")

        raw_result = call_llm(
            api_url=args.api_url,
            model=args.model,
            system_prompt=args.system_prompt,
            user_prompt=question_text,
        )
        result = extract_answer(raw_result)
        llm_results.append(result)

        if args.sleep > 0:
            time.sleep(args.sleep)

    df["LLM_Result"] = llm_results

    # Save to Excel with all original columns + LLM_Result
    df.to_excel(output_path, index=False)
    print(f"Done. Saved results to: {output_path}")


if __name__ == "__main__":
    main()
