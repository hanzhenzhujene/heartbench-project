#!/usr/bin/env python3
"""Parse raw model outputs and extract structured fields."""

import json
import sys
from pathlib import Path
from collections import Counter

from utils import load_jsonl, save_jsonl, parse_json_output, validate_parsed_output, PROJECT_ROOT


def reparse_results(results: list[dict]) -> list[dict]:
    """Re-parse raw outputs from saved results."""
    reparsed = []
    for r in results:
        raw = r.get("raw_output", "")
        parsed = parse_json_output(raw)
        valid = parsed is not None and validate_parsed_output(parsed)

        updated = dict(r)
        if valid:
            updated["heart_worse"] = parsed["heart_worse"]
            updated["morally_worse"] = parsed["morally_worse"]
            updated["reason_focus"] = parsed["reason_focus"]
            updated["parse_success"] = True
        else:
            updated["heart_worse"] = None
            updated["morally_worse"] = None
            updated["reason_focus"] = None
            updated["parse_success"] = False

        reparsed.append(updated)
    return reparsed


def summarize_parse_results(results: list[dict]) -> dict:
    """Summarize parse success rates by model and condition."""
    by_key = {}
    for r in results:
        key = (r.get("model", "unknown"), r.get("condition", "unknown"))
        if key not in by_key:
            by_key[key] = {"total": 0, "parsed": 0, "repaired": 0, "failed": 0}
        by_key[key]["total"] += 1
        if r.get("parse_success"):
            if r.get("repair_success"):
                by_key[key]["repaired"] += 1
            else:
                by_key[key]["parsed"] += 1
        else:
            by_key[key]["failed"] += 1

    return by_key


def main():
    results_dir = PROJECT_ROOT / "results"

    for subdir in ["pilot", "main"]:
        combined_path = results_dir / subdir / "all_results.jsonl"
        if not combined_path.exists():
            continue

        print(f"\n{'='*60}")
        print(f"Parsing: {combined_path}")
        results = load_jsonl(combined_path)

        # Re-parse
        reparsed = reparse_results(results)

        # Save reparsed
        output_path = results_dir / subdir / "all_results_parsed.jsonl"
        save_jsonl(reparsed, output_path)
        print(f"Saved reparsed results to {output_path}")

        # Summary
        summary = summarize_parse_results(reparsed)
        print(f"\nParse summary:")
        for (model, cond), stats in sorted(summary.items()):
            total = stats["total"]
            parsed = stats["parsed"]
            repaired = stats["repaired"]
            failed = stats["failed"]
            print(f"  {model}/{cond}: {parsed}/{total} parsed, "
                  f"{repaired} repaired, {failed} failed "
                  f"({(parsed+repaired)/total*100:.1f}% success)")

        # Reason focus distribution
        rf_counts = Counter(
            r.get("reason_focus") for r in reparsed if r.get("parse_success")
        )
        print(f"\nReason focus distribution: {dict(sorted(rf_counts.items()))}")


if __name__ == "__main__":
    main()
