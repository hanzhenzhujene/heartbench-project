# HeartBench

[![Paper Summary PDF](https://img.shields.io/badge/PDF-paper--style%20summary-B91C1C)](paper/heartbench_project_summary.pdf)
[![Main Results](https://img.shields.io/badge/results-staged%20main-166534)](results_staged_paper/heartbench_v2/main/direct_comparison_summary.csv)
![Models](https://img.shields.io/badge/models-Qwen2.5%207B%20%7C%200.5B-1d4ed8)
![Design](https://img.shields.io/badge/design-J1%20%E2%86%92%20E%20%E2%86%92%20J2-7c3aed)
![License](https://img.shields.io/github/license/hanzhenzhujene/heartbench-project)

**HeartBench** is a research repository for studying **stage-dissociated moral evaluation** in language models.

The central question is deliberately narrow and empirical:

> When models are given a **religiously marked moral frame** and a **matched secular motive-focused frame**, do they actually change their **first-pass exposed judgment**, or do they mainly change their **explanations**?

The strongest current answer is:

- **First-pass Christian-versus-secular judgment differences are small or null.**
- **Explanation-layer differences are larger and much more reliable.**
- **Those explanation differences survive lexical-echo control**, so they are not just direct reuse of frame words.

This repository is intended as a **neutral empirical resource**, not as an argument for or against any religious viewpoint. The Christian condition matters here as a **test case** within a controlled framing comparison.

## Start Here

If you open the repository for the first time, the fastest path is:

1. Read the [paper-style summary PDF](paper/heartbench_project_summary.pdf).
2. Skim the [result overview figure](assets/readme_result_overview.png).
3. Open the [main staged comparison table](results_staged_paper/heartbench_v2/main/direct_comparison_summary.csv).

![HeartBench staged result overview](assets/readme_result_overview.png)

## Main Takeaway

The repository currently supports a **mechanism claim**, not a broad claim of moral override:

**Religiously marked framing changes how models explain a judgment more strongly than it changes the model's first-pass exposed choice.**

This distinction matters for:

- prompt evaluation
- safety benchmarking
- interpretability
- any paper that tries to infer “moral change” from explanation text alone

In other words, a changed rationale should not automatically be interpreted as a changed initial decision process.

## What The Study Is, And Is Not

### What it is

- A controlled comparison between **Christian framing** and a **matched secular motive-focused control**
- A staged design that separates:
  - `J1`: first-pass judgment
  - `E`: explanation
  - `J2`: re-judgment after explanation
- A benchmark-and-analysis repo designed to test whether effects concentrate at the **decision layer** or the **justification layer**

### What it is not

- Not a claim that Christian framing is broadly “better”
- Not a claim that explanation change implies deep moral change
- Not a theological argument
- Not a finalized human-annotated benchmark release yet

## Current Best-Supported Result

### Direct Christian-vs-secular contrasts on `HeartBench-v2` main

| Model | `christian_pre - secular_pre` on `J1` heart | `christian_pre - secular_pre` on `J1` act | `christian_post - secular_post` on explanation Christianization | `christian_post - secular_post` on controlled heart-focus | `christian_post - secular_post` on restructuring |
|---|---:|---:|---:|---:|---:|
| `qwen2.5:7b-instruct` | `+0.017` (`p=0.7286`) | `-0.008` (`p=1.0`) | `+0.049` (`p<0.001`) | `+0.015` (`p<0.001`) | `+0.196` (`p<0.001`) |
| `qwen2.5:0.5b-instruct` | `+0.033` (`p=0.2095`) | `+0.008` (`p=1.0`) | `+0.013` (`p<0.001`) | `+0.015` (`p<0.001`) | `+0.069` (`p=0.0366`) |

### Why this is the key result

- The **pre-frame** comparison targets first-pass exposed judgment.
- The **post-frame** comparison targets explanation and re-judgment behavior.
- The clearest movement appears in **explanation metrics**, not in `J1`.

### Strongest mechanism evidence

In the matched post comparison, both models have:

- `same_j1_rate = 1.0`

That means explanation differences remain even when first-pass `J1` is unchanged itemwise. This is the clearest evidence for **stage dissociation** in the repository.

## Balanced Interpretation

### Claims the results support

- Explanation-layer movement is more robust than first-pass judgment movement.
- Matched secular controls matter: part of the effect is generic motive salience rather than uniquely religious language.
- The residual Christian-over-secular difference is most visible in explanation style and structure.

### Claims the results do not support

- A strong claim that Christian framing broadly changes first-pass moral choice
- A strong claim that Christian framing uniquely improves moral judgment
- A strong claim that explanation effects are only lexical mimicry

## Repository Guide

The root is intentionally organized around just a few places most readers need:

| Path | What it is for |
|---|---|
| [paper/](paper) | Paper-facing summary materials, including the PDF |
| [assets/](assets) | Homepage figures and visual assets |
| [benchmark/](benchmark) | Benchmark files and relabel templates |
| [src/](src) | Experiment runners, scorers, analyzers, and builders |
| [results_staged_paper/](results_staged_paper) | Main staged paper results |
| [results_dual_logit_v2/](results_dual_logit_v2) | Dual-logit benchmark follow-on results |
| [reports/](reports) | Audits, summaries, and research notes |
| [archive/](archive) | Historical pipelines and legacy planning material |

If you only want the main paper-facing result, you can ignore most of the repository and focus on:

- [paper/heartbench_project_summary.pdf](paper/heartbench_project_summary.pdf)
- [results_staged_paper/heartbench_v2/main/](results_staged_paper/heartbench_v2/main/)

## Reproducibility

The staged pipeline records:

- model name
- backend
- split
- item count
- seed
- decoding settings
- condition
- frame family
- frame variant
- output file path

See:

- [results_staged_paper/heartbench_v2/main/run_manifest.json](results_staged_paper/heartbench_v2/main/run_manifest.json)

## Quick Start

### Install

```bash
pip3 install -r requirements.txt
```

### Validate the main benchmark

```bash
python3 src/validate_benchmark.py --benchmark benchmark/heartbench_v2_120.jsonl
```

### Run the staged main experiment

```bash
python3 src/run_staged_paper_inference.py \
  --benchmark heartbench_v2 \
  --models qwen2.5:7b-instruct qwen2.5:0.5b-instruct \
  --conditions baseline secular_pre christian_pre secular_post christian_post judgment_only \
  --variant-limit-per-family 1

python3 src/analyze_staged_paper_results.py --benchmark heartbench_v2 --results-root results_staged_paper
python3 src/plot_staged_paper_figures.py --benchmark heartbench_v2 --results-root results_staged_paper
```

## Important Caveat

`HeartBench-v2` is currently the most informative benchmark in the repository, but its case-level `1-5` labels are still partly template-assigned. The blind relabel package is included so the benchmark can be upgraded to a more publication-grade human annotation layer.

Useful links:

- [benchmark/heartbench_v2_relabel_blind_template.csv](benchmark/heartbench_v2_relabel_blind_template.csv)
- [reports/heartbench_v2_relabel_protocol.md](reports/heartbench_v2_relabel_protocol.md)

## Legacy Material

The old pairwise A/B pipeline is archived under:

- [archive/pairwise_ab_pipelines/README.md](archive/pairwise_ab_pipelines/README.md)

Older planning and construction notes now live under:

- [archive/legacy_notes/](archive/legacy_notes)

## License

This project is released under the [Apache 2.0 License](LICENSE).
