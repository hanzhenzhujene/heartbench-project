#!/usr/bin/env python3
"""Score corrected order-balanced results."""

import argparse
import json
from collections import Counter, defaultdict
from typing import Optional

import yaml

from utils import PROJECT_ROOT, load_benchmark, load_jsonl


def aggregate_results(results: list[dict], benchmark: list[dict]) -> list[dict]:
    gold = {item["item_id"]: item for item in benchmark}
    grouped = defaultdict(dict)

    for row in results:
        if row["item_id"] not in gold:
            continue
        key = (row["model"], row["condition"], row["item_id"])
        grouped[key][row["order"]] = row

    aggregated = []
    for (model, condition, item_id), orders in sorted(grouped.items()):
        gold_item = gold[item_id]
        original = orders.get("original")
        swapped = orders.get("swapped")

        original_norm = original.get("normalized_heart_worse") if original else None
        swapped_norm = swapped.get("normalized_heart_worse") if swapped else None

        parsed_orders = [pred for pred in [original_norm, swapped_norm] if pred is not None]
        order_correct = [pred == gold_item["gold_heart_worse"] for pred in parsed_orders]

        agreement = (
            original_norm is not None
            and swapped_norm is not None
            and original_norm == swapped_norm
        )
        resolved_pred = original_norm if agreement else None
        heart_correct = resolved_pred == gold_item["gold_heart_worse"] if resolved_pred else None

        aggregated.append(
            {
                "item_id": item_id,
                "model": model,
                "condition": condition,
                "family": gold_item["family"],
                "difficulty": gold_item["difficulty"],
                "gold_heart_worse": gold_item["gold_heart_worse"],
                "original_parse_success": bool(original and original.get("parse_success")),
                "swapped_parse_success": bool(swapped and swapped.get("parse_success")),
                "original_raw_heart_worse": original.get("heart_worse") if original else None,
                "swapped_raw_heart_worse": swapped.get("heart_worse") if swapped else None,
                "original_normalized_heart_worse": original_norm,
                "swapped_normalized_heart_worse": swapped_norm,
                "agreement": agreement,
                "resolved_pred": resolved_pred,
                "heart_correct": heart_correct,
                "order_avg_correct": sum(order_correct) / len(order_correct) if order_correct else None,
                "original_reason_focus": original.get("reason_focus") if original else None,
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


def score_group(items: list[dict]) -> dict:
    original_items = [item for item in items if item["original_parse_success"]]
    swapped_items = [item for item in items if item["swapped_parse_success"]]
    reason_counts = Counter(
        item["original_reason_focus"] for item in original_items if item["original_reason_focus"]
    )
    reason_total = sum(reason_counts.values())

    by_family = defaultdict(list)
    for item in items:
        by_family[item["family"]].append(item["heart_correct"])

    return {
        "total_items": len(items),
        "original_parse_rate": len(original_items) / len(items) if items else 0.0,
        "swapped_parse_rate": len(swapped_items) / len(items) if items else 0.0,
        "agreement_rate": sum(1 for item in items if item["agreement"]) / len(items) if items else 0.0,
        "resolved_accuracy": accuracy([item["heart_correct"] for item in items]),
        "order_avg_accuracy": average([item["order_avg_correct"] for item in items]),
        "original_answer_distribution": {
            key: {"count": value, "rate": value / len(original_items) if original_items else 0.0}
            for key, value in sorted(Counter(item["original_raw_heart_worse"] for item in original_items).items())
        },
        "swapped_answer_distribution": {
            key: {"count": value, "rate": value / len(swapped_items) if swapped_items else 0.0}
            for key, value in sorted(Counter(item["swapped_raw_heart_worse"] for item in swapped_items).items())
        },
        "reason_focus": {
            key: {"count": value, "rate": value / reason_total if reason_total else 0.0}
            for key, value in sorted(reason_counts.items())
        },
        "by_family": {
            family: accuracy(values) for family, values in sorted(by_family.items())
        },
    }


def benchmark_configs() -> dict:
    with open(PROJECT_ROOT / "configs" / "experiment_corrected.yaml") as f:
        return yaml.safe_load(f)["benchmarks"]


def score_benchmark(bench_name: str, bench_cfg: dict) -> None:
    results_path = PROJECT_ROOT / "results_corrected" / bench_name / "main" / "all_results.jsonl"
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
    print(f"Saved corrected scores to {scores_path}")


def main():
    parser = argparse.ArgumentParser(description="Score corrected results")
    parser.add_argument("--benchmark", type=str, default=None, help="Optional benchmark key")
    args = parser.parse_args()

    configs = benchmark_configs()
    if args.benchmark:
        if args.benchmark not in configs:
            raise SystemExit(f"Unknown corrected benchmark: {args.benchmark}")
        configs = {args.benchmark: configs[args.benchmark]}

    for bench_name, bench_cfg in configs.items():
        score_benchmark(bench_name, bench_cfg)


if __name__ == "__main__":
    main()
