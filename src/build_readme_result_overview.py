from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_CSV = PROJECT_ROOT / "results_staged_paper" / "heartbench_v2" / "main" / "direct_comparison_summary.csv"
ASSETS_DIR = PROJECT_ROOT / "assets"
PNG_OUT = ASSETS_DIR / "readme_result_overview.png"
SVG_OUT = ASSETS_DIR / "readme_result_overview.svg"


MODEL_ORDER = ["qwen2.5:7b-instruct", "qwen2.5:0.5b-instruct"]
MODEL_LABELS = {
    "qwen2.5:7b-instruct": "Qwen2.5 7B",
    "qwen2.5:0.5b-instruct": "Qwen2.5 0.5B",
}
MODEL_COLORS = {
    "qwen2.5:7b-instruct": "#1d4ed8",
    "qwen2.5:0.5b-instruct": "#0f766e",
}


def load_summary() -> pd.DataFrame:
    df = pd.read_csv(RESULTS_CSV)
    return df


def metric_rows(df: pd.DataFrame, metric_names: list[str]) -> pd.DataFrame:
    subset = df[df["metric"].isin(metric_names)].copy()
    subset["model_order"] = subset["model"].map({m: i for i, m in enumerate(MODEL_ORDER)})
    subset = subset.sort_values(["metric", "model_order"])
    return subset


def draw_panel(ax, df: pd.DataFrame, metric_order: list[str], title: str, xlim: tuple[float, float]) -> None:
    y_positions = []
    y_labels = []
    bar_height = 0.34

    for metric_idx, metric in enumerate(metric_order):
        base = metric_idx * 1.5
        metric_df = df[df["metric"] == metric]
        for model_idx, model in enumerate(MODEL_ORDER):
            row = metric_df[metric_df["model"] == model].iloc[0]
            y = base + (model_idx - 0.5) * bar_height
            diff = row["mean_diff"]
            ci_low = row["bootstrap.ci_low"]
            ci_high = row["bootstrap.ci_high"]
            p_value = row["permutation.p_value"]

            ax.barh(y, diff, height=bar_height * 0.9, color=MODEL_COLORS[model], alpha=0.9)
            ax.errorbar(
                diff,
                y,
                xerr=[[diff - ci_low], [ci_high - diff]],
                fmt="none",
                ecolor="#111827",
                elinewidth=1.1,
                capsize=3,
            )

            sig = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else "n.s."
            offset = 0.01 if diff >= 0 else -0.01
            ax.text(
                diff + offset,
                y,
                sig,
                va="center",
                ha="left" if diff >= 0 else "right",
                fontsize=9,
                color="#111827",
                fontweight="bold",
            )

        y_positions.append(base)
        y_labels.append(metric)

    ax.axvline(0, color="#9ca3af", linewidth=1, linestyle="--")
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=10)
    ax.set_xlim(*xlim)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_summary()

    first_pass_metrics = [
        "J1 heart shift",
        "J1 act shift",
    ]
    explanation_metrics = [
        "Explanation Christianization",
        "Explanation heart-focus\n(lexical controlled)",
        "Explanation restructuring",
    ]

    metric_name_map = {
        "j1_heart_correct": "J1 heart shift",
        "j1_act_correct": "J1 act shift",
        "explanation_christianization_score": "Explanation Christianization",
        "explanation_heart_focus_controlled": "Explanation heart-focus\n(lexical controlled)",
        "explanation_structure_score": "Explanation restructuring",
    }

    selected = metric_rows(
        df,
        [
            "j1_heart_correct",
            "j1_act_correct",
            "explanation_christianization_score",
            "explanation_heart_focus_controlled",
            "explanation_structure_score",
        ],
    ).copy()
    selected["metric"] = selected["metric"].map(metric_name_map)

    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "figure.facecolor": "white",
        }
    )

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6), constrained_layout=True)

    draw_panel(
        axes[0],
        selected[selected["metric"].isin(first_pass_metrics)],
        first_pass_metrics,
        title="First-pass judgment shift\n(Christian pre - secular pre)",
        xlim=(-0.09, 0.09),
    )
    draw_panel(
        axes[1],
        selected[selected["metric"].isin(explanation_metrics)],
        explanation_metrics,
        title="Explanation-layer shift\n(Christian post - secular post)",
        xlim=(-0.01, 0.24),
    )

    axes[0].set_xlabel("Paired item-level mean difference")
    axes[1].set_xlabel("Paired item-level mean difference")

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=MODEL_COLORS[m], label=MODEL_LABELS[m])
        for m in MODEL_ORDER
    ]
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.02))

    fig.suptitle(
        "Christian framing shifts explanation language much more than first-pass judgment",
        fontsize=16,
        fontweight="bold",
        y=1.08,
    )
    fig.text(
        0.5,
        1.01,
        "HeartBench-v2 staged main results. Error bars show bootstrap 95% CIs. "
        "Asterisks mark paired permutation significance.",
        ha="center",
        fontsize=10,
        color="#374151",
    )

    fig.savefig(PNG_OUT, dpi=220, bbox_inches="tight")
    fig.savefig(SVG_OUT, bbox_inches="tight")
    print(f"Saved {PNG_OUT}")
    print(f"Saved {SVG_OUT}")


if __name__ == "__main__":
    main()
