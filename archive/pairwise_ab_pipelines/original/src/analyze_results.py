#!/usr/bin/env python3
"""
Statistical analysis for HeartBench results.

Implements:
- Bootstrap confidence intervals for accuracy differences
- McNemar tests for paired comparisons
- Summary tables
- Heart shift gain computation
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats as scipy_stats

from utils import load_jsonl, load_benchmark, PROJECT_ROOT
from score_results import merge_results_with_gold


def bootstrap_ci(values: list[bool], n_boot: int = 1000, seed: int = 42,
                 alpha: float = 0.05) -> dict:
    """Compute bootstrap confidence interval for accuracy."""
    if not values:
        return {"mean": None, "ci_low": None, "ci_high": None, "n": 0}
    rng = np.random.RandomState(seed)
    arr = np.array(values, dtype=float)
    boot_means = []
    for _ in range(n_boot):
        sample = rng.choice(arr, size=len(arr), replace=True)
        boot_means.append(sample.mean())
    boot_means = sorted(boot_means)
    lo = boot_means[int(n_boot * alpha / 2)]
    hi = boot_means[int(n_boot * (1 - alpha / 2))]
    return {
        "mean": float(arr.mean()),
        "ci_low": float(lo),
        "ci_high": float(hi),
        "n": len(values),
    }


def bootstrap_diff_ci(values_a: list[bool], values_b: list[bool],
                       n_boot: int = 1000, seed: int = 42,
                       alpha: float = 0.05) -> dict:
    """Bootstrap CI for the difference in accuracy (B - A)."""
    if not values_a or not values_b or len(values_a) != len(values_b):
        return {"mean_diff": None, "ci_low": None, "ci_high": None, "n": 0}
    rng = np.random.RandomState(seed)
    arr_a = np.array(values_a, dtype=float)
    arr_b = np.array(values_b, dtype=float)
    diffs = arr_b - arr_a
    boot_diffs = []
    for _ in range(n_boot):
        idx = rng.choice(len(diffs), size=len(diffs), replace=True)
        boot_diffs.append(diffs[idx].mean())
    boot_diffs = sorted(boot_diffs)
    lo = boot_diffs[int(n_boot * alpha / 2)]
    hi = boot_diffs[int(n_boot * (1 - alpha / 2))]
    return {
        "mean_diff": float(diffs.mean()),
        "ci_low": float(lo),
        "ci_high": float(hi),
        "n": len(diffs),
    }


def mcnemar_test(correct_a: list[bool], correct_b: list[bool]) -> dict:
    """McNemar's test for paired binary comparisons.

    Compares condition B vs condition A on the same items.
    """
    if len(correct_a) != len(correct_b):
        return {"statistic": None, "p_value": None, "n": 0}

    # Count discordant pairs
    b_right_a_wrong = 0  # B correct, A wrong
    b_wrong_a_right = 0  # A correct, B wrong

    for a, b in zip(correct_a, correct_b):
        if b and not a:
            b_right_a_wrong += 1
        elif a and not b:
            b_wrong_a_right += 1

    n_discordant = b_right_a_wrong + b_wrong_a_right
    if n_discordant == 0:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "b_right_a_wrong": b_right_a_wrong,
            "b_wrong_a_right": b_wrong_a_right,
            "n": len(correct_a),
        }

    # McNemar's chi-squared (with continuity correction)
    stat = (abs(b_right_a_wrong - b_wrong_a_right) - 1) ** 2 / n_discordant
    p_val = 1 - scipy_stats.chi2.cdf(stat, df=1)

    return {
        "statistic": float(stat),
        "p_value": float(p_val),
        "b_right_a_wrong": b_right_a_wrong,
        "b_wrong_a_right": b_wrong_a_right,
        "n": len(correct_a),
    }


def compute_heart_shift_gain(baseline_correct: list[bool],
                              condition_correct: list[bool]) -> dict:
    """Heart shift gain = condition accuracy - baseline accuracy."""
    if not baseline_correct or not condition_correct:
        return {"gain": None}
    base_acc = sum(baseline_correct) / len(baseline_correct)
    cond_acc = sum(condition_correct) / len(condition_correct)
    return {
        "baseline_accuracy": float(base_acc),
        "condition_accuracy": float(cond_acc),
        "gain": float(cond_acc - base_acc),
    }


def run_paired_analysis(scored: list[dict], comparisons: list[tuple]) -> dict:
    """Run all paired comparisons for a given model."""
    # Group by condition, indexed by item_id
    by_cond = defaultdict(dict)
    for s in scored:
        cond = s.get("condition", "unknown")
        item_id = s.get("item_id", "")
        by_cond[cond][item_id] = s

    analysis = {}
    for cond_a, cond_b in comparisons:
        label = f"{cond_a}_vs_{cond_b}"
        items_a = by_cond.get(cond_a, {})
        items_b = by_cond.get(cond_b, {})

        # Align on common items
        common_ids = sorted(set(items_a.keys()) & set(items_b.keys()))

        correct_a = []
        correct_b = []
        for iid in common_ids:
            a = items_a[iid]
            b = items_b[iid]
            if a.get("heart_correct") is not None and b.get("heart_correct") is not None:
                correct_a.append(a["heart_correct"])
                correct_b.append(b["heart_correct"])

        mcnemar = mcnemar_test(correct_a, correct_b)
        boot_diff = bootstrap_diff_ci(correct_a, correct_b)
        shift_gain = compute_heart_shift_gain(correct_a, correct_b)

        analysis[label] = {
            "mcnemar": mcnemar,
            "bootstrap_diff": boot_diff,
            "heart_shift_gain": shift_gain,
            "n_items": len(correct_a),
        }

    return analysis


def generate_summary_table(scored: list[dict]) -> list[dict]:
    """Generate a condition x model summary table."""
    by_mc = defaultdict(list)
    for s in scored:
        key = (s.get("model", "unknown"), s.get("condition", "unknown"))
        by_mc[key].append(s)

    rows = []
    for (model, cond), items in sorted(by_mc.items()):
        valid = [s for s in items if s.get("heart_correct") is not None]
        if not valid:
            continue
        heart_correct = [s["heart_correct"] for s in valid]
        moral_valid = [s for s in items if s.get("moral_correct") is not None]
        moral_correct = [s["moral_correct"] for s in moral_valid]

        motive_items = [s for s in items if s.get("reason_focus") == "motive"]
        outward_items = [s for s in items if s.get("reason_focus") == "outward_act"]

        rows.append({
            "model": model,
            "condition": cond,
            "heart_acc": sum(heart_correct) / len(heart_correct),
            "heart_n": len(heart_correct),
            "moral_acc": sum(moral_correct) / len(moral_correct) if moral_correct else None,
            "moral_n": len(moral_correct),
            "motive_rate": len(motive_items) / len(valid) if valid else None,
            "outward_rate": len(outward_items) / len(valid) if valid else None,
            "parse_rate": sum(1 for s in items if s.get("parse_success")) / len(items),
        })

    return rows


def get_benchmark_configs():
    """Load benchmark configurations from experiment.yaml."""
    import yaml
    config_path = PROJECT_ROOT / "configs" / "experiment.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config.get("benchmarks", {})


def analyze_benchmark(bench_name, bench_cfg, results_dir, comparisons):
    """Analyze results for a single benchmark."""
    benchmark_path = PROJECT_ROOT / bench_cfg["benchmark_file"]
    dev_path = PROJECT_ROOT / bench_cfg["dev_file"]

    for subdir in ["pilot", "main"]:
        # Check new-style path first, then old-style
        results_path = results_dir / bench_name / subdir / "all_results.jsonl"
        if not results_path.exists():
            if bench_name == "heartbench":
                results_path = results_dir / subdir / "all_results.jsonl"
            if not results_path.exists():
                continue

        bench = dev_path if subdir == "pilot" else benchmark_path
        if not bench.exists():
            bench = benchmark_path

        print(f"\n{'='*60}")
        print(f"Analyzing [{bench_name}]: {results_path}")

        results = load_jsonl(results_path)
        benchmark = load_benchmark(bench)
        scored = merge_results_with_gold(results, benchmark)

        # Summary table
        summary = generate_summary_table(scored)
        print("\n--- Summary Table ---")
        print(f"{'Model':<30} {'Cond':<6} {'Heart':<8} {'Moral':<8} {'Motive%':<8} {'Outward%':<9} {'Parse%':<7}")
        for row in summary:
            h = f"{row['heart_acc']:.3f}" if row['heart_acc'] is not None else "N/A"
            m = f"{row['moral_acc']:.3f}" if row['moral_acc'] is not None else "N/A"
            mt = f"{row['motive_rate']:.3f}" if row['motive_rate'] is not None else "N/A"
            ow = f"{row['outward_rate']:.3f}" if row['outward_rate'] is not None else "N/A"
            pr = f"{row['parse_rate']:.3f}"
            print(f"{row['model']:<30} {row['condition']:<6} {h:<8} {m:<8} {mt:<8} {ow:<9} {pr:<7}")

        # Paired analysis per model
        by_model = defaultdict(list)
        for s in scored:
            by_model[s.get("model", "unknown")].append(s)

        all_analysis = {}
        for model, model_scored in sorted(by_model.items()):
            print(f"\n--- Paired Analysis: {model} ---")
            analysis = run_paired_analysis(model_scored, comparisons)
            all_analysis[model] = analysis

            for label, res in analysis.items():
                mc = res["mcnemar"]
                bd = res["bootstrap_diff"]
                sg = res["heart_shift_gain"]
                print(f"\n  {label} (n={res['n_items']}):")
                if sg.get("gain") is not None:
                    print(f"    Heart shift gain: {sg['gain']:+.3f} "
                          f"({sg['baseline_accuracy']:.3f} -> {sg['condition_accuracy']:.3f})")
                if bd.get("mean_diff") is not None:
                    print(f"    Bootstrap diff: {bd['mean_diff']:+.3f} "
                          f"[{bd['ci_low']:+.3f}, {bd['ci_high']:+.3f}]")
                if mc.get("p_value") is not None:
                    print(f"    McNemar: chi2={mc['statistic']:.3f}, p={mc['p_value']:.4f}")
                    print(f"    Discordant: B>A={mc['b_right_a_wrong']}, A>B={mc['b_wrong_a_right']}")

        # Save analysis in the same directory as results
        analysis_path = results_path.parent / "analysis.json"
        with open(analysis_path, "w") as f:
            json.dump({
                "benchmark": bench_name,
                "summary_table": summary,
                "paired_analysis": all_analysis,
            }, f, indent=2, default=str)
        print(f"\nAnalysis saved to {analysis_path}")


def main():
    results_dir = PROJECT_ROOT / "results"
    comparisons = [("C0", "C1"), ("C0", "C2"), ("C2", "C4"), ("C2", "C3")]

    bench_configs = get_benchmark_configs()
    if not bench_configs:
        bench_configs = {
            "heartbench": {
                "benchmark_file": "benchmark/heartbench_240.jsonl",
                "dev_file": "benchmark/heartbench_dev.jsonl",
            }
        }

    for bench_name, bench_cfg in bench_configs.items():
        analyze_benchmark(bench_name, bench_cfg, results_dir, comparisons)


if __name__ == "__main__":
    main()
