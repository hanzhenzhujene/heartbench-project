#!/usr/bin/env python3
"""Export relabel templates for HeartBench-v2 manual annotation."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from utils import PROJECT_ROOT, load_jsonl


DEFAULT_INPUT = PROJECT_ROOT / "benchmark" / "heartbench_v2_120.jsonl"
DEFAULT_OUTPUT = PROJECT_ROOT / "benchmark" / "heartbench_v2_relabel_blind_template.csv"


BLIND_FIELDNAMES = [
    "item_id",
    "case_A",
    "case_B",
    "annotator_id",
    "review_round",
    "annotated_gold_heart_worse",
    "annotated_gold_act_worse",
    "annotated_gold_case_A_heart_score",
    "annotated_gold_case_B_heart_score",
    "annotated_gold_case_A_act_score",
    "annotated_gold_case_B_act_score",
    "annotation_confidence",
    "needs_discussion",
    "notes",
]


ADJUDICATION_FIELDNAMES = [
    "item_id",
    "source_item_id",
    "benchmark_version",
    "family",
    "difficulty",
    "domain",
    "setting_type",
    "case_A",
    "case_B",
    "current_gold_heart_worse",
    "current_gold_act_worse",
    "current_gold_case_A_heart_score",
    "current_gold_case_B_heart_score",
    "current_gold_case_A_act_score",
    "current_gold_case_B_act_score",
    "annotator_id",
    "review_round",
    "annotated_gold_heart_worse",
    "annotated_gold_act_worse",
    "annotated_gold_case_A_heart_score",
    "annotated_gold_case_B_heart_score",
    "annotated_gold_case_A_act_score",
    "annotated_gold_case_B_act_score",
    "annotation_confidence",
    "needs_discussion",
    "notes",
]


def main():
    parser = argparse.ArgumentParser(description="Export HeartBench-v2 relabel template")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT), help="Input benchmark JSONL")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT), help="Output CSV path")
    parser.add_argument(
        "--include-current-labels",
        action="store_true",
        help="Include current heuristic labels and benchmark metadata for adjudication/internal review",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    items = load_jsonl(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ADJUDICATION_FIELDNAMES if args.include_current_labels else BLIND_FIELDNAMES

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            row = {
                "item_id": item["item_id"],
                "case_A": item["case_A"],
                "case_B": item["case_B"],
                "annotator_id": "",
                "review_round": "",
                "annotated_gold_heart_worse": "",
                "annotated_gold_act_worse": "",
                "annotated_gold_case_A_heart_score": "",
                "annotated_gold_case_B_heart_score": "",
                "annotated_gold_case_A_act_score": "",
                "annotated_gold_case_B_act_score": "",
                "annotation_confidence": "",
                "needs_discussion": "",
                "notes": "",
            }
            if args.include_current_labels:
                row.update(
                    {
                        "source_item_id": item.get("source_item_id", ""),
                        "benchmark_version": item.get("benchmark_version", ""),
                        "family": item["family"],
                        "difficulty": item["difficulty"],
                        "domain": item["domain"],
                        "setting_type": item["setting_type"],
                        "current_gold_heart_worse": item["gold_heart_worse"],
                        "current_gold_act_worse": item.get("gold_act_worse", ""),
                        "current_gold_case_A_heart_score": item.get("gold_case_A_heart_score", ""),
                        "current_gold_case_B_heart_score": item.get("gold_case_B_heart_score", ""),
                        "current_gold_case_A_act_score": item.get("gold_case_A_act_score", ""),
                        "current_gold_case_B_act_score": item.get("gold_case_B_act_score", ""),
                    }
                )
            writer.writerow(row)

    mode = "adjudication" if args.include_current_labels else "blind annotation"
    print(f"Wrote {mode} template to {output_path}")


if __name__ == "__main__":
    main()
