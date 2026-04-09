from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "materials" / "assets"
PNG_OUT = ASSETS_DIR / "generated_methodology_workflow.png"
SVG_OUT = ASSETS_DIR / "generated_methodology_workflow.svg"


def add_shadow_card(
    ax,
    x,
    y,
    w,
    h,
    title,
    lines,
    facecolor,
    edgecolor,
    title_color,
    accent=None,
    body_color="#0f172a",
    body_fontsize=10.6,
    body_top_offset=0.105,
):
    shadow = FancyBboxPatch(
        (x + 0.008, y - 0.008),
        w,
        h,
        boxstyle="round,pad=0.018,rounding_size=0.03",
        linewidth=0,
        facecolor="#0f172a",
        alpha=0.08,
        zorder=1,
    )
    ax.add_patch(shadow)

    card = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.018,rounding_size=0.03",
        linewidth=1.6,
        facecolor=facecolor,
        edgecolor=edgecolor,
        zorder=2,
    )
    ax.add_patch(card)

    if accent:
        ax.add_patch(
            FancyBboxPatch(
                (x, y + h - 0.028),
                w,
                0.028,
                boxstyle="round,pad=0.0,rounding_size=0.02",
                linewidth=0,
                facecolor=accent,
                zorder=3,
            )
        )

    ax.text(
        x + 0.025,
        y + h - 0.052,
        title,
        fontsize=13.2,
        fontweight="bold",
        color=title_color,
        va="top",
        zorder=4,
    )
    ax.text(
        x + 0.025,
        y + h - body_top_offset,
        "\n".join(lines),
        fontsize=body_fontsize,
        color=body_color,
        va="top",
        linespacing=1.42,
        zorder=4,
    )


def add_section_panel(ax, x, y, w, h, label, facecolor, edgecolor):
    panel = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.018,rounding_size=0.04",
        linewidth=1.2,
        facecolor=facecolor,
        edgecolor=edgecolor,
        alpha=0.65,
        zorder=0,
    )
    ax.add_patch(panel)
    ax.text(
        x + 0.02,
        y + h - 0.03,
        label,
        fontsize=11.5,
        fontweight="bold",
        color=edgecolor,
        va="top",
        zorder=1,
    )


def add_pill(ax, x, y, w, h, label, facecolor, edgecolor, textcolor):
    pill = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.04",
        linewidth=1.2,
        facecolor=facecolor,
        edgecolor=edgecolor,
        zorder=3,
    )
    ax.add_patch(pill)
    ax.text(
        x + w / 2,
        y + h / 2,
        label,
        ha="center",
        va="center",
        fontsize=9.4,
        color=textcolor,
        fontweight="bold",
        zorder=4,
    )


def add_arrow(ax, start, end, color="#334155", rad=0.0):
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="Simple,tail_width=0.7,head_width=8,head_length=10",
        linewidth=1.6,
        color=color,
        connectionstyle=f"arc3,rad={rad}",
        zorder=5,
    )
    ax.add_patch(arrow)


def add_label(ax, x, y, text, color):
    ax.text(
        x,
        y,
        text,
        fontsize=9.6,
        color=color,
        fontweight="bold",
        ha="center",
        va="center",
        zorder=6,
    )


def main():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update(
        {
            "font.size": 11,
            "figure.facecolor": "#f8fafc",
            "axes.facecolor": "#f8fafc",
            "font.family": "DejaVu Sans",
        }
    )

    fig, ax = plt.subplots(figsize=(16, 9.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    fig.text(
        0.5,
        0.965,
        "How HeartBench Works",
        ha="center",
        va="top",
        fontsize=24,
        fontweight="bold",
        color="#0f172a",
    )
    fig.text(
        0.5,
        0.928,
        "A staged workflow for separating first-pass judgment from explanation-layer change",
        ha="center",
        va="top",
        fontsize=12.5,
        color="#475569",
    )

    add_section_panel(ax, 0.04, 0.17, 0.24, 0.68, "Inputs", "#e0f2fe", "#0369a1")
    add_section_panel(ax, 0.31, 0.17, 0.34, 0.68, "Staged Evaluation", "#ede9fe", "#6d28d9")
    add_section_panel(ax, 0.68, 0.17, 0.28, 0.68, "Analysis And Takeaway", "#ecfccb", "#4d7c0f")

    add_shadow_card(
        ax,
        0.065,
        0.56,
        0.19,
        0.22,
        "Benchmark",
        [
            "HeartBench-v2 paired cases",
            "Motive-sensitive item families",
            "Heart labels and act labels",
        ],
        facecolor="#ffffff",
        edgecolor="#38bdf8",
        title_color="#075985",
        accent="#7dd3fc",
    )
    add_shadow_card(
        ax,
        0.065,
        0.31,
        0.19,
        0.18,
        "Models",
        [
            "Qwen2.5 7B Instruct",
            "Qwen2.5 0.5B Instruct",
            "Same-family scale check",
        ],
        facecolor="#ffffff",
        edgecolor="#38bdf8",
        title_color="#075985",
        accent="#bae6fd",
    )
    add_shadow_card(
        ax,
        0.065,
        0.17,
        0.19,
        0.12,
        "Question",
        [
            "Does framing mainly move J1,",
            "or mainly E?",
        ],
        facecolor="#ffffff",
        edgecolor="#38bdf8",
        title_color="#075985",
        accent="#e0f2fe",
        body_fontsize=9.0,
        body_top_offset=0.08,
    )

    add_shadow_card(
        ax,
        0.35,
        0.56,
        0.25,
        0.16,
        "J1: First-Pass Judgment",
        [
            "Forced choice on which case has",
            "worse heart / worse act",
            "Measures immediate exposed choice",
        ],
        facecolor="#ffffff",
        edgecolor="#8b5cf6",
        title_color="#5b21b6",
        accent="#c4b5fd",
    )
    add_shadow_card(
        ax,
        0.35,
        0.35,
        0.25,
        0.16,
        "E: Explanation",
        [
            "Model explains the J1 choice",
            "Track lexical echo, heart-focus,",
            "and explanation restructuring",
        ],
        facecolor="#ffffff",
        edgecolor="#d946ef",
        title_color="#86198f",
        accent="#f0abfc",
    )
    add_shadow_card(
        ax,
        0.35,
        0.14,
        0.25,
        0.16,
        "J2: Re-Judgment",
        [
            "Model judges again after E",
            "Measures revision pressure",
            "and revision direction",
        ],
        facecolor="#ffffff",
        edgecolor="#fb7185",
        title_color="#9f1239",
        accent="#fda4af",
    )

    add_shadow_card(
        ax,
        0.715,
        0.56,
        0.22,
        0.22,
        "Direct Contrasts",
        [
            "christian_pre vs secular_pre",
            "christian_post vs secular_post",
            "Bootstrap CIs and paired tests",
        ],
        facecolor="#ffffff",
        edgecolor="#84cc16",
        title_color="#3f6212",
        accent="#bef264",
    )
    add_shadow_card(
        ax,
        0.715,
        0.31,
        0.22,
        0.18,
        "Controlled Explanation Metrics",
        [
            "Exact frame-word echo",
            "Lexical-controlled heart shift",
            "Structure change beyond wording",
        ],
        facecolor="#ffffff",
        edgecolor="#84cc16",
        title_color="#3f6212",
        accent="#d9f99d",
    )
    add_shadow_card(
        ax,
        0.715,
        0.12,
        0.22,
        0.15,
        "Mechanism Claim",
        [
            "Explanation moves more",
            "than first-pass judgment",
        ],
        facecolor="#ffffff",
        edgecolor="#16a34a",
        title_color="#166534",
        accent="#86efac",
        body_fontsize=9.8,
        body_top_offset=0.082,
    )

    pill_y = 0.83
    pill_w = 0.1
    pill_h = 0.045
    pill_xs = [0.325, 0.435, 0.545, 0.655, 0.765, 0.875]
    pill_specs = [
        ("baseline", "#e2e8f0", "#94a3b8", "#334155"),
        ("secular_pre", "#dbeafe", "#60a5fa", "#1d4ed8"),
        ("christian_pre", "#fee2e2", "#f87171", "#b91c1c"),
        ("secular_post", "#dbeafe", "#60a5fa", "#1d4ed8"),
        ("christian_post", "#fee2e2", "#f87171", "#b91c1c"),
        ("judgment_only", "#ede9fe", "#a78bfa", "#6d28d9"),
    ]
    for x, (label, facecolor, edgecolor, textcolor) in zip(pill_xs, pill_specs):
        add_pill(ax, x, pill_y, pill_w, pill_h, label, facecolor, edgecolor, textcolor)
    ax.text(
        0.32,
        0.885,
        "Condition families:",
        fontsize=10.2,
        fontweight="bold",
        color="#475569",
        ha="left",
        va="center",
    )

    add_arrow(ax, (0.255, 0.66), (0.35, 0.64), color="#0284c7")
    add_arrow(ax, (0.255, 0.40), (0.35, 0.43), color="#0284c7")
    add_arrow(ax, (0.255, 0.24), (0.35, 0.23), color="#0284c7")
    add_arrow(ax, (0.475, 0.56), (0.475, 0.51), color="#8b5cf6")
    add_arrow(ax, (0.475, 0.35), (0.475, 0.30), color="#d946ef")
    add_arrow(ax, (0.60, 0.64), (0.715, 0.67), color="#65a30d")
    add_arrow(ax, (0.60, 0.43), (0.715, 0.40), color="#65a30d")
    add_arrow(ax, (0.60, 0.22), (0.715, 0.20), color="#16a34a")
    add_arrow(ax, (0.55, 0.81), (0.47, 0.72), color="#6366f1", rad=0.1)
    add_arrow(ax, (0.76, 0.81), (0.47, 0.51), color="#dc2626", rad=-0.08)

    add_label(ax, 0.53, 0.775, "pre-frame reaches J1", "#4f46e5")
    add_label(ax, 0.72, 0.785, "post-frame reaches E and J2", "#b91c1c")

    takeaway = FancyBboxPatch(
        (0.07, 0.03),
        0.86,
        0.08,
        boxstyle="round,pad=0.02,rounding_size=0.035",
        linewidth=0,
        facecolor="#0f172a",
        zorder=2,
    )
    ax.add_patch(takeaway)
    ax.text(
        0.5,
        0.072,
        "Main empirical takeaway: explanation language moves more than first-pass exposed judgment",
        ha="center",
        va="center",
        fontsize=12.2,
        fontweight="bold",
        color="white",
        zorder=3,
    )

    fig.savefig(PNG_OUT, dpi=260, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(SVG_OUT, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Saved {PNG_OUT}")
    print(f"Saved {SVG_OUT}")


if __name__ == "__main__":
    main()
