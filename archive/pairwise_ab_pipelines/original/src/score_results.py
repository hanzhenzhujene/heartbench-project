#!/usr/bin/env python3
"""Score HeartBench results: accuracy, reason focus, surface overweighting."""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from utils import load_jsonl, load_benchmark, save_jsonl, PROJECT_ROOT


def merge_results_with_gold(results: list[dict], benchmark: list[dict]) -> list[dict]:
    """Join model outputs with gold labels from the benchmark."""
    gold_map = {item["item_id"]: item for item in benchmark}
    merged = []
    for r in results:
        item_id = r["item_id"]
        # Handle swapped item IDs
        base_id = item_id.replace("_swap", "")
        gold = gold_map.get(item_id) or gold_map.get(base_id)
        if gold is None:
            continue
        m = dict(r)
        m["gold_heart_worse"] = gold["gold_heart_worse"]
        m["gold_morally_worse"] = gold["gold_morally_worse"]
        m["gold_primary_cue"] = gold["gold_primary_cue"]
        m["family"] = gold["family"]
        m["difficulty"] = gold["difficulty"]
        m["domain"] = gold.get("domain", "")
        # Score
        m["heart_correct"] = (r.get("heart_worse") == gold["gold_heart_worse"]) if r.get("heart_worse") else None
        m["moral_correct"] = (r.get("morally_worse") == gold["gold_morally_worse"]) if r.get("morally_worse") else None
        merged.append(m)
    return merged


def compute_accuracy(scored: list[dict], key: str = "heart_correct") -> dict:
    """Compute accuracy for items with valid parses."""
    valid = [s for s in scored if s.get(key) is not None]
    if not valid:
        return {"accuracy": None, "n": 0, "correct": 0}
    correct = sum(1 for s in valid if s[key])
    return {
        "accuracy": correct / len(valid),
        "n": len(valid),
        "correct": correct,
    }


def compute_reason_focus_distribution(scored: list[dict]) -> dict:
    """Distribution of reason_focus values."""
    valid = [s for s in scored if s.get("parse_success") and s.get("reason_focus")]
    counts = Counter(s["reason_focus"] for s in valid)
    total = sum(counts.values())
    return {k: {"count": v, "rate": v / total if total else 0} for k, v in sorted(counts.items())}


def compute_surface_overweighting(scored: list[dict]) -> dict:
    """Rate of outward_act focus on items where motive is the intended cue."""
    motive_items = [s for s in scored if s.get("gold_primary_cue") in ("motive", "inward_posture")
                    and s.get("parse_success") and s.get("reason_focus")]
    if not motive_items:
        return {"rate": None, "n": 0}
    surface = sum(1 for s in motive_items if s["reason_focus"] == "outward_act")
    return {
        "rate": surface / len(motive_items),
        "n": len(motive_items),
        "surface_count": surface,
    }


def compute_dissociation_rate(scored: list[dict]) -> dict:
    """Rate at which heart_worse and morally_worse answers differ."""
    valid = [s for s in scored if s.get("heart_worse") and s.get("morally_worse")]
    if not valid:
        return {"rate": None, "n": 0}
    dissociated = sum(1 for s in valid if s["heart_worse"] != s["morally_worse"])
    return {
        "rate": dissociated / len(valid),
        "n": len(valid),
        "dissociated_count": dissociated,
    }


def score_by_group(scored: list[dict], group_key: str) -> dict:
    """Compute heart accuracy by a grouping variable."""
    groups = defaultdict(list)
    for s in scored:
        groups[s.get(group_key, "unknown")].append(s)
    return {k: compute_accuracy(v, "heart_correct") for k, v in sorted(groups.items())}


def generate_scores(results_path: Path, benchmark_path: Path) -> dict:
    """Main scoring function."""
    results = load_jsonl(results_path)
    benchmark = load_benchmark(benchmark_path)

    scored = merge_results_with_gold(results, benchmark)

    # Group by model x condition
    by_mc = defaultdict(list)
    for s in scored:
        key = (s.get("model", "unknown"), s.get("condition", "unknown"))
        by_mc[key].append(s)

    all_scores = {}
    for (model, cond), items in sorted(by_mc.items()):
        key = f"{model}/{cond}"
        all_scores[key] = {
            "heart_accuracy": compute_accuracy(items, "heart_correct"),
            "moral_accuracy": compute_accuracy(items, "moral_correct"),
            "reason_focus": compute_reason_focus_distribution(items),
            "surface_overweighting": compute_surface_overweighting(items),
            "dissociation": compute_dissociation_rate(items),
            "by_family": score_by_group(items, "family"),
            "by_difficulty": score_by_group(items, "difficulty"),
        }

    return {"per_model_condition": all_scores, "total_scored": len(scored)}


def get_benchmark_configs():
    """Load benchmark configurations from experiment.yaml."""
    import yaml
    config_path = PROJECT_ROOT / "configs" / "experiment.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config.get("benchmarks", {})


def score_benchmark(bench_name, bench_cfg, results_dir):
    """Score results for a single benchmark."""
    benchmark_path = PROJECT_ROOT / bench_cfg["benchmark_file"]
    dev_path = PROJECT_ROOT / bench_cfg["dev_file"]

    for subdir in ["pilot", "main"]:
        # Check both new-style (results/bench_name/subdir) and old-style (results/subdir)
        results_path = results_dir / bench_name / subdir / "all_results.jsonl"
        if not results_path.exists():
            # Try old-style path for backward compat with heartbench pilot
            if bench_name == "heartbench":
                results_path = results_dir / subdir / "all_results.jsonl"
            if not results_path.exists():
                continue

        # Use dev benchmark for pilot, full for main
        bench = dev_path if subdir == "pilot" else benchmark_path
        if not bench.exists():
            bench = benchmark_path

        print(f"\n{'='*60}")
        print(f"Scoring [{bench_name}]: {results_path}")

        scores = generate_scores(results_path, bench)

        # Save scores in the same directory as results
        scores_path = results_path.parent / "scores.json"
        with open(scores_path, "w") as f:
            json.dump(scores, f, indent=2, default=str)
        print(f"Scores saved to {scores_path}")

        # Print summary
        print(f"\nTotal scored items: {scores['total_scored']}")
        for key, s in scores["per_model_condition"].items():
            ha = s["heart_accuracy"]
            ma = s["moral_accuracy"]
            so = s["surface_overweighting"]
            print(f"\n  {key}:")
            print(f"    Heart acc: {ha['accuracy']:.3f} ({ha['correct']}/{ha['n']})" if ha['accuracy'] is not None else f"    Heart acc: N/A")
            print(f"    Moral acc: {ma['accuracy']:.3f} ({ma['correct']}/{ma['n']})" if ma['accuracy'] is not None else f"    Moral acc: N/A")
            if so.get("rate") is not None:
                print(f"    Surface overweight: {so['rate']:.3f} ({so['surface_count']}/{so['n']})")
            # Reason focus
            rf = s["reason_focus"]
            rf_str = ", ".join(f"{k}:{v['count']}" for k, v in rf.items())
            print(f"    Reason focus: {rf_str}")


def main():
    results_dir = PROJECT_ROOT / "results"
    bench_configs = get_benchmark_configs()

    if not bench_configs:
        # Fallback: old-style single benchmark
        bench_configs = {
            "heartbench": {
                "benchmark_file": "benchmark/heartbench_240.jsonl",
                "dev_file": "benchmark/heartbench_dev.jsonl",
            }
        }

    for bench_name, bench_cfg in bench_configs.items():
        score_benchmark(bench_name, bench_cfg, results_dir)


if __name__ == "__main__":
    main()
