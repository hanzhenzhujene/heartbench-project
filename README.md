# HeartBench

[![Paper Summary PDF](https://img.shields.io/badge/PDF-paper--style%20summary-B91C1C)](paper/heartbench_project_summary.pdf)
[![Main Results](https://img.shields.io/badge/results-staged%20main-166534)](results/staged_paper/heartbench_v2/main/direct_comparison_summary.csv)
![Models](https://img.shields.io/badge/models-Qwen2.5%207B%20%7C%200.5B-1d4ed8)
![Design](https://img.shields.io/badge/design-J1%20%E2%86%92%20E%20%E2%86%92%20J2-7c3aed)
![License](https://img.shields.io/github/license/hanzhenzhujene/heartbench-project)

**HeartBench** is a research repository about a narrow empirical question in moral prompting:

> When models see a **religiously marked frame** and a **matched secular motive-focused frame**, does the framing change the model's **first-pass exposed judgment**, or mainly the **explanation** it gives around that judgment?

The strongest current answer is:

- **First-pass Christian-versus-secular judgment differences are small or null.**
- **Explanation-layer differences are larger and more reliable.**
- **Those explanation differences survive lexical-echo control.**

This is a **neutral empirical benchmark and analysis repo**, not a theological argument. The Christian condition matters here as a controlled test case within a matched framing comparison.

> Quick links: [paper PDF](paper/heartbench_project_summary.pdf) | [workflow figure](assets/readme_methodology_workflow.png) | [main staged results](results/staged_paper/heartbench_v2/main/direct_comparison_summary.csv)

## Start Here

If you are new to the repository, use this order:

1. Read the [paper-style summary PDF](paper/heartbench_project_summary.pdf).
2. Skim the [workflow figure](assets/readme_methodology_workflow.png).
3. Skim the [result overview figure](assets/readme_result_overview.png).
4. Open the [main staged comparison table](results/staged_paper/heartbench_v2/main/direct_comparison_summary.csv).

## Workflow

![HeartBench methodology workflow](assets/readme_methodology_workflow.png)

The logic is simple:

- build paired cases where inward motive and outward act can come apart
- compare a religiously marked frame to a matched secular motive-focused control
- separate `J1` first-pass judgment, `E` explanation, and `J2` re-judgment
- test whether movement appears at the decision layer or mainly at the explanation layer

## Main Finding

![HeartBench staged result overview](assets/readme_result_overview.png)

**Religiously marked framing changes how models explain a judgment more strongly than it changes the model's first-pass exposed choice.**

Why this is the key result:

- the **pre-frame** contrast targets first-pass exposed judgment
- the **post-frame** contrast targets explanation and re-judgment behavior
- the clearest movement appears in **explanation metrics**, not in `J1`
- in the matched post comparison, both models have `same_j1_rate = 1.0`, so explanation differences remain even when first-pass `J1` is unchanged itemwise

Direct Christian-vs-secular contrasts on `HeartBench-v2` main:

| Model | `christian_pre - secular_pre` on `J1` heart | `christian_pre - secular_pre` on `J1` act | `christian_post - secular_post` on explanation Christianization | `christian_post - secular_post` on controlled heart-focus | `christian_post - secular_post` on restructuring |
|---|---:|---:|---:|---:|---:|
| `qwen2.5:7b-instruct` | `+0.017` (`p=0.7286`) | `-0.008` (`p=1.0`) | `+0.049` (`p<0.001`) | `+0.015` (`p<0.001`) | `+0.196` (`p<0.001`) |
| `qwen2.5:0.5b-instruct` | `+0.033` (`p=0.2095`) | `+0.008` (`p=1.0`) | `+0.013` (`p<0.001`) | `+0.015` (`p<0.001`) | `+0.069` (`p=0.0366`) |

## Repository Layout

The root is intentionally kept small:

```text
heartbench_project/
├── paper/        paper-style summary PDF and paper-facing materials
├── assets/       README figures and visual assets
├── benchmark/    benchmark releases and relabel templates
├── research/     configs, prompt sets, and internal reports
├── results/      main experiment outputs and figures
├── src/          experiment runners, scorers, analyzers, builders
└── archive/      legacy pipelines, notes, and exploratory material
```

Most readers only need:

- [paper/heartbench_project_summary.pdf](paper/heartbench_project_summary.pdf)
- [results/staged_paper/heartbench_v2/main/](results/staged_paper/heartbench_v2/main/)

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

See [results/staged_paper/heartbench_v2/main/run_manifest.json](results/staged_paper/heartbench_v2/main/run_manifest.json).

## Quick Start

```bash
pip3 install -r requirements.txt
python3 src/validate_benchmark.py --benchmark benchmark/heartbench_v2_120.jsonl
python3 src/run_staged_paper_inference.py \
  --benchmark heartbench_v2 \
  --models qwen2.5:7b-instruct qwen2.5:0.5b-instruct \
  --conditions baseline secular_pre christian_pre secular_post christian_post judgment_only \
  --variant-limit-per-family 1
python3 src/analyze_staged_paper_results.py --benchmark heartbench_v2 --results-root results/staged_paper
python3 src/plot_staged_paper_figures.py --benchmark heartbench_v2 --results-root results/staged_paper
```

## Caveat

`HeartBench-v2` is currently the most informative benchmark in the repository, but its case-level `1-5` labels are still partly template-assigned. The blind relabel package is included so the benchmark can be upgraded to a more publication-grade human annotation layer.

- [benchmark/heartbench_v2_relabel_blind_template.csv](benchmark/heartbench_v2_relabel_blind_template.csv)
- [research/reports/heartbench_v2_relabel_protocol.md](research/reports/heartbench_v2_relabel_protocol.md)

## Archive

- [archive/pairwise_ab_pipelines/README.md](archive/pairwise_ab_pipelines/README.md)
- [archive/legacy_notes/](archive/legacy_notes)

## License

This project is released under the [Apache 2.0 License](LICENSE).
