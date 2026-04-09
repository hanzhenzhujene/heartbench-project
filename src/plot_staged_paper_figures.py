#!/usr/bin/env python3
"""Generate paper-style figures for the staged J1 / E / J2 experiment."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from utils import PROJECT_ROOT, get_config

CONDITION_ORDER = [
    "baseline",
    "secular_pre",
    "christian_pre",
    "secular_post",
    "christian_post",
    "judgment_only",
]

CONDITION_LABELS = {
    "baseline": "Baseline",
    "secular_pre": "Secular Pre",
    "christian_pre": "Christian Pre",
    "secular_post": "Secular Post",
    "christian_post": "Christian Post",
    "judgment_only": "Judgment Only",
}

MODEL_LABELS = {
    "qwen2.5:7b-instruct": "qwen2.5:7b-instruct",
    "qwen2.5:0.5b-instruct": "qwen2.5:0.5b-instruct",
    "Qwen2.5-7B-Instruct": "Qwen2.5-7B-Instruct",
    "Qwen2.5-0.5B-Instruct": "Qwen2.5-0.5B-Instruct",
}

METRIC_LABELS = {
    "j1_heart_correct": "J1 Heart Shift vs Baseline",
    "j1_act_correct": "J1 Act Shift vs Baseline",
    "explanation_direct_frame_echo_rate": "Direct Frame Echo",
    "explanation_christianization_score": "Christianized Language",
    "explanation_heart_focus_inclusive": "Heart Focus (Inclusive)",
    "explanation_heart_focus_controlled": "Heart Focus (Echo Controlled)",
    "explanation_structure_score": "Explanation Restructuring",
    "any_revision": "Any Revision",
    "heart_revision": "Heart Revision",
    "act_revision": "Act Revision",
}


def set_theme():
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.15)
    plt.rcParams["figure.dpi"] = 160
    plt.rcParams["savefig.dpi"] = 300


def load_analysis_tables(output_dir: Path):
    figure_dir = output_dir / "figure_data"
    return {
        "first_pass": pd.read_csv(figure_dir / "first_pass_shift.csv"),
        "explanation": pd.read_csv(figure_dir / "explanation_layer_effects.csv"),
        "dissociation": pd.read_csv(figure_dir / "judgment_vs_explanation_dissociation.csv"),
        "revision": pd.read_csv(figure_dir / "revision_rates.csv"),
        "heterogeneity": pd.read_csv(figure_dir / "heterogeneity_effects.csv"),
    }


def first_pass_shift_figure(df: pd.DataFrame, out_dir: Path):
    plot_df = df[df["condition"].isin(CONDITION_ORDER)].copy()
    plot_df["condition_label"] = plot_df["condition"].map(CONDITION_LABELS)
    plot_df["metric_label"] = plot_df["metric"].map(METRIC_LABELS)

    models = [m for m in MODEL_LABELS if m in plot_df["model"].unique()]
    fig, axes = plt.subplots(1, len(models), figsize=(6.5 * len(models), 4.2), sharey=True)
    if len(models) == 1:
        axes = [axes]

    y_min = plot_df["ci_low"].min(skipna=True)
    y_max = plot_df["ci_high"].max(skipna=True)

    palette = {
        "J1 Heart Shift vs Baseline": "#0B7285",
        "J1 Act Shift vs Baseline": "#B08968",
    }

    for ax, model in zip(axes, models):
        model_df = plot_df[plot_df["model"] == model]
        for metric_label, metric_df in model_df.groupby("metric_label"):
            x = [CONDITION_ORDER.index(cond) for cond in metric_df["condition"]]
            ax.errorbar(
                x,
                metric_df["mean_diff"],
                yerr=[
                    metric_df["mean_diff"] - metric_df["ci_low"],
                    metric_df["ci_high"] - metric_df["mean_diff"],
                ],
                fmt="o-",
                lw=2.2,
                ms=6,
                capsize=4,
                label=metric_label,
                color=palette[metric_label],
            )
        ax.axhline(0, color="black", lw=1, alpha=0.6)
        ax.set_xticks(range(len(CONDITION_ORDER)))
        ax.set_xticklabels([CONDITION_LABELS[c] for c in CONDITION_ORDER], rotation=35, ha="right")
        ax.set_title(MODEL_LABELS[model])
        ax.set_xlabel("Condition")
    axes[0].set_ylabel("Mean Shift Relative to Baseline")
    axes[0].set_ylim(y_min - 0.02, y_max + 0.02)
    axes[-1].legend(frameon=False, loc="upper right")
    fig.suptitle("First-Pass Judgment Shift Is Concentrated in Heart-Sensitive Metrics", y=1.02)
    fig.tight_layout()
    fig.savefig(out_dir / "figure_1_first_pass_shift.png", bbox_inches="tight")
    fig.savefig(out_dir / "figure_1_first_pass_shift.pdf", bbox_inches="tight")
    plt.close(fig)


def explanation_layer_figure(df: pd.DataFrame, out_dir: Path):
    metric_order = [
        "explanation_direct_frame_echo_rate",
        "explanation_heart_focus_inclusive",
        "explanation_heart_focus_controlled",
        "explanation_structure_score",
    ]
    plot_df = df[df["condition"] != "judgment_only"].copy()
    plot_df = plot_df[plot_df["metric"].isin(metric_order)]
    plot_df["condition_label"] = plot_df["condition"].map(CONDITION_LABELS)
    plot_df["metric_label"] = plot_df["metric"].map(METRIC_LABELS)

    models = [m for m in MODEL_LABELS if m in plot_df["model"].unique()]
    fig, axes = plt.subplots(len(metric_order), len(models), figsize=(5.2 * len(models), 3.0 * len(metric_order)), sharex=True)
    if len(models) == 1:
        axes = [[ax] for ax in axes]

    for row_idx, metric in enumerate(metric_order):
        metric_df = plot_df[plot_df["metric"] == metric]
        y_min = metric_df["ci_low"].min(skipna=True)
        y_max = metric_df["ci_high"].max(skipna=True)
        for col_idx, model in enumerate(models):
            ax = axes[row_idx][col_idx]
            sub = metric_df[metric_df["model"] == model]
            x = [CONDITION_ORDER.index(cond) for cond in sub["condition"]]
            ax.errorbar(
                x,
                sub["mean"],
                yerr=[sub["mean"] - sub["ci_low"], sub["ci_high"] - sub["mean"]],
                fmt="o-",
                lw=2.0,
                ms=5,
                capsize=3,
                color="#7A3E65" if "christian" in metric else "#1D4E89",
            )
            ax.set_ylim(y_min - 0.02, y_max + 0.02)
            if row_idx == 0:
                ax.set_title(MODEL_LABELS[model])
            if col_idx == 0:
                ax.set_ylabel(METRIC_LABELS[metric])
            if row_idx == len(metric_order) - 1:
                ax.set_xticks(range(len(CONDITION_ORDER[:-1])))
                ax.set_xticklabels([CONDITION_LABELS[c] for c in CONDITION_ORDER[:-1]], rotation=35, ha="right")
            else:
                ax.set_xticks(range(len(CONDITION_ORDER[:-1])))
                ax.set_xticklabels([])
    fig.suptitle("Explanation-Layer Effects Persist Beyond Direct Frame Echo", y=1.01)
    fig.tight_layout()
    fig.savefig(out_dir / "figure_2_explanation_layer_effects.png", bbox_inches="tight")
    fig.savefig(out_dir / "figure_2_explanation_layer_effects.pdf", bbox_inches="tight")
    plt.close(fig)


def dissociation_scatter_figure(df: pd.DataFrame, out_dir: Path):
    plot_df = df[df["condition"] != "baseline"].copy()
    models = [m for m in MODEL_LABELS if m in plot_df["model"].unique()]
    fig, axes = plt.subplots(1, len(models), figsize=(5.8 * len(models), 4.8), sharex=True, sharey=True)
    if len(models) == 1:
        axes = [axes]

    for ax, model in zip(axes, models):
        sub = plot_df[plot_df["model"] == model]
        ax.axhline(0, color="black", lw=1, alpha=0.5)
        ax.axvline(0, color="black", lw=1, alpha=0.5)
        sns.scatterplot(
            data=sub,
            x="j1_heart_shift",
            y="explanation_shift",
            hue="condition",
            palette="Set2",
            s=70,
            ax=ax,
            legend=False,
        )
        for _, row in sub.iterrows():
            if pd.isna(row["j1_heart_shift"]) or pd.isna(row["explanation_shift"]):
                continue
            ax.text(
                row["j1_heart_shift"] + 0.002,
                row["explanation_shift"] + 0.002,
                CONDITION_LABELS.get(row["condition"], row["condition"]),
                fontsize=9,
            )
        ax.set_title(MODEL_LABELS[model])
        ax.set_xlabel("First-Pass Heart Shift vs Baseline")
    axes[0].set_ylabel("Explanation Shift vs Baseline")
    fig.suptitle("Explanation Movement Can Outrun First-Pass Judgment Movement", y=1.02)
    fig.tight_layout()
    fig.savefig(out_dir / "figure_3_judgment_vs_explanation_dissociation.png", bbox_inches="tight")
    fig.savefig(out_dir / "figure_3_judgment_vs_explanation_dissociation.pdf", bbox_inches="tight")
    plt.close(fig)


def revision_figure(df: pd.DataFrame, out_dir: Path):
    metric_order = ["any_revision", "heart_revision", "act_revision"]
    plot_df = df[df["metric"].isin(metric_order) & (df["condition"] != "judgment_only")].copy()
    plot_df["metric_label"] = plot_df["metric"].map(METRIC_LABELS)
    plot_df["condition_label"] = plot_df["condition"].map(CONDITION_LABELS)

    models = [m for m in MODEL_LABELS if m in plot_df["model"].unique()]
    fig, axes = plt.subplots(1, len(models), figsize=(6.5 * len(models), 4.6), sharey=True)
    if len(models) == 1:
        axes = [axes]

    palette = {
        "Any Revision": "#2D6A4F",
        "Heart Revision": "#40916C",
        "Act Revision": "#74C69D",
    }
    for ax, model in zip(axes, models):
        sub = plot_df[plot_df["model"] == model]
        for metric_label, metric_df in sub.groupby("metric_label"):
            x = [CONDITION_ORDER.index(cond) for cond in metric_df["condition"]]
            ax.errorbar(
                x,
                metric_df["mean"],
                yerr=[metric_df["mean"] - metric_df["ci_low"], metric_df["ci_high"] - metric_df["mean"]],
                fmt="o-",
                lw=2,
                ms=5,
                capsize=3,
                label=metric_label,
                color=palette[metric_label],
            )
        ax.set_xticks(range(len(CONDITION_ORDER[:-1])))
        ax.set_xticklabels([CONDITION_LABELS[c] for c in CONDITION_ORDER[:-1]], rotation=35, ha="right")
        ax.set_title(MODEL_LABELS[model])
        ax.set_xlabel("Condition")
    axes[0].set_ylabel("Revision Rate")
    axes[-1].legend(frameon=False, loc="upper right")
    fig.suptitle("Post Framing Can Raise Revision Pressure Even When J1 Stays Fixed", y=1.02)
    fig.tight_layout()
    fig.savefig(out_dir / "figure_4_revision_rates.png", bbox_inches="tight")
    fig.savefig(out_dir / "figure_4_revision_rates.pdf", bbox_inches="tight")
    plt.close(fig)


def heterogeneity_figure(df: pd.DataFrame, out_dir: Path):
    plot_df = df[df["metric_label"].isin([
        "J1 heart (christian_pre vs secular_pre)",
        "Explanation controlled heart-focus (christian_post vs secular_post)",
    ])].copy()
    plot_df["display_metric"] = plot_df["metric_label"]
    plot_df["ci_low"] = plot_df["bootstrap.ci_low"]
    plot_df["ci_high"] = plot_df["bootstrap.ci_high"]
    plot_df["mean_diff"] = plot_df["mean_diff"]

    models = [m for m in MODEL_LABELS if m in plot_df["model"].unique()]
    metrics = plot_df["display_metric"].dropna().unique().tolist()
    fig, axes = plt.subplots(len(metrics), len(models), figsize=(5.6 * len(models), 3.2 * len(metrics)), sharex=False)
    if len(metrics) == 1 and len(models) == 1:
        axes = [[axes]]
    elif len(metrics) == 1:
        axes = [axes]
    elif len(models) == 1:
        axes = [[ax] for ax in axes]

    for row_idx, metric in enumerate(metrics):
        for col_idx, model in enumerate(models):
            ax = axes[row_idx][col_idx]
            sub = plot_df[(plot_df["display_metric"] == metric) & (plot_df["model"] == model)].copy()
            sub = sub.sort_values("mean_diff")
            ax.axvline(0, color="black", lw=1, alpha=0.6)
            ax.errorbar(
                sub["mean_diff"],
                sub["slice"],
                xerr=[sub["mean_diff"] - sub["ci_low"], sub["ci_high"] - sub["mean_diff"]],
                fmt="o",
                color="#6A4C93",
                capsize=3,
            )
            if row_idx == 0:
                ax.set_title(MODEL_LABELS[model])
            if col_idx == 0:
                ax.set_ylabel(metric)
            ax.set_xlabel("Christian - Secular Effect")
    fig.suptitle("Framing Effects Concentrate in Motive-Salient Item Slices", y=1.02)
    fig.tight_layout()
    fig.savefig(out_dir / "figure_5_heterogeneity.png", bbox_inches="tight")
    fig.savefig(out_dir / "figure_5_heterogeneity.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Plot staged paper figures")
    parser.add_argument("--benchmark", type=str, default=None, help="Optional benchmark key")
    parser.add_argument(
        "--results-root",
        type=str,
        default="results/staged_paper",
        help="Results root directory relative to project root",
    )
    args = parser.parse_args()

    experiment_cfg = get_config("experiment_staged_paper")
    benchmark_key = args.benchmark or experiment_cfg["default_benchmark"]
    if benchmark_key not in experiment_cfg["benchmarks"]:
        raise SystemExit(f"Unknown benchmark: {benchmark_key}")
    bench_cfg = experiment_cfg["benchmarks"][benchmark_key]
    output_dir = PROJECT_ROOT / args.results_root / benchmark_key / bench_cfg["split"]
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    set_theme()
    tables = load_analysis_tables(output_dir)
    first_pass_shift_figure(tables["first_pass"], figure_dir)
    explanation_layer_figure(tables["explanation"], figure_dir)
    dissociation_scatter_figure(tables["dissociation"], figure_dir)
    revision_figure(tables["revision"], figure_dir)
    heterogeneity_figure(tables["heterogeneity"], figure_dir)
    print(f"Saved staged paper figures to {figure_dir}")


if __name__ == "__main__":
    main()
