import json
import sys
from collections import Counter


# All possible partial score values to always show in the summary
PARTIAL_SCORE_LEVELS = [0.0, 0.25, 0.5, 0.75, 1.0]


def calculate_accuracy(filepath: str) -> dict:
    """
    Calculate accuracy metrics from a JSON file containing scored predictions.

    Each entry in the JSON is expected to have at minimum:
        - "index": int   — position identifier
        - "score": float — partial score (e.g. 0.0, 0.25, 0.5, 0.75, 1.0)
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("Expected a non-empty JSON array.")

    total = len(data)
    scores = [item["score"] for item in data]

    # ── Core metrics ─────────────────────────────────────────────────────────
    exact_correct  = sum(1 for s in scores if s == 1.0)
    partial_scores = [s for s in scores if 0 < s < 1.0]
    fully_wrong    = sum(1 for s in scores if s == 0.0)

    mean_score      = sum(scores) / total
    strict_accuracy = exact_correct / total
    distribution    = Counter(scores)
    partial_counts  = {pval: distribution.get(pval, 0) for pval in PARTIAL_SCORE_LEVELS}

    indexed = sorted(data, key=lambda x: x["index"])

    sep = "=" * 55
    print(sep)
    print(f"  FILE: {filepath}")
    print(sep)

    print(f"\n  Total samples       : {total}")
    print(f"\n  Overall accuracy    : {mean_score:.4f}  ({mean_score*100:.2f}%)")
    print(f"  Strict accuracy     : {strict_accuracy:.4f}  ({strict_accuracy*100:.2f}%)")

    print(f"\n  Fully correct (1.0) : {exact_correct:>5}  ({exact_correct/total*100:.2f}%)")
    print(f"  Partial credit      : {len(partial_scores):>5}  ({len(partial_scores)/total*100:.2f}%)")
    for pval in PARTIAL_SCORE_LEVELS:
        count = partial_counts[pval]
        print(f"    ↳ score {pval:.2f}      : {count:>5}  ({count/total*100:.2f}%)")
    print(f"  Fully wrong   (0.0) : {fully_wrong:>5}  ({fully_wrong/total*100:.2f}%)")

    print(f"\n  Score Distribution:")
    for score_val in sorted(distribution):
        count = distribution[score_val]
        bar = "*" * int(count / total * 40)
        print(f"    {score_val:.2f}  {count:>5}  {bar}")

    print(f"\n{sep}")
    print(f"  Per-Index Accuracy (first 20 entries)")
    print(sep)
    print(f"  {'Index':>6}  {'Score':>6}  {'Result'}")
    print(f"  {'-'*6}  {'-'*6}  {'-'*15}")
    for item in indexed[:20]:
        label = (
            "✓ Correct" if item["score"] == 1.0 else
            "~ Partial" if item["score"] > 0    else
            "✗ Wrong"
        )
        print(f"  {item['index']:>6}  {item['score']:>6.2f}  {label}")
    if total > 20:
        print(f"  ... and {total - 20} more entries.")

    print(f"\n{sep}\n")

    return {
        "file":           filepath,
        "total":          total,
        "mean_score":     mean_score,
        "strict_accuracy":strict_accuracy,
        "exact_correct":  exact_correct,
        "partial_counts": partial_counts,
        "partial_count":  len(partial_scores),
        "fully_wrong":    fully_wrong,
        "distribution":   dict(distribution),
    }


def print_summary_table(all_results: list) -> None:
    """Print a one-row-per-file comparison table (no duplicate columns)."""

    # Columns: Overall | Correct(1.0) | partial scores... | Wrong(0.0)
    # "Correct" IS s=1.00 and "Wrong" IS s=0.00 — no need to repeat them.
    col_w   = 10   # column width
    name_w  = 38   # filename column width

    partial_headers = [f"s={pval:.2f}" for pval in PARTIAL_SCORE_LEVELS]
    all_cols        = ["Overall", "Strict", "✓ Correct"] + partial_headers + ["✗ Wrong"]
    total_w         = name_w + (col_w + 2) * len(all_cols)

    sep      = "═" * total_w
    thin_sep = "─" * total_w

    print(f"\n{sep}")
    print("  SUMMARY ACROSS ALL FILES")
    print(sep)

    # Header row
    header = f"  {'File':<{name_w}}"
    for col in all_cols:
        header += f"  {col:>{col_w}}"
    print(header)
    print(thin_sep)

    # Data rows
    for r in all_results:
        name = r["file"].split("/")[-1][:name_w]
        row  = f"  {name:<{name_w}}"
        row += f"  {r['mean_score']*100:>{col_w-1}.2f}%"
        row += f"  {r['strict_accuracy']*100:>{col_w-1}.2f}%"
        row += f"  {r['exact_correct']/r['total']*100:>{col_w-1}.2f}%"
        for pval in PARTIAL_SCORE_LEVELS:
            row += f"  {r['partial_counts'][pval]/r['total']*100:>{col_w-1}.2f}%"
        row += f"  {r['fully_wrong']/r['total']*100:>{col_w-1}.2f}%"
        print(row)

    # Average row
    n = len(all_results)
    print(thin_sep)
    avg  = f"  {'AVERAGE':<{name_w}}"
    avg += f"  {sum(r['mean_score'] for r in all_results)/n*100:>{col_w-1}.2f}%"
    avg += f"  {sum(r['strict_accuracy'] for r in all_results)/n*100:>{col_w-1}.2f}%"
    avg += f"  {sum(r['exact_correct']/r['total'] for r in all_results)/n*100:>{col_w-1}.2f}%"
    for pval in PARTIAL_SCORE_LEVELS:
        avg += f"  {sum(r['partial_counts'][pval]/r['total'] for r in all_results)/n*100:>{col_w-1}.2f}%"
    avg += f"  {sum(r['fully_wrong']/r['total'] for r in all_results)/n*100:>{col_w-1}.2f}%"
    print(avg)
    print(f"{sep}\n")


def print_combined_report(all_results: list) -> None:
    """Print a single aggregated report treating all files as one dataset."""
    sep         = "=" * 55
    total_all   = sum(r["total"] for r in all_results)
    exact_all   = sum(r["exact_correct"] for r in all_results)
    wrong_all   = sum(r["fully_wrong"] for r in all_results)
    partial_all = sum(r["partial_count"] for r in all_results)
    mean_all    = sum(r["mean_score"] * r["total"] for r in all_results) / total_all
    strict_all  = exact_all / total_all
    dist_all    = Counter()
    for r in all_results:
        dist_all.update(r["distribution"])
    partial_counts_all = {
        pval: sum(r["partial_counts"][pval] for r in all_results)
        for pval in PARTIAL_SCORE_LEVELS
    }

    print(sep)
    print("  COMBINED REPORT (ALL FILES)")
    print(sep)

    print(f"\n  Total samples       : {total_all}")
    print(f"\n  Overall accuracy    : {mean_all:.4f}  ({mean_all*100:.2f}%)")
    print(f"  Strict accuracy     : {strict_all:.4f}  ({strict_all*100:.2f}%)")

    print(f"\n  Fully correct (1.0) : {exact_all:>5}  ({exact_all/total_all*100:.2f}%)")
    print(f"  Partial credit      : {partial_all:>5}  ({partial_all/total_all*100:.2f}%)")
    for pval in PARTIAL_SCORE_LEVELS:
        count = partial_counts_all[pval]
        print(f"    ↳ score {pval:.2f}      : {count:>5}  ({count/total_all*100:.2f}%)")
    print(f"  Fully wrong   (0.0) : {wrong_all:>5}  ({wrong_all/total_all*100:.2f}%)")

    print(f"\n  Score Distribution:")
    for score_val in sorted(dist_all):
        count = dist_all[score_val]
        bar = "*" * int(count / total_all * 40)
        print(f"    {score_val:.2f}  {count:>5}  {bar}")

    print(f"\n{sep}\n")


DEFAULT_FILES = [
    "meta-llama_Llama-3.3-70B-Instruct_prompts_prompt2_gen_data_hebrew_accessible_places_with_accuracy_gemini_with_partial.json",
    "meta-llama_Llama-3.3-70B-Instruct_prompts_prompt2_gen_data_hijri_accessible_places_with_accuracy_gemini_with_partial.json",
    "meta-llama_Llama-3.3-70B-Instruct_prompts_prompt3_gen_data_hebrew_accessible_places_with_accuracy_gemini_with_partial.json",
]

if __name__ == "__main__":
    filepaths = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_FILES

    all_results = []
    for filepath in filepaths:
        try:
            result = calculate_accuracy(filepath)
            all_results.append(result)
        except FileNotFoundError:
            print(f"  [SKIPPED] File not found: {filepath}\n")
        except Exception as e:
            print(f"  [ERROR] {filepath}: {e}\n")

    if len(all_results) > 1:
        print_summary_table(all_results)
        print_combined_report(all_results)
