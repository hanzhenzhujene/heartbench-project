#!/usr/bin/env python3
"""Analyze staged J1 / explanation / J2 mechanism results."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from stats_utils import (
    bootstrap_mean_ci,
    bootstrap_numeric_diff_ci,
    paired_effect_size,
    paired_permutation_test,
)
from utils import PROJECT_ROOT, get_config, load_jsonl, load_yaml

TOKEN_RE = re.compile(r"[a-z']+")

DIRECT_COMPARISONS = [
    {
        "comparison": "christian_pre_vs_secular_pre_j1_heart",
        "condition_a": "secular_pre",
        "condition_b": "christian_pre",
        "metric": "j1_heart_correct",
        "label": "J1 heart correctness",
    },
    {
        "comparison": "christian_pre_vs_secular_pre_j1_act",
        "condition_a": "secular_pre",
        "condition_b": "christian_pre",
        "metric": "j1_act_correct",
        "label": "J1 act correctness",
    },
    {
        "comparison": "christian_post_vs_secular_post_christianization",
        "condition_a": "secular_post",
        "condition_b": "christian_post",
        "metric": "explanation_christianization_score",
        "label": "Explanation Christianization",
    },
    {
        "comparison": "christian_post_vs_secular_post_heart_focus_inclusive",
        "condition_a": "secular_post",
        "condition_b": "christian_post",
        "metric": "explanation_heart_focus_inclusive",
        "label": "Explanation heart-focus (inclusive)",
    },
    {
        "comparison": "christian_post_vs_secular_post_heart_focus_controlled",
        "condition_a": "secular_post",
        "condition_b": "christian_post",
        "metric": "explanation_heart_focus_controlled",
        "label": "Explanation heart-focus (lexical controlled)",
    },
    {
        "comparison": "christian_post_vs_secular_post_structure",
        "condition_a": "secular_post",
        "condition_b": "christian_post",
        "metric": "explanation_structure_score",
        "label": "Explanation restructuring score",
    },
    {
        "comparison": "christian_post_vs_secular_post_any_revision",
        "condition_a": "secular_post",
        "condition_b": "christian_post",
        "metric": "any_revision",
        "label": "Any J1->J2 revision rate",
    },
    {
        "comparison": "christian_post_vs_secular_post_heart_revision",
        "condition_a": "secular_post",
        "condition_b": "christian_post",
        "metric": "heart_revision",
        "label": "Heart J1->J2 revision rate",
    },
    {
        "comparison": "christian_post_vs_secular_post_act_revision",
        "condition_a": "secular_post",
        "condition_b": "christian_post",
        "metric": "act_revision",
        "label": "Act J1->J2 revision rate",
    },
]


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def count_matches(text: str, lexicon: list[str]) -> int:
    text_lower = text.lower()
    tokens = Counter(tokenize(text))
    total = 0
    for term in lexicon:
        if " " in term:
            total += text_lower.count(term.lower())
        else:
            total += tokens[term.lower()]
    return total


def structure_metrics(text: str, lexicon_cfg: dict) -> dict:
    text_lower = text.lower()
    category_presence = {}
    total_matches = 0
    for category, terms in lexicon_cfg["lexicons"]["reasoning_structure"].items():
        matches = count_matches(text, terms)
        total_matches += matches
        category_presence[category] = 1.0 if matches > 0 else 0.0
    token_count = max(len(tokenize(text)), 1)
    return {
        "explanation_structure_score": float(np.mean(list(category_presence.values()))),
        "explanation_structure_density": total_matches / token_count,
    }


def label_correct(pred: str | None, gold: str | None) -> float | None:
    if pred is None or gold is None:
        return None
    return 1.0 if pred == gold else 0.0


def consensus_or_mixed(values: pd.Series) -> str | None:
    vals = [v for v in values.tolist() if pd.notna(v)]
    if not vals:
        return None
    unique = set(vals)
    if len(unique) == 1:
        return vals[0]
    return "mixed"


def enrich_rows(rows: list[dict], lexicon_cfg: dict) -> pd.DataFrame:
    enriched = []
    christian_terms = lexicon_cfg["lexicons"]["christian_echo"]
    secular_terms = lexicon_cfg["lexicons"]["secular_echo"]
    heart_terms = lexicon_cfg["lexicons"]["heart_semantic"]
    act_terms = lexicon_cfg["lexicons"]["act_semantic"]
    controlled_heart_terms = [
        term for term in heart_terms if term not in set(christian_terms) | set(secular_terms)
    ]

    for row in rows:
        explanation = row.get("explanation_text") or ""
        token_count = len(tokenize(explanation))
        christian_echo = count_matches(explanation, christian_terms) if explanation else 0
        secular_echo = count_matches(explanation, secular_terms) if explanation else 0
        heart_matches = count_matches(explanation, heart_terms) if explanation else 0
        controlled_heart_matches = count_matches(explanation, controlled_heart_terms) if explanation else 0
        act_matches = count_matches(explanation, act_terms) if explanation else 0
        structure = structure_metrics(explanation, lexicon_cfg) if explanation else {
            "explanation_structure_score": None,
            "explanation_structure_density": None,
        }
        active_frame_echo = 0
        if row["frame_family"] == "christian":
            active_frame_echo = christian_echo
        elif row["frame_family"] == "secular":
            active_frame_echo = secular_echo

        j1_heart_correct = label_correct(row.get("j1_heart_worse"), row.get("gold_heart_worse"))
        j1_act_correct = label_correct(row.get("j1_act_worse"), row.get("gold_act_worse"))
        j2_heart_correct = label_correct(row.get("j2_heart_worse"), row.get("gold_heart_worse"))
        j2_act_correct = label_correct(row.get("j2_act_worse"), row.get("gold_act_worse"))

        heart_revision = None
        act_revision = None
        any_revision = None
        heart_revision_toward_gold = None
        heart_revision_away_from_gold = None
        act_revision_toward_gold = None
        act_revision_away_from_gold = None
        if row.get("j2_heart_worse") is not None and row.get("j1_heart_worse") is not None:
            heart_revision = 1.0 if row["j2_heart_worse"] != row["j1_heart_worse"] else 0.0
            if heart_revision and j1_heart_correct is not None and j2_heart_correct is not None:
                heart_revision_toward_gold = 1.0 if j2_heart_correct > j1_heart_correct else 0.0
                heart_revision_away_from_gold = 1.0 if j2_heart_correct < j1_heart_correct else 0.0
            elif heart_revision == 0:
                heart_revision_toward_gold = 0.0
                heart_revision_away_from_gold = 0.0
        if row.get("j2_act_worse") is not None and row.get("j1_act_worse") is not None:
            act_revision = 1.0 if row["j2_act_worse"] != row["j1_act_worse"] else 0.0
            if act_revision and j1_act_correct is not None and j2_act_correct is not None:
                act_revision_toward_gold = 1.0 if j2_act_correct > j1_act_correct else 0.0
                act_revision_away_from_gold = 1.0 if j2_act_correct < j1_act_correct else 0.0
            elif act_revision == 0:
                act_revision_toward_gold = 0.0
                act_revision_away_from_gold = 0.0
        if heart_revision is not None or act_revision is not None:
            any_revision = 1.0 if (heart_revision or act_revision) else 0.0

        enriched.append(
            {
                **row,
                "explanation_token_count": token_count if explanation else None,
                "explanation_christian_echo_rate": (christian_echo / token_count) if token_count else None,
                "explanation_secular_echo_rate": (secular_echo / token_count) if token_count else None,
                "explanation_direct_frame_echo_rate": (active_frame_echo / token_count) if token_count else None,
                "explanation_christianization_score": (christian_echo / token_count) if token_count else None,
                "explanation_heart_semantic_rate_inclusive": (heart_matches / token_count) if token_count else None,
                "explanation_heart_semantic_rate_controlled": (controlled_heart_matches / token_count) if token_count else None,
                "explanation_act_semantic_rate": (act_matches / token_count) if token_count else None,
                "explanation_heart_focus_inclusive": ((heart_matches - act_matches) / token_count) if token_count else None,
                "explanation_heart_focus_controlled": ((controlled_heart_matches - act_matches) / token_count) if token_count else None,
                "j1_heart_correct": j1_heart_correct,
                "j1_act_correct": j1_act_correct,
                "j2_heart_correct": j2_heart_correct,
                "j2_act_correct": j2_act_correct,
                "heart_revision": heart_revision,
                "act_revision": act_revision,
                "any_revision": any_revision,
                "heart_revision_toward_gold": heart_revision_toward_gold,
                "heart_revision_away_from_gold": heart_revision_away_from_gold,
                "act_revision_toward_gold": act_revision_toward_gold,
                "act_revision_away_from_gold": act_revision_away_from_gold,
                **structure,
            }
        )
    return pd.DataFrame(enriched)


def aggregate_variants(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = [
        "j1_heart_correct",
        "j1_act_correct",
        "j2_heart_correct",
        "j2_act_correct",
        "heart_revision",
        "act_revision",
        "any_revision",
        "heart_revision_toward_gold",
        "heart_revision_away_from_gold",
        "act_revision_toward_gold",
        "act_revision_away_from_gold",
        "explanation_christianization_score",
        "explanation_direct_frame_echo_rate",
        "explanation_heart_semantic_rate_inclusive",
        "explanation_heart_semantic_rate_controlled",
        "explanation_act_semantic_rate",
        "explanation_heart_focus_inclusive",
        "explanation_heart_focus_controlled",
        "explanation_structure_score",
        "explanation_structure_density",
        "explanation_token_count",
    ]
    group_cols = [
        "benchmark",
        "benchmark_split",
        "item_id",
        "model",
        "model_id",
        "condition",
        "condition_name",
        "frame_family",
        "frame_placement",
        "family",
        "difficulty",
        "domain",
        "setting_type",
        "dissociation_target",
        "gold_heart_worse",
        "gold_act_worse",
    ]

    agg = (
        df.groupby(group_cols, dropna=False)
        .agg({**{col: "mean" for col in numeric_cols},
              "frame_variant_id": "nunique",
              "j1_heart_worse": consensus_or_mixed,
              "j1_act_worse": consensus_or_mixed,
              "j2_heart_worse": consensus_or_mixed,
              "j2_act_worse": consensus_or_mixed})
        .reset_index()
        .rename(columns={"frame_variant_id": "n_prompt_variants"})
    )
    return agg


def paired_metric_summary(df: pd.DataFrame, model: str, cond_a: str, cond_b: str, metric: str, subset=None) -> dict:
    subset_df = df[df["model"] == model]
    if subset is not None:
        subset_df = subset(subset_df)
    a = subset_df[subset_df["condition"] == cond_a][["item_id", metric]].rename(columns={metric: "a"})
    b = subset_df[subset_df["condition"] == cond_b][["item_id", metric]].rename(columns={metric: "b"})
    merged = a.merge(b, on="item_id", how="inner").dropna()
    if merged.empty:
        return {
            "model": model,
            "condition_a": cond_a,
            "condition_b": cond_b,
            "metric": metric,
            "n_items": 0,
            "mean_a": None,
            "mean_b": None,
            "mean_diff": None,
            "bootstrap": {"mean_diff": None, "ci_low": None, "ci_high": None, "n": 0},
            "permutation": {"observed_mean_diff": None, "p_value": None, "n": 0},
            "effect_size": {"effect_size_dz": None, "mean_diff": None, "sd_diff": None, "n": 0},
        }

    values_a = merged["a"].astype(float).tolist()
    values_b = merged["b"].astype(float).tolist()
    return {
        "model": model,
        "condition_a": cond_a,
        "condition_b": cond_b,
        "metric": metric,
        "n_items": len(merged),
        "mean_a": float(np.mean(values_a)),
        "mean_b": float(np.mean(values_b)),
        "mean_diff": float(np.mean(np.array(values_b) - np.array(values_a))),
        "bootstrap": bootstrap_numeric_diff_ci(values_a, values_b),
        "permutation": paired_permutation_test(values_a, values_b),
        "effect_size": paired_effect_size(values_a, values_b),
    }


def summarize_condition(df: pd.DataFrame, model: str, condition: str, metric: str) -> dict:
    values = (
        df[(df["model"] == model) & (df["condition"] == condition)][metric]
        .dropna()
        .astype(float)
        .tolist()
    )
    ci = bootstrap_mean_ci(values)
    return {
        "model": model,
        "condition": condition,
        "metric": metric,
        **ci,
    }


def baseline_shift_summary(df: pd.DataFrame, model: str, condition: str, metric: str) -> dict:
    if condition == "baseline":
        return {
            "model": model,
            "condition": condition,
            "metric": metric,
            "mean_diff": 0.0,
            "ci_low": 0.0,
            "ci_high": 0.0,
            "n": 0,
        }
    base = df[(df["model"] == model) & (df["condition"] == "baseline")][["item_id", metric]].rename(columns={metric: "base"})
    cond = df[(df["model"] == model) & (df["condition"] == condition)][["item_id", metric]].rename(columns={metric: "cond"})
    merged = base.merge(cond, on="item_id", how="inner").dropna()
    if merged.empty:
        return {"model": model, "condition": condition, "metric": metric, "mean_diff": None, "ci_low": None, "ci_high": None, "n": 0}
    diffs = (merged["cond"] - merged["base"]).astype(float).tolist()
    ci = bootstrap_mean_ci(diffs)
    return {
        "model": model,
        "condition": condition,
        "metric": metric,
        "mean_diff": ci["mean"],
        "ci_low": ci["ci_low"],
        "ci_high": ci["ci_high"],
        "n": ci["n"],
    }


def interpret_effect(summary: dict, positive_label: str, negative_label: str) -> str:
    diff = summary.get("mean_diff")
    p_val = ((summary.get("permutation") or {}).get("p_value"))
    if diff is None or p_val is None:
        return "Insufficient paired data."
    if abs(diff) < 1e-12:
        direction = "No directional difference"
    else:
        direction = positive_label if diff > 0 else negative_label
    if p_val < 0.01:
        strength = "clear"
    elif p_val < 0.05:
        strength = "modest"
    else:
        strength = "weak or null"
    return f"{direction}; {strength} paired difference (diff={diff:.3f}, p={p_val:.4g})."


def direct_comparison_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model in sorted(df["model"].unique()):
        for spec in DIRECT_COMPARISONS:
            summary = paired_metric_summary(
                df,
                model=model,
                cond_a=spec["condition_a"],
                cond_b=spec["condition_b"],
                metric=spec["metric"],
            )
            summary["comparison"] = spec["comparison"]
            summary["label"] = spec["label"]
            summary["interpretation"] = interpret_effect(
                summary,
                positive_label=f"{spec['condition_b']} exceeds {spec['condition_a']} on {spec['label']}",
                negative_label=f"{spec['condition_b']} falls below {spec['condition_a']} on {spec['label']}",
            )
            rows.append(summary)
    return pd.json_normalize(rows)


def post_explanation_without_j1_change(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model in sorted(df["model"].unique()):
        a = df[(df["model"] == model) & (df["condition"] == "secular_post")][[
            "item_id",
            "j1_heart_worse",
            "j1_act_worse",
            "explanation_heart_focus_controlled",
            "explanation_christianization_score",
            "explanation_structure_score",
        ]].rename(columns=lambda c: f"a_{c}" if c != "item_id" else c)
        b = df[(df["model"] == model) & (df["condition"] == "christian_post")][[
            "item_id",
            "j1_heart_worse",
            "j1_act_worse",
            "explanation_heart_focus_controlled",
            "explanation_christianization_score",
            "explanation_structure_score",
        ]].rename(columns=lambda c: f"b_{c}" if c != "item_id" else c)
        merged = a.merge(b, on="item_id", how="inner")
        if merged.empty:
            continue
        matched = merged[
            (merged["a_j1_heart_worse"] == merged["b_j1_heart_worse"])
            & (merged["a_j1_act_worse"] == merged["b_j1_act_worse"])
        ]
        for metric in [
            "explanation_heart_focus_controlled",
            "explanation_christianization_score",
            "explanation_structure_score",
        ]:
            aa = f"a_{metric}"
            bb = f"b_{metric}"
            sub = matched[["item_id", aa, bb]].dropna()
            if sub.empty:
                continue
            values_a = sub[aa].astype(float).tolist()
            values_b = sub[bb].astype(float).tolist()
            rows.append(
                {
                    "model": model,
                    "metric": metric,
                    "n_items_same_j1": len(sub),
                    "same_j1_rate": len(matched) / len(merged),
                    "mean_diff": float(np.mean(np.array(values_b) - np.array(values_a))),
                    "bootstrap": bootstrap_numeric_diff_ci(values_a, values_b),
                    "permutation": paired_permutation_test(values_a, values_b),
                    "effect_size": paired_effect_size(values_a, values_b),
                    "interpretation": interpret_effect(
                        {
                            "mean_diff": float(np.mean(np.array(values_b) - np.array(values_a))),
                            "permutation": paired_permutation_test(values_a, values_b),
                        },
                        positive_label="Christian post raises explanation metric even when J1 is unchanged",
                        negative_label="Christian post lowers explanation metric even when J1 is unchanged",
                    ),
                }
            )
    return pd.json_normalize(rows)


def dissociation_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model in sorted(df["model"].unique()):
        base = df[(df["model"] == model) & (df["condition"] == "baseline")][[
            "item_id",
            "j1_heart_correct",
            "explanation_heart_focus_controlled",
        ]].rename(
            columns={
                "j1_heart_correct": "base_j1_heart_correct",
                "explanation_heart_focus_controlled": "base_explanation_heart_focus_controlled",
            }
        )
        for condition in sorted(df["condition"].unique()):
            cond = df[(df["model"] == model) & (df["condition"] == condition)][[
                "item_id",
                "j1_heart_correct",
                "explanation_heart_focus_controlled",
            ]].rename(
                columns={
                    "j1_heart_correct": "cond_j1_heart_correct",
                    "explanation_heart_focus_controlled": "cond_explanation_heart_focus_controlled",
                }
            )
            merged = base.merge(cond, on="item_id", how="inner").dropna()
            if merged.empty:
                rows.append(
                    {
                        "model": model,
                        "condition": condition,
                        "j1_heart_shift": None,
                        "explanation_shift": None,
                        "pearson_r": None,
                        "pearson_p": None,
                    }
                )
                continue
            x = (merged["cond_j1_heart_correct"] - merged["base_j1_heart_correct"]).astype(float)
            y = (merged["cond_explanation_heart_focus_controlled"] - merged["base_explanation_heart_focus_controlled"]).astype(float)
            if len(merged) > 2 and x.nunique() > 1 and y.nunique() > 1:
                r, p = scipy_stats.pearsonr(x, y)
            else:
                r, p = None, None
            rows.append(
                {
                    "model": model,
                    "condition": condition,
                    "j1_heart_shift": float(x.mean()),
                    "explanation_shift": float(y.mean()),
                    "pearson_r": None if r is None else float(r),
                    "pearson_p": None if p is None else float(p),
                }
            )
    return pd.DataFrame(rows)


def heterogeneity_table(df: pd.DataFrame, experiment_cfg: dict) -> pd.DataFrame:
    rows = []
    for model in sorted(df["model"].unique()):
        for slice_name, families in experiment_cfg["heterogeneity_slices"].items():
            subset = lambda frame, fams=families: frame[frame["family"].isin(fams)]
            for label, cond_a, cond_b, metric in [
                ("J1 heart (christian_pre vs secular_pre)", "secular_pre", "christian_pre", "j1_heart_correct"),
                ("Explanation controlled heart-focus (christian_post vs secular_post)", "secular_post", "christian_post", "explanation_heart_focus_controlled"),
            ]:
                summary = paired_metric_summary(
                    df,
                    model=model,
                    cond_a=cond_a,
                    cond_b=cond_b,
                    metric=metric,
                    subset=subset,
                )
                rows.append(
                    {
                        "model": model,
                        "slice": slice_name,
                        "metric_label": label,
                        **summary,
                    }
                )
    return pd.json_normalize(rows)


def save_outputs(output_dir: Path, item_df: pd.DataFrame, agg_df: pd.DataFrame, summary_df: pd.DataFrame,
                 baseline_df: pd.DataFrame, direct_df: pd.DataFrame, dissociation_df: pd.DataFrame,
                 same_j1_df: pd.DataFrame, hetero_df: pd.DataFrame, analysis_json: dict) -> None:
    ensure = output_dir / "figure_data"
    ensure.mkdir(parents=True, exist_ok=True)

    item_df.to_csv(output_dir / "item_level_metrics.csv", index=False)
    agg_df.to_csv(output_dir / "aggregated_item_metrics.csv", index=False)
    summary_df.to_csv(output_dir / "summary_by_condition.csv", index=False)
    baseline_df.to_csv(output_dir / "baseline_shift_summary.csv", index=False)
    direct_df.to_csv(output_dir / "direct_comparison_summary.csv", index=False)
    dissociation_df.to_csv(output_dir / "figure_data" / "judgment_vs_explanation_dissociation.csv", index=False)
    same_j1_df.to_csv(output_dir / "same_j1_explanation_shift.csv", index=False)
    hetero_df.to_csv(output_dir / "heterogeneity_summary.csv", index=False)

    first_pass_figure = baseline_df[baseline_df["metric"].isin(["j1_heart_correct", "j1_act_correct"])].copy()
    first_pass_figure.to_csv(output_dir / "figure_data" / "first_pass_shift.csv", index=False)

    explanation_figure = summary_df[
        summary_df["metric"].isin(
            [
                "explanation_direct_frame_echo_rate",
                "explanation_heart_focus_inclusive",
                "explanation_heart_focus_controlled",
                "explanation_christianization_score",
                "explanation_structure_score",
            ]
        )
    ].copy()
    explanation_figure.to_csv(output_dir / "figure_data" / "explanation_layer_effects.csv", index=False)

    revision_figure = summary_df[
        summary_df["metric"].isin(
            [
                "any_revision",
                "heart_revision",
                "act_revision",
                "heart_revision_toward_gold",
                "act_revision_toward_gold",
            ]
        )
    ].copy()
    revision_figure.to_csv(output_dir / "figure_data" / "revision_rates.csv", index=False)

    hetero_df.to_csv(output_dir / "figure_data" / "heterogeneity_effects.csv", index=False)

    with open(output_dir / "analysis.json", "w") as f:
        json.dump(analysis_json, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Analyze staged paper results")
    parser.add_argument("--benchmark", type=str, default=None, help="Optional benchmark key")
    parser.add_argument(
        "--results-root",
        type=str,
        default="results_staged_paper",
        help="Results root directory relative to project root",
    )
    args = parser.parse_args()

    experiment_cfg = get_config("experiment_staged_paper")
    lexicon_cfg = load_yaml(PROJECT_ROOT / "configs" / "explanation_lexicons.yaml")

    benchmark_key = args.benchmark or experiment_cfg["default_benchmark"]
    if benchmark_key not in experiment_cfg["benchmarks"]:
        raise SystemExit(f"Unknown benchmark: {benchmark_key}")

    benchmark_cfg = experiment_cfg["benchmarks"][benchmark_key]
    output_dir = PROJECT_ROOT / args.results_root / benchmark_key / benchmark_cfg["split"]
    results_path = output_dir / "all_results.jsonl"
    if results_path.exists():
        rows = load_jsonl(results_path)
    else:
        rows = []
        for path in sorted(output_dir.glob("*.jsonl")):
            if path.name == "all_results.jsonl":
                continue
            rows.extend(load_jsonl(path))
        if not rows:
            raise SystemExit(f"Missing staged results: {results_path}")

    item_df = enrich_rows(rows, lexicon_cfg)
    agg_df = aggregate_variants(item_df)

    metrics_for_summary = [
        "j1_heart_correct",
        "j1_act_correct",
        "j2_heart_correct",
        "j2_act_correct",
        "any_revision",
        "heart_revision",
        "act_revision",
        "heart_revision_toward_gold",
        "act_revision_toward_gold",
        "explanation_direct_frame_echo_rate",
        "explanation_christianization_score",
        "explanation_heart_focus_inclusive",
        "explanation_heart_focus_controlled",
        "explanation_structure_score",
    ]

    summary_rows = []
    baseline_rows = []
    for model in sorted(agg_df["model"].unique()):
        for condition in sorted(agg_df["condition"].unique()):
            for metric in metrics_for_summary:
                summary_rows.append(summarize_condition(agg_df, model, condition, metric))
                baseline_rows.append(baseline_shift_summary(agg_df, model, condition, metric))
    summary_df = pd.DataFrame(summary_rows)
    baseline_df = pd.DataFrame(baseline_rows)
    direct_df = direct_comparison_table(agg_df)
    dissociation_df = dissociation_summary(agg_df)
    same_j1_df = post_explanation_without_j1_change(agg_df)
    hetero_df = heterogeneity_table(agg_df, experiment_cfg)

    analysis_json = {
        "experiment": experiment_cfg["experiment"]["name"],
        "benchmark": benchmark_key,
        "split": benchmark_cfg["split"],
        "models_present": sorted(agg_df["model"].unique().tolist()),
        "direct_comparisons": direct_df.to_dict(orient="records"),
        "same_j1_explanation_shift": same_j1_df.to_dict(orient="records"),
        "judgment_vs_explanation_dissociation": dissociation_df.to_dict(orient="records"),
        "heterogeneity": hetero_df.to_dict(orient="records"),
    }

    save_outputs(
        output_dir,
        item_df,
        agg_df,
        summary_df,
        baseline_df,
        direct_df,
        dissociation_df,
        same_j1_df,
        hetero_df,
        analysis_json,
    )
    print(f"Saved staged analysis outputs to {output_dir}")


if __name__ == "__main__":
    main()
