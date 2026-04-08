#!/usr/bin/env python3
"""Score casewise heart scoring results."""

import argparse
import json
from collections import Counter, defaultdict
from typing import Optional

import yaml

from utils import PROJECT_ROOT, load_benchmark, load_jsonl

EXPECTED_MARGIN_THRESHOLD = 0.10


def aggregate_results(results: list, benchmark: list) -> list:
    gold = {item["item_id"]: item for item in benchmark}
    grouped = defaultdict(dict)

    for row in results:
        if row["item_id"] not in gold:
            continue
        key = (row["model"], row["condition"], row["item_id"])
        grouped[key][row["case_label"]] = row

    aggregated = []
    for (model, condition, item_id), cases in sorted(grouped.items()):
        gold_item = gold[item_id]
        case_a = cases.get("A")
        case_b = cases.get("B")
        score_a = case_a.get("heart_score") if case_a else None
        score_b = case_b.get("heart_score") if case_b else None
        expected_a = case_a.get("expected_heart_score") if case_a else None
        expected_b = case_b.get("expected_heart_score") if case_b else None

        pair_pred = None
        if score_a is not None and score_b is not None:
            if score_a > score_b:
                pair_pred = "A"
            elif score_b > score_a:
                pair_pred = "B"

        heart_correct = (
            pair_pred == gold_item["gold_heart_worse"] if pair_pred is not None else None
        )
        margin = abs(score_a - score_b) if score_a is not None and score_b is not None else None
        expected_pair_pred = None
        expected_margin = None
        expected_confident_pred = None
        if expected_a is not None and expected_b is not None:
            expected_margin = abs(expected_a - expected_b)
            if expected_a > expected_b:
                expected_pair_pred = "A"
            elif expected_b > expected_a:
                expected_pair_pred = "B"
            if expected_margin >= EXPECTED_MARGIN_THRESHOLD:
                expected_confident_pred = expected_pair_pred

        expected_heart_correct = (
            expected_pair_pred == gold_item["gold_heart_worse"]
            if expected_pair_pred is not None
            else None
        )
        expected_confident_correct = (
            expected_confident_pred == gold_item["gold_heart_worse"]
            if expected_confident_pred is not None
            else None
        )

        aggregated.append(
            {
                "item_id": item_id,
                "model": model,
                "condition": condition,
                "family": gold_item["family"],
                "difficulty": gold_item["difficulty"],
                "gold_heart_worse": gold_item["gold_heart_worse"],
                "case_a_parse_success": bool(case_a and case_a.get("parse_success")),
                "case_b_parse_success": bool(case_b and case_b.get("parse_success")),
                "case_a_score": score_a,
                "case_b_score": score_b,
                "case_a_expected_score": expected_a,
                "case_b_expected_score": expected_b,
                "case_a_reason_focus": case_a.get("reason_focus") if case_a else None,
                "case_b_reason_focus": case_b.get("reason_focus") if case_b else None,
                "pair_pred": pair_pred,
                "heart_correct": heart_correct,
                "margin": margin,
                "expected_pair_pred": expected_pair_pred,
                "expected_heart_correct": expected_heart_correct,
                "expected_margin": expected_margin,
                "expected_confident_pred": expected_confident_pred,
                "expected_confident_correct": expected_confident_correct,
            }
        )

    return aggregated


def accuracy(values: list[Optional[bool]]) -> dict:
    valid = [value for value in values if value is not None]
    if not valid:
        return {"accuracy": None, "n": 0, "correct": 0}
    correct = sum(1 for value in valid if value)
    return {"accuracy": correct / len(valid), "n": len(valid), "correct": correct}


def average(values: list[Optional[float]]) -> dict:
    valid = [value for value in values if value is not None]
    if not valid:
        return {"mean": None, "n": 0}
    return {"mean": sum(valid) / len(valid), "n": len(valid)}


def score_group(items: list) -> dict:
    parse_a = [item for item in items if item["case_a_parse_success"]]
    parse_b = [item for item in items if item["case_b_parse_success"]]
    reason_counts = Counter()
    for item in items:
        if item["case_a_reason_focus"]:
            reason_counts[f"A:{item['case_a_reason_focus']}"] += 1
        if item["case_b_reason_focus"]:
            reason_counts[f"B:{item['case_b_reason_focus']}"] += 1

    by_family = defaultdict(list)
    by_family_expected = defaultdict(list)
    for item in items:
        by_family[item["family"]].append(item["heart_correct"])
        by_family_expected[item["family"]].append(item["expected_heart_correct"])

    resolved = [item for item in items if item["heart_correct"] is not None]
    ties = [item for item in items if item["pair_pred"] is None and item["case_a_score"] is not None and item["case_b_score"] is not None]
    expected_resolved = [item for item in items if item["expected_heart_correct"] is not None]
    expected_confident = [item for item in items if item["expected_confident_correct"] is not None]

    return {
        "total_items": len(items),
        "case_a_parse_rate": len(parse_a) / len(items) if items else 0.0,
        "case_b_parse_rate": len(parse_b) / len(items) if items else 0.0,
        "resolved_rate": len(resolved) / len(items) if items else 0.0,
        "tie_rate": len(ties) / len(items) if items else 0.0,
        "resolved_accuracy": accuracy([item["heart_correct"] for item in items]),
        "mean_margin": average([item["margin"] for item in items]),
        "mean_case_a_score": average([item["case_a_score"] for item in items]),
        "mean_case_b_score": average([item["case_b_score"] for item in items]),
        "expected_accuracy": accuracy([item["expected_heart_correct"] for item in items]),
        "expected_mean_margin": average([item["expected_margin"] for item in items]),
        "expected_mean_case_a_score": average([item["case_a_expected_score"] for item in items]),
        "expected_mean_case_b_score": average([item["case_b_expected_score"] for item in items]),
        "expected_confident_rate": len(expected_confident) / len(items) if items else 0.0,
        "expected_confident_accuracy": accuracy([item["expected_confident_correct"] for item in items]),
        "expected_margin_threshold": EXPECTED_MARGIN_THRESHOLD,
        "reason_focus": {
            key: {"count": value, "rate": value / max(sum(reason_counts.values()), 1)}
            for key, value in sorted(reason_counts.items())
        },
        "by_family": {family: accuracy(values) for family, values in sorted(by_family.items())},
        "by_family_expected": {
            family: accuracy(values) for family, values in sorted(by_family_expected.items())
        },
    }


def benchmark_configs() -> dict:
    with open(PROJECT_ROOT / "configs" / "experiment_casewise_logit.yaml") as f:
        return yaml.safe_load(f)["benchmarks"]


def score_benchmark(bench_name: str, bench_cfg: dict) -> None:
    results_root = score_benchmark.results_root
    results_path = PROJECT_ROOT / results_root / bench_name / "main" / "all_results.jsonl"
    if not results_path.exists():
        print(f"Missing results for {bench_name}: {results_path}")
        return

    benchmark = load_benchmark(PROJECT_ROOT / bench_cfg["benchmark_file"])
    aggregated = aggregate_results(load_jsonl(results_path), benchmark)

    by_model_condition = defaultdict(list)
    for item in aggregated:
        by_model_condition[(item["model"], item["condition"])].append(item)

    scores = {
        "benchmark": bench_name,
        "total_items": len(benchmark),
        "per_model_condition": {
            f"{model}/{condition}": score_group(items)
            for (model, condition), items in sorted(by_model_condition.items())
        },
    }

    scores_path = results_path.parent / "scores.json"
    with open(scores_path, "w") as f:
        json.dump(scores, f, indent=2)
    print(f"Saved casewise scores to {scores_path}")


def main():
    parser = argparse.ArgumentParser(description="Score casewise results")
    parser.add_argument("--benchmark", type=str, default=None, help="Optional benchmark key")
    parser.add_argument(
        "--results-root",
        type=str,
        default="results_casewise_logit",
        help="Results root directory relative to project root",
    )
    args = parser.parse_args()

    score_benchmark.results_root = args.results_root

    configs = benchmark_configs()
    if args.benchmark:
        if args.benchmark not in configs:
            raise SystemExit(f"Unknown casewise benchmark: {args.benchmark}")
        configs = {args.benchmark: configs[args.benchmark]}

    for bench_name, bench_cfg in configs.items():
        score_benchmark(bench_name, bench_cfg)


if __name__ == "__main__":
    main()
