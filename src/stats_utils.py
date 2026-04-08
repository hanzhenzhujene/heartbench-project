#!/usr/bin/env python3
"""Shared statistical helpers for corrected analyses."""

import numpy as np
from scipy import stats as scipy_stats


def bootstrap_ci(values: list[bool], n_boot: int = 1000, seed: int = 42,
                 alpha: float = 0.05) -> dict:
    """Compute a bootstrap confidence interval for accuracy."""
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
    """Bootstrap confidence interval for paired accuracy differences (B - A)."""
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
    """McNemar's test for paired binary outcomes."""
    if len(correct_a) != len(correct_b):
        return {"statistic": None, "p_value": None, "n": 0}

    b_right_a_wrong = 0
    b_wrong_a_right = 0

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
    """Condition accuracy minus baseline accuracy."""
    if not baseline_correct or not condition_correct:
        return {"gain": None}
    base_acc = sum(baseline_correct) / len(baseline_correct)
    cond_acc = sum(condition_correct) / len(condition_correct)
    return {
        "baseline_accuracy": float(base_acc),
        "condition_accuracy": float(cond_acc),
        "gain": float(cond_acc - base_acc),
    }
