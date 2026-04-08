#!/usr/bin/env python3
"""Analyze corrected order-balanced results."""

import argparse
import json
from collections import defaultdict

from score_corrected_results import aggregate_results, benchmark_configs
from stats_utils import bootstrap_diff_ci, mcnemar_test
from utils import PROJECT_ROOT, load_benchmark, load_jsonl


def summary_rows(aggregated: list[dict]) -> list[dict]:
    by_model_condition = defaultdict(list)
    for item in aggregated:
        by_model_condition[(item["model"], item["condition"])].append(item)

    rows = []
    for (model, condition), items in sorted(by_model_condition.items()):
        resolved = [item for item in items if item["heart_correct"] is not None]
        order_avg = [item["order_avg_correct"] for item in items if item["order_avg_correct"] is not None]
        motive_rate = sum(
            1 for item in items if item["original_reason_focus"] == "motive"
        ) / max(sum(1 for item in items if item["original_reason_focus"] is not None), 1)
        outward_rate = sum(
            1 for item in items if item["original_reason_focus"] == "outward_act"
        ) / max(sum(1 for item in items if item["original_reason_focus"] is not None), 1)
        original_a_rate = sum(
            1 for item in items if item["original_raw_heart_worse"] == "A"
        ) / max(sum(1 for item in items if item["original_raw_heart_worse"] is not None), 1)
        swapped_a_rate = sum(
            1 for item in items if item["swapped_raw_heart_worse"] == "A"
        ) / max(sum(1 for item in items if item["swapped_raw_heart_worse"] is not None), 1)

        rows.append(
            {
                "model": model,
                "condition": condition,
                "resolved_accuracy": (
                    sum(item["heart_correct"] for item in resolved) / len(resolved)
                    if resolved else None
                ),
                "resolved_n": len(resolved),
                "coverage": len(resolved) / len(items) if items else 0.0,
                "agreement_rate": sum(1 for item in items if item["agreement"]) / len(items) if items else 0.0,
                "order_avg_accuracy": sum(order_avg) / len(order_avg) if order_avg else None,
                "motive_rate": motive_rate,
                "outward_rate": outward_rate,
                "original_a_rate": original_a_rate,
                "swapped_a_rate": swapped_a_rate,
            }
        )

    return rows


def paired_analysis(aggregated: list[dict], comparisons: list[tuple[str, str]]) -> dict:
    by_model_condition_item = defaultdict(dict)
    for item in aggregated:
        by_model_condition_item[(item["model"], item["condition"])][item["item_id"]] = item

    analysis = defaultdict(dict)
    models = sorted({item["model"] for item in aggregated})
    for model in models:
        for cond_a, cond_b in comparisons:
            items_a = by_model_condition_item[(model, cond_a)]
            items_b = by_model_condition_item[(model, cond_b)]
            common_ids = sorted(set(items_a) & set(items_b))
            correct_a = []
            correct_b = []
            for item_id in common_ids:
                item_a = items_a[item_id]
                item_b = items_b[item_id]
                if item_a["heart_correct"] is None or item_b["heart_correct"] is None:
                    continue
                correct_a.append(item_a["heart_correct"])
                correct_b.append(item_b["heart_correct"])

            label = f"{cond_a}_vs_{cond_b}"
            analysis[model][label] = {
                "n_items": len(correct_a),
                "mcnemar": mcnemar_test(correct_a, correct_b),
                "bootstrap_diff": bootstrap_diff_ci(correct_a, correct_b),
                "gain": (
                    (sum(correct_b) / len(correct_b)) - (sum(correct_a) / len(correct_a))
                    if correct_a else None
                ),
            }

    return analysis


def analyze_benchmark(bench_name: str, bench_cfg: dict) -> None:
    results_path = PROJECT_ROOT / "results_corrected" / bench_name / "main" / "all_results.jsonl"
    if not results_path.exists():
        print(f"Missing corrected results for {bench_name}: {results_path}")
        return

    benchmark = load_benchmark(PROJECT_ROOT / bench_cfg["benchmark_file"])
    aggregated = aggregate_results(load_jsonl(results_path), benchmark)
    rows = summary_rows(aggregated)
    analysis = paired_analysis(aggregated, [("C0", "C1"), ("C0", "C2"), ("C2", "C4"), ("C2", "C3")])

    output = {
        "benchmark": bench_name,
        "summary_table": rows,
        "paired_analysis": analysis,
    }
    analysis_path = results_path.parent / "analysis.json"
    with open(analysis_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Saved corrected analysis to {analysis_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyze corrected results")
    parser.add_argument("--benchmark", type=str, default=None, help="Optional benchmark key")
    args = parser.parse_args()

    configs = benchmark_configs()
    if args.benchmark:
        if args.benchmark not in configs:
            raise SystemExit(f"Unknown corrected benchmark: {args.benchmark}")
        configs = {args.benchmark: configs[args.benchmark]}

    for bench_name, bench_cfg in configs.items():
        analyze_benchmark(bench_name, bench_cfg)


if __name__ == "__main__":
    main()
