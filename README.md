# HeartBench

![Finding](https://img.shields.io/badge/finding-explanations%20move%20more%20than%20first--pass%20judgment-166534)
![Models](https://img.shields.io/badge/models-Qwen2.5%207B%20%7C%200.5B-1d4ed8)
![Design](https://img.shields.io/badge/design-J1%20%E2%86%92%20E%20%E2%86%92%20J2-7c3aed)
![Benchmark](https://img.shields.io/badge/benchmark-HeartBench--v2-0f766e)
![GitHub License](https://img.shields.io/github/license/hanzhenzhujene/heartbench-project)
![GitHub last commit](https://img.shields.io/github/last-commit/hanzhenzhujene/heartbench-project)
![GitHub Repo stars](https://img.shields.io/github/stars/hanzhenzhujene/heartbench-project?style=social)

**HeartBench** is a research repo for testing a very specific question:

> Does Christian heart-focused framing actually change a model's **first-pass exposed moral judgment**, or does it mainly change the **way the model explains itself** after the judgment is already made?

The short answer from the current staged experiments is:

- **First-pass Christian-over-secular judgment movement is modest or null.**
- **Explanation-layer movement is much larger and more reliable.**
- **That explanation effect survives lexical-echo control**, so it is not just the model parroting frame words.

![HeartBench staged result overview](assets/readme_result_overview.png)

## Deep Takeaway

If you are trying to steer model **decisions**, Christian framing does not currently look like a strong first-pass override.

If you are trying to steer model **rationales, narrative framing, and motive-sensitive explanation language**, Christian framing is much more potent.

That makes the project useful well beyond this specific paper question. It suggests that prompt framing can change the **justification layer** more strongly than the **exposed choice layer**. For evaluation, safety, and interpretability work, this means we should not treat a changed explanation as evidence that the underlying first-pass decision moved by the same amount.

## What This Repo Shows

### Main empirical claim

Across a staged `J1 -> E -> J2` design, Christian framing appears to affect **explanation language** more strongly than **first-pass exposed judgment**.

### Why that matters

- If you audit moral or safety prompting, you should measure **decision shifts** and **rationale shifts** separately.
- If you compare religious framing to a matched secular control, you can separate **generic motive salience** from **specifically Christian rhetorical uptake**.
- If you want a reviewer-resistant mechanism claim, the strongest honest claim is at the **explanation layer**, not broad moral override.

### Current best-supported takeaway

The completed full main staged runs on `HeartBench-v2` support this pattern on both:

- `qwen2.5:7b-instruct`
- `qwen2.5:0.5b-instruct`

## Main Result

### Direct Christian-vs-secular contrasts on HeartBench-v2 main

These are the headline paired comparisons from the completed staged main runs.

| Model | `christian_pre - secular_pre` on `J1` heart | `christian_pre - secular_pre` on `J1` act | `christian_post - secular_post` on explanation Christianization | `christian_post - secular_post` on controlled heart-focus | `christian_post - secular_post` on restructuring |
|---|---:|---:|---:|---:|---:|
| `qwen2.5:7b-instruct` | `+0.017` (`p=0.7286`) | `-0.008` (`p=1.0`) | `+0.049` (`p<0.001`) | `+0.015` (`p<0.001`) | `+0.196` (`p<0.001`) |
| `qwen2.5:0.5b-instruct` | `+0.033` (`p=0.2095`) | `+0.008` (`p=1.0`) | `+0.013` (`p<0.001`) | `+0.015` (`p<0.001`) | `+0.069` (`p=0.0366`) |

### Mechanism evidence

The most diagnostic result is that explanation movement remains even when `J1` is unchanged itemwise:

- `same_j1_rate = 1.0` for both models in the matched post comparison
- `qwen2.5:7b-instruct`: controlled explanation heart-focus still rises by `+0.015` with `p<0.001`
- `qwen2.5:0.5b-instruct`: controlled explanation heart-focus still rises by `+0.015` with `p<0.001`

That is the cleanest evidence in the repo for **stage dissociation**.

## How To Read The Findings

### Strong claims the repo supports

- Christian framing changes explanation language more than first-pass exposed judgment.
- Matched secular motive-focused prompts already account for part of the effect.
- The residual Christian-over-secular difference is concentrated in the explanation layer.

### Claims the repo does not support

- A broad claim that Christian framing strongly changes first-pass moral choice.
- A broad claim that Christian framing uniquely improves model moral judgment.
- A strong claim that explanation shifts are only lexical echo.

### Current caveat

`HeartBench-v2` is the most informative benchmark in the repo, but its case-level `1-5` labels are still partly template-assigned. The blind relabel package is included in this repository so the benchmark can be upgraded to publication-grade human labels.

## Project Tracks

| Track | Purpose | Status |
|---|---|---|
| **Staged paper track** | Main paper-facing result: separate `J1`, `E`, and `J2` | Active, completed full main runs for both Qwen models |
| **Bias-resistant casewise-logit track** | Correct the old A/B artifact and recover a clean benchmark result | Active, stable |
| **HeartBench-v2 rebuild track** | Rebuild the benchmark to separate `heart` vs `act` more explicitly | Active, relabeling still pending |
| **Old pairwise A/B track** | Historical reference only | Archived |

## Repository Map

```text
heartbench_project/
  benchmark/                    # HeartBench, HeartBench-v2, relabel templates
  configs/                      # Experiment configs and prompt families
  prompts/                      # Pre/post frame prompts and staged prompts
  reports/                      # Result writeups, audits, revision packet
  results_casewise_logit/       # Corrected benchmark results
  results_dual_logit_v2/        # HeartBench-v2 dual-logit results
  results_staged_paper/         # Staged J1/E/J2 paper results and figures
  src/                          # Builders, runners, scorers, analyzers, plotters
```

## Quick Start

### 1. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Validate the core benchmarks

```bash
python3 src/validate_benchmark.py --benchmark benchmark/heartbench_240.jsonl
python3 src/validate_benchmark.py --benchmark benchmark/moral_stories_supported.jsonl
python3 src/validate_benchmark.py --benchmark benchmark/heartbench_v2_120.jsonl
```

### 3. Run the staged paper pipeline

```bash
python3 src/run_staged_paper_inference.py \
  --benchmark heartbench_v2 \
  --models qwen2.5:7b-instruct qwen2.5:0.5b-instruct \
  --conditions baseline secular_pre christian_pre secular_post christian_post judgment_only \
  --variant-limit-per-family 1

python3 src/analyze_staged_paper_results.py --benchmark heartbench_v2 --results-root results_staged_paper
python3 src/plot_staged_paper_figures.py --benchmark heartbench_v2 --results-root results_staged_paper
```

### 4. Run the artifact-corrected legacy benchmark

```bash
python3 src/run_casewise_logit_inference.py --benchmark heartbench --models Qwen/Qwen2.5-1.5B-Instruct
python3 src/run_casewise_logit_inference.py --benchmark heartbench --models Qwen/Qwen2.5-0.5B-Instruct
python3 src/score_casewise_results.py --benchmark heartbench
python3 src/analyze_casewise_results.py --benchmark heartbench
```

## Most Useful Files

### Start here

- [reports/staged_paper_revision_packet.md](reports/staged_paper_revision_packet.md)
- [reports/staged_paper_status_2026-04-08.md](reports/staged_paper_status_2026-04-08.md)
- [reports/final_status.md](reports/final_status.md)

### Main staged outputs

- [results_staged_paper/heartbench_v2/main/direct_comparison_summary.csv](results_staged_paper/heartbench_v2/main/direct_comparison_summary.csv)
- [results_staged_paper/heartbench_v2/main/same_j1_explanation_shift.csv](results_staged_paper/heartbench_v2/main/same_j1_explanation_shift.csv)
- [results_staged_paper/heartbench_v2/main/heterogeneity_summary.csv](results_staged_paper/heartbench_v2/main/heterogeneity_summary.csv)
- [results_staged_paper/heartbench_v2/main/figures](results_staged_paper/heartbench_v2/main/figures)

### Benchmark and relabel materials

- [benchmark/heartbench_v2_120.jsonl](benchmark/heartbench_v2_120.jsonl)
- [benchmark/heartbench_v2_relabel_blind_template.csv](benchmark/heartbench_v2_relabel_blind_template.csv)
- [reports/heartbench_v2_relabel_protocol.md](reports/heartbench_v2_relabel_protocol.md)

## Reproducibility Notes

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

## Legacy and Historical Material

The old pairwise A/B pipeline is archived under:

- [archive/pairwise_ab_pipelines/README.md](archive/pairwise_ab_pipelines/README.md)

It is preserved for historical reference only. The old A/B headline should not be treated as the main result path.

## License

This project is released under the [Apache 2.0 License](LICENSE).
