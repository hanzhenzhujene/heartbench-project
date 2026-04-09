#!/usr/bin/env python3
"""Analyze casewise heart scoring results."""

import argparse
import json
from collections import defaultdict

from score_casewise_results import aggregate_results, benchmark_configs
from stats_utils import bootstrap_diff_ci, mcnemar_test
from utils import PROJECT_ROOT, load_benchmark, load_jsonl


def summary_rows(aggregated: list) -> list:
    by_model_condition = defaultdict(list)
    for item in aggregated:
        by_model_condition[(item["model"], item["condition"])].append(item)

    rows = []
    for (model, condition), items in sorted(by_model_condition.items()):
        resolved = [item for item in items if item["heart_correct"] is not None]
        expected_resolved = [item for item in items if item["expected_heart_correct"] is not None]
        expected_confident = [item for item in items if item["expected_confident_correct"] is not None]
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
                "tie_rate": sum(1 for item in items if item["pair_pred"] is None) / len(items) if items else 0.0,
                "expected_accuracy": (
                    sum(item["expected_heart_correct"] for item in expected_resolved) / len(expected_resolved)
                    if expected_resolved else None
                ),
                "expected_n": len(expected_resolved),
                "expected_coverage": len(expected_resolved) / len(items) if items else 0.0,
                "expected_mean_margin": (
                    sum(item["expected_margin"] for item in items if item["expected_margin"] is not None)
                    / max(sum(1 for item in items if item["expected_margin"] is not None), 1)
                ),
                "expected_confident_accuracy": (
                    sum(item["expected_confident_correct"] for item in expected_confident) / len(expected_confident)
                    if expected_confident else None
                ),
                "expected_confident_n": len(expected_confident),
                "expected_confident_coverage": len(expected_confident) / len(items) if items else 0.0,
                "mean_margin": (
                    sum(item["margin"] for item in items if item["margin"] is not None)
                    / max(sum(1 for item in items if item["margin"] is not None), 1)
                ),
                "mean_case_a_score": (
                    sum(item["case_a_score"] for item in items if item["case_a_score"] is not None)
                    / max(sum(1 for item in items if item["case_a_score"] is not None), 1)
                ),
                "mean_case_b_score": (
                    sum(item["case_b_score"] for item in items if item["case_b_score"] is not None)
                    / max(sum(1 for item in items if item["case_b_score"] is not None), 1)
                ),
            }
        )
    return rows


def paired_analysis(aggregated: list, comparisons: list) -> dict:
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


def paired_analysis_expected(aggregated: list, comparisons: list) -> dict:
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
                if (
                    item_a["expected_heart_correct"] is None
                    or item_b["expected_heart_correct"] is None
                ):
                    continue
                correct_a.append(item_a["expected_heart_correct"])
                correct_b.append(item_b["expected_heart_correct"])

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
    results_root = analyze_benchmark.results_root
    results_path = PROJECT_ROOT / results_root / bench_name / "main" / "all_results.jsonl"
    if not results_path.exists():
        print(f"Missing casewise results for {bench_name}: {results_path}")
        return

    benchmark = load_benchmark(PROJECT_ROOT / bench_cfg["benchmark_file"])
    aggregated = aggregate_results(load_jsonl(results_path), benchmark)
    output = {
        "benchmark": bench_name,
        "summary_table": summary_rows(aggregated),
        "paired_analysis": paired_analysis(
            aggregated,
            [("C0", "C1"), ("C0", "C2"), ("C2", "C4"), ("C2", "C3")],
        ),
        "paired_analysis_expected": paired_analysis_expected(
            aggregated,
            [("C0", "C1"), ("C0", "C2"), ("C2", "C4"), ("C2", "C3")],
        ),
    }

    analysis_path = results_path.parent / "analysis.json"
    with open(analysis_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Saved casewise analysis to {analysis_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyze casewise results")
    parser.add_argument("--benchmark", type=str, default=None, help="Optional benchmark key")
    parser.add_argument(
        "--results-root",
        type=str,
        default="results/casewise_logit",
        help="Results root directory relative to project root",
    )
    args = parser.parse_args()

    analyze_benchmark.results_root = args.results_root

    configs = benchmark_configs()
    if args.benchmark:
        if args.benchmark not in configs:
            raise SystemExit(f"Unknown casewise benchmark: {args.benchmark}")
        configs = {args.benchmark: configs[args.benchmark]}

    for bench_name, bench_cfg in configs.items():
        analyze_benchmark(bench_name, bench_cfg)


if __name__ == "__main__":
    main()
