#!/usr/bin/env python3
"""Score structured HeartBench-v2 casewise results."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from typing import Optional

import yaml

from utils import PROJECT_ROOT, load_benchmark, load_jsonl


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


def compare_scores(score_a: Optional[int], score_b: Optional[int]) -> Optional[str]:
    if score_a is None or score_b is None:
        return None
    if score_a > score_b:
        return "A"
    if score_b > score_a:
        return "B"
    return "tie"


def aligned_margin(score_a: Optional[int], score_b: Optional[int], gold_worse: str) -> Optional[float]:
    if score_a is None or score_b is None:
        return None
    if gold_worse == "A":
        return float(score_a - score_b)
    if gold_worse == "B":
        return float(score_b - score_a)
    return None


def aggregate_results(results: list[dict], benchmark: list[dict]) -> list[dict]:
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

        act_a = case_a.get("act_score") if case_a else None
        act_b = case_b.get("act_score") if case_b else None
        heart_a = case_a.get("heart_score") if case_a else None
        heart_b = case_b.get("heart_score") if case_b else None
        exp_act_a = case_a.get("expected_act_score", act_a) if case_a else None
        exp_act_b = case_b.get("expected_act_score", act_b) if case_b else None
        exp_heart_a = case_a.get("expected_heart_score", heart_a) if case_a else None
        exp_heart_b = case_b.get("expected_heart_score", heart_b) if case_b else None

        pred_act_worse = compare_scores(act_a, act_b)
        pred_heart_worse = compare_scores(heart_a, heart_b)

        heart_correct = (
            pred_heart_worse == gold_item["gold_heart_worse"]
            if pred_heart_worse in {"A", "B"}
            else None
        )
        act_correct = (
            pred_act_worse == gold_item["gold_act_worse"]
            if pred_act_worse is not None
            else None
        )

        heart_margin_aligned = aligned_margin(exp_heart_a, exp_heart_b, gold_item["gold_heart_worse"])
        if gold_item["gold_act_worse"] in {"A", "B"}:
            act_margin_target = aligned_margin(exp_act_a, exp_act_b, gold_item["gold_act_worse"])
            act_tie_error = None
        else:
            act_margin_target = None
            act_tie_error = (
                abs(exp_act_a - exp_act_b)
                if exp_act_a is not None and exp_act_b is not None
                else None
            )

        dissociation_success = None
        collapse = None
        if gold_item["dissociation_target"]:
            if gold_item["gold_act_worse"] == "tie":
                dissociation_success = (
                    pred_heart_worse == gold_item["gold_heart_worse"]
                    and pred_act_worse == "tie"
                )
            else:
                dissociation_success = (
                    pred_heart_worse == gold_item["gold_heart_worse"]
                    and pred_act_worse == gold_item["gold_act_worse"]
                )
            collapse = pred_heart_worse == pred_act_worse and pred_heart_worse != "tie"

        aggregated.append(
            {
                "item_id": item_id,
                "model": model,
                "condition": condition,
                "family": gold_item["family"],
                "difficulty": gold_item["difficulty"],
                "dissociation_target": gold_item["dissociation_target"],
                "gold_heart_worse": gold_item["gold_heart_worse"],
                "gold_act_worse": gold_item["gold_act_worse"],
                "case_a_parse_success": bool(case_a and case_a.get("parse_success")),
                "case_b_parse_success": bool(case_b and case_b.get("parse_success")),
                "case_a_act_score": act_a,
                "case_b_act_score": act_b,
                "case_a_heart_score": heart_a,
                "case_b_heart_score": heart_b,
                "case_a_expected_act_score": exp_act_a,
                "case_b_expected_act_score": exp_act_b,
                "case_a_expected_heart_score": exp_heart_a,
                "case_b_expected_heart_score": exp_heart_b,
                "case_a_reason_focus": case_a.get("reason_focus") if case_a else None,
                "case_b_reason_focus": case_b.get("reason_focus") if case_b else None,
                "pred_heart_worse": pred_heart_worse,
                "pred_act_worse": pred_act_worse,
                "heart_correct": heart_correct,
                "act_correct": act_correct,
                "heart_margin_aligned": heart_margin_aligned,
                "act_margin_target": act_margin_target,
                "act_tie_error": act_tie_error,
                "dissociation_success": dissociation_success,
                "collapse": collapse,
            }
        )

    return aggregated


def score_group(items: list[dict]) -> dict:
    parse_a = [item for item in items if item["case_a_parse_success"]]
    parse_b = [item for item in items if item["case_b_parse_success"]]
    target_items = [item for item in items if item["dissociation_target"]]
    reason_counts = Counter()
    for item in items:
        if item["case_a_reason_focus"]:
            reason_counts[f"A:{item['case_a_reason_focus']}"] += 1
        if item["case_b_reason_focus"]:
            reason_counts[f"B:{item['case_b_reason_focus']}"] += 1

    by_family_heart = defaultdict(list)
    by_family_dissociation = defaultdict(list)
    for item in items:
        by_family_heart[item["family"]].append(item["heart_correct"])
        if item["dissociation_target"]:
            by_family_dissociation[item["family"]].append(item["dissociation_success"])

    return {
        "total_items": len(items),
        "dissociation_items": len(target_items),
        "case_a_parse_rate": len(parse_a) / len(items) if items else 0.0,
        "case_b_parse_rate": len(parse_b) / len(items) if items else 0.0,
        "heart_resolved_accuracy": accuracy([item["heart_correct"] for item in items]),
        "heart_tie_rate": sum(1 for item in items if item["pred_heart_worse"] == "tie") / len(items) if items else 0.0,
        "act_pair_accuracy": accuracy([item["act_correct"] for item in items]),
        "act_tie_rate": sum(1 for item in items if item["pred_act_worse"] == "tie") / len(items) if items else 0.0,
        "mean_aligned_heart_margin": average([item["heart_margin_aligned"] for item in items]),
        "mean_aligned_heart_margin_target": average(
            [item["heart_margin_aligned"] for item in target_items]
        ),
        "mean_act_margin_target": average(
            [item["act_margin_target"] for item in items if item["act_margin_target"] is not None]
        ),
        "mean_act_tie_error": average(
            [item["act_tie_error"] for item in items if item["act_tie_error"] is not None]
        ),
        "dissociation_success": accuracy([item["dissociation_success"] for item in target_items]),
        "collapse_rate": average([1.0 if item["collapse"] else 0.0 for item in target_items]),
        "reason_focus": {
            key: {"count": value, "rate": value / max(sum(reason_counts.values()), 1)}
            for key, value in sorted(reason_counts.items())
        },
        "by_family_heart": {
            family: accuracy(values) for family, values in sorted(by_family_heart.items())
        },
        "by_family_dissociation": {
            family: accuracy(values)
            for family, values in sorted(by_family_dissociation.items())
        },
    }


def benchmark_configs(config_name: str) -> dict:
    with open(PROJECT_ROOT / "research" / "configs" / f"{config_name}.yaml") as f:
        return yaml.safe_load(f)["benchmarks"]


def load_results_rows(results_dir, expected_rows: int | None = None) -> list[dict]:
    per_condition_paths = [
        path
        for path in sorted(results_dir.glob("Qwen*.jsonl"))
        if path.name != "all_results.jsonl"
    ]
    if per_condition_paths:
        deduped = {}
        for path in per_condition_paths:
            rows = load_jsonl(path)
            if expected_rows is not None and len(rows) != expected_rows:
                print(
                    f"Skipping incomplete result file {path.name}: "
                    f"{len(rows)} rows, expected {expected_rows}"
                )
                continue
            for row in rows:
                key = (
                    row.get("model"),
                    row.get("condition"),
                    row.get("item_id"),
                    row.get("case_label"),
                )
                deduped[key] = row
        return list(deduped.values())

    combined_path = results_dir / "all_results.jsonl"
    if combined_path.exists():
        return load_jsonl(combined_path)

    rows = []
    for path in per_condition_paths:
        if path.name == "all_results.jsonl":
            continue
        rows.extend(load_jsonl(path))
    return rows


def score_benchmark(bench_name: str, bench_cfg: dict) -> None:
    results_root = score_benchmark.results_root
    results_dir = PROJECT_ROOT / results_root / bench_name / "main"
    benchmark = load_benchmark(PROJECT_ROOT / bench_cfg["benchmark_file"])
    expected_rows = len(benchmark) * 2
    results_rows = load_results_rows(results_dir, expected_rows=expected_rows)
    if not results_rows:
        print(f"Missing structured results for {bench_name}: {results_dir}")
        return

    aggregated = aggregate_results(results_rows, benchmark)

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

    scores_path = results_dir / "scores.json"
    with open(scores_path, "w") as f:
        json.dump(scores, f, indent=2)
    print(f"Saved structured scores to {scores_path}")


def main():
    parser = argparse.ArgumentParser(description="Score structured casewise results")
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
        help="Config stem under research/configs/ to use for benchmark paths",
    )
    args = parser.parse_args()

    score_benchmark.results_root = args.results_root
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
        score_benchmark(bench_name, bench_cfg)


if __name__ == "__main__":
    main()
