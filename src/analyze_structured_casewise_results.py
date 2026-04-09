#!/usr/bin/env python3
"""Analyze structured HeartBench-v2 results."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict

from score_structured_casewise_results import aggregate_results, benchmark_configs, load_results_rows
from stats_utils import (
    bootstrap_diff_ci,
    bootstrap_numeric_diff_ci,
    mcnemar_test,
    wilcoxon_signed_rank,
)
from utils import PROJECT_ROOT, load_benchmark


def summary_rows(aggregated: list[dict]) -> list[dict]:
    by_model_condition = defaultdict(list)
    for item in aggregated:
        by_model_condition[(item["model"], item["condition"])].append(item)

    rows = []
    for (model, condition), items in sorted(by_model_condition.items()):
        target_items = [item for item in items if item["dissociation_target"]]
        rows.append(
            {
                "model": model,
                "condition": condition,
                "heart_resolved_accuracy": (
                    sum(item["heart_correct"] for item in items if item["heart_correct"] is not None)
                    / max(sum(1 for item in items if item["heart_correct"] is not None), 1)
                ),
                "heart_resolved_n": sum(1 for item in items if item["heart_correct"] is not None),
                "heart_tie_rate": sum(1 for item in items if item["pred_heart_worse"] == "tie") / len(items) if items else 0.0,
                "act_pair_accuracy": (
                    sum(item["act_correct"] for item in items if item["act_correct"] is not None)
                    / max(sum(1 for item in items if item["act_correct"] is not None), 1)
                ),
                "act_pair_n": sum(1 for item in items if item["act_correct"] is not None),
                "act_tie_rate": sum(1 for item in items if item["pred_act_worse"] == "tie") / len(items) if items else 0.0,
                "mean_aligned_heart_margin": (
                    sum(item["heart_margin_aligned"] for item in items if item["heart_margin_aligned"] is not None)
                    / max(sum(1 for item in items if item["heart_margin_aligned"] is not None), 1)
                ),
                "mean_aligned_heart_margin_target": (
                    sum(item["heart_margin_aligned"] for item in target_items if item["heart_margin_aligned"] is not None)
                    / max(sum(1 for item in target_items if item["heart_margin_aligned"] is not None), 1)
                ),
                "dissociation_success_rate": (
                    sum(item["dissociation_success"] for item in target_items if item["dissociation_success"] is not None)
                    / max(sum(1 for item in target_items if item["dissociation_success"] is not None), 1)
                ),
                "dissociation_success_n": sum(
                    1 for item in target_items if item["dissociation_success"] is not None
                ),
                "collapse_rate": (
                    sum(1 for item in target_items if item["collapse"])
                    / len(target_items)
                    if target_items
                    else 0.0
                ),
            }
        )
    return rows


def paired_margin_analysis(aggregated: list[dict], comparisons: list[tuple[str, str]]) -> dict:
    by_model_condition_item = defaultdict(dict)
    for item in aggregated:
        by_model_condition_item[(item["model"], item["condition"])][item["item_id"]] = item

    analysis = defaultdict(dict)
    for model in sorted({item["model"] for item in aggregated}):
        for cond_a, cond_b in comparisons:
            items_a = by_model_condition_item[(model, cond_a)]
            items_b = by_model_condition_item[(model, cond_b)]
            common_ids = sorted(set(items_a) & set(items_b))
            values_a = []
            values_b = []
            for item_id in common_ids:
                item_a = items_a[item_id]
                item_b = items_b[item_id]
                if not item_a["dissociation_target"] or not item_b["dissociation_target"]:
                    continue
                if item_a["heart_margin_aligned"] is None or item_b["heart_margin_aligned"] is None:
                    continue
                values_a.append(item_a["heart_margin_aligned"])
                values_b.append(item_b["heart_margin_aligned"])

            label = f"{cond_a}_vs_{cond_b}"
            analysis[model][label] = {
                "n_items": len(values_a),
                "bootstrap_diff": bootstrap_numeric_diff_ci(values_a, values_b),
                "wilcoxon": wilcoxon_signed_rank(values_a, values_b),
                "gain": (
                    (sum(values_b) / len(values_b)) - (sum(values_a) / len(values_a))
                    if values_a else None
                ),
            }
    return analysis


def paired_dissociation_analysis(aggregated: list[dict], comparisons: list[tuple[str, str]]) -> dict:
    by_model_condition_item = defaultdict(dict)
    for item in aggregated:
        by_model_condition_item[(item["model"], item["condition"])][item["item_id"]] = item

    analysis = defaultdict(dict)
    for model in sorted({item["model"] for item in aggregated}):
        for cond_a, cond_b in comparisons:
            items_a = by_model_condition_item[(model, cond_a)]
            items_b = by_model_condition_item[(model, cond_b)]
            common_ids = sorted(set(items_a) & set(items_b))
            values_a = []
            values_b = []
            for item_id in common_ids:
                item_a = items_a[item_id]
                item_b = items_b[item_id]
                if not item_a["dissociation_target"] or not item_b["dissociation_target"]:
                    continue
                if item_a["dissociation_success"] is None or item_b["dissociation_success"] is None:
                    continue
                values_a.append(item_a["dissociation_success"])
                values_b.append(item_b["dissociation_success"])

            label = f"{cond_a}_vs_{cond_b}"
            analysis[model][label] = {
                "n_items": len(values_a),
                "mcnemar": mcnemar_test(values_a, values_b),
                "bootstrap_diff": bootstrap_diff_ci(values_a, values_b),
                "gain": (
                    (sum(values_b) / len(values_b)) - (sum(values_a) / len(values_a))
                    if values_a else None
                ),
            }
    return analysis


def analyze_benchmark(bench_name: str, bench_cfg: dict) -> None:
    results_root = analyze_benchmark.results_root
    results_dir = PROJECT_ROOT / results_root / bench_name / "main"
    benchmark = load_benchmark(PROJECT_ROOT / bench_cfg["benchmark_file"])
    expected_rows = len(benchmark) * 2
    results_rows = load_results_rows(results_dir, expected_rows=expected_rows)
    if not results_rows:
        print(f"Missing structured results for {bench_name}: {results_dir}")
        return

    aggregated = aggregate_results(results_rows, benchmark)
    comparisons = [("C0", "C1"), ("C0", "C2"), ("C2", "C4"), ("C2", "C3")]
    output = {
        "benchmark": bench_name,
        "summary_table": summary_rows(aggregated),
        "paired_margin_analysis": paired_margin_analysis(aggregated, comparisons),
        "paired_dissociation_analysis": paired_dissociation_analysis(aggregated, comparisons),
    }

    analysis_path = results_dir / "analysis.json"
    with open(analysis_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Saved structured analysis to {analysis_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyze structured casewise results")
    parser.add_argument("--benchmark", type=str, default=None, help="Optional benchmark key")
    parser.add_argument(
        "--results-root",
        type=str,
        default="results_structured_v2",
        help="Results root directory relative to project root",
    )
    parser.add_argument(
        "--experiment-config",
        type=str,
        default=None,
        help="Config stem under configs/ to use for benchmark paths",
    )
    args = parser.parse_args()

    analyze_benchmark.results_root = args.results_root
    config_name = args.experiment_config
    if not config_name:
        config_name = (
            "experiment_dual_logit_v2"
            if "dual_logit_v2" in args.results_root
            else "experiment_structured_v2"
        )

    configs = benchmark_configs(config_name)
    if args.benchmark:
        if args.benchmark not in configs:
            raise SystemExit(f"Unknown structured benchmark: {args.benchmark}")
        configs = {args.benchmark: configs[args.benchmark]}

    for bench_name, bench_cfg in configs.items():
        analyze_benchmark(bench_name, bench_cfg)


if __name__ == "__main__":
    main()
