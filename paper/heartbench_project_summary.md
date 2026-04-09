---
title: "HeartBench"
subtitle: "Stage-Dissociated Moral Evaluation Under Religious and Secular Framing"
author: "Project Summary"
date: "2026-04-08"
geometry: margin=1in
fontsize: 11pt
colorlinks: true
---

# Overview

HeartBench studies a narrow but important empirical question:

**When language models are exposed to a religiously marked moral frame and a matched secular motive-focused frame, do they change their first-pass exposed judgment, or mainly the explanation they produce around that judgment?**

The current repository evidence supports a stage-dissociation interpretation:

- first-pass Christian-versus-secular judgment differences are small or null
- explanation-layer differences are larger and more reliable
- those explanation differences survive lexical-echo control

# Core Design

The main paper-facing experiment uses a staged design:

- `J1`: first-pass forced-choice judgment
- `E`: explanation tied to `J1`
- `J2`: re-judgment after explanation

This staged structure matters because it lets us separate:

1. **decision movement** at first exposure
2. **justification movement** after framing and explanation
3. **revision pressure** after explanation

The key comparison is not simply “Christian prompt versus baseline.” It is:

- **Christian framing versus a matched secular motive-focused control**

That makes the interpretation cleaner. It helps distinguish:

- generic motive salience
- specifically Christian rhetorical uptake

# Workflow At A Glance

![](../materials/assets/readme_methodology_workflow.png){ width=100% }

# Main Result

## Direct Christian-vs-secular contrasts on HeartBench-v2 main

| Model | `christian_pre - secular_pre` on `J1` heart | `christian_pre - secular_pre` on `J1` act | `christian_post - secular_post` on explanation Christianization | `christian_post - secular_post` on controlled heart-focus | `christian_post - secular_post` on restructuring |
|:--|--:|--:|--:|--:|--:|
| `qwen2.5:7b-instruct` | `+0.017` (`p=0.7286`) | `-0.008` (`p=1.0`) | `+0.049` (`p<0.001`) | `+0.015` (`p<0.001`) | `+0.196` (`p<0.001`) |
| `qwen2.5:0.5b-instruct` | `+0.033` (`p=0.2095`) | `+0.008` (`p=1.0`) | `+0.013` (`p<0.001`) | `+0.015` (`p<0.001`) | `+0.069` (`p=0.0366`) |

## Mechanism evidence

The strongest mechanism result is that the explanation shift remains when `J1` is unchanged itemwise:

- `same_j1_rate = 1.0` for both models in the matched post comparison
- explanation-layer Christian-over-secular movement therefore remains even without first-pass movement

This is the clearest evidence in the repository for **stage dissociation**.

# What The Results Support

## Strong claims

- Explanation-layer movement is more robust than first-pass judgment movement.
- Matched secular controls matter; part of the effect is generic motive salience.
- The residual Christian-over-secular difference is concentrated in explanation style and restructuring.

## Claims the repo does not support

- A strong claim that Christian framing broadly changes first-pass moral choice
- A strong claim that Christian framing uniquely improves moral judgment
- A strong claim that explanation effects are only lexical mimicry

# Visual Summary

![](../materials/assets/readme_result_overview.png){ width=100% }

\newpage

# Repository Pointers

If you want the shortest path through the repository, start with:

- `README.md`
- `materials/results/staged_paper/heartbench_v2/main/direct_comparison_summary.csv`
- `materials/results/staged_paper/heartbench_v2/main/same_j1_explanation_shift.csv`
- `materials/research/reports/staged_paper_revision_packet.md`

If you want the benchmark and labeling materials, use:

- `materials/benchmark/heartbench_v2_120.jsonl`
- `materials/benchmark/heartbench_v2_relabel_blind_template.csv`
- `materials/research/reports/heartbench_v2_relabel_protocol.md`

If you want the code path for the main staged paper result, use:

- `src/run_staged_paper_inference.py`
- `src/analyze_staged_paper_results.py`
- `src/plot_staged_paper_figures.py`

# Caveat

`HeartBench-v2` is currently the most informative benchmark in the repository, but its case-level `1-5` labels are still partly template-assigned. The repository already includes a blind relabel package so the benchmark can be upgraded to a stronger human-annotation footing.

# Bottom Line

The strongest honest conclusion is not that religious framing broadly rewires first-pass moral judgment.

The stronger conclusion is narrower and more useful:

**In this repository, religiously marked framing changes explanation language more strongly than first-pass exposed judgment.**
