# Christian Framing and Heart-Level Moral Attribution

This project tests whether Christian heart-focused framing changes what small language models treat as morally diagnostic: inward motive versus outward action.

## Canonical Status

The only supported evaluation path is the **bias-resistant casewise-logit pipeline**. It removes raw `A/B` answer-choice bias by scoring each case independently on a `1-5` heart scale and computing the pairwise decision offline.

The older pairwise A/B pipelines have been archived under [archive/pairwise_ab_pipelines](archive/pairwise_ab_pipelines/README.md). They are preserved for historical reference only and should not be treated as the main result path.

Current canonical references:

- [reports/bias_resistant_rerun_report.md](reports/bias_resistant_rerun_report.md)
- [reports/final_status.md](reports/final_status.md)
- [results_casewise_logit/heartbench/main/analysis.json](results_casewise_logit/heartbench/main/analysis.json)

## Current Result

### HeartBench-240 (primary benchmark)

Expected heart accuracy under the corrected casewise-logit setup:

| Model | C0 | C1 | C2 | C3 | C4 |
|-------|----|----|----|----|----|
| Qwen2.5-1.5B-Instruct | 0.933 | 0.942 | 0.938 | 0.938 | 0.942 |
| Qwen2.5-0.5B-Instruct | 0.388 | 0.429 | 0.362 | 0.408 | 0.413 |

Interpretation:

- `Qwen2.5-1.5B-Instruct` shows **no robust condition differences** on the corrected primary benchmark.
- `Qwen2.5-0.5B-Instruct` remains weak overall; `C2` is not beneficial and is slightly worse than `C1` and `C4`.
- The old strong claim that Christian framing hurts performance was an artifact of the original pairwise A/B setup, not a stable finding.

### Moral Stories supported (exploratory secondary benchmark)

This benchmark remains weaker and should be treated as exploratory:

| Model | C0 | C1 | C2 | C3 | C4 |
|-------|----|----|----|----|----|
| Qwen2.5-1.5B-Instruct | 0.808 | 0.808 | 0.788 | 0.808 | 0.750 |
| Qwen2.5-0.5B-Instruct | 0.327 | 0.327 | 0.288 | 0.269 | 0.250 |

## Benchmarks

| Benchmark | Role | Items | Status |
|-----------|------|-------|--------|
| HeartBench-240 | Primary | 240 | Canonical |
| Moral Stories supported | Exploratory secondary | 52 | Diagnostic only |

## Active Pipeline

Main scripts:

- `src/run_casewise_logit_inference.py`
- `src/score_casewise_results.py`
- `src/analyze_casewise_results.py`
- `configs/experiment_casewise_logit.yaml`
- `configs/prompts_casewise_logit.yaml`

Supporting build and validation scripts:

- `src/build_benchmark.py`
- `src/build_moral_stories_subset.py`
- `src/build_corrected_benchmarks.py`
- `src/validate_benchmark.py`

## Recommended Quick Start

```bash
pip3 install -r requirements.txt

# Build benchmarks
python3 src/build_benchmark.py
python3 src/build_moral_stories_subset.py
python3 src/build_corrected_benchmarks.py

# Validate the canonical benchmark files
python3 src/validate_benchmark.py --benchmark benchmark/heartbench_240.jsonl
python3 src/validate_benchmark.py --benchmark benchmark/moral_stories_supported.jsonl

# Run corrected HeartBench for both models
python3 src/run_casewise_logit_inference.py --benchmark heartbench --models Qwen/Qwen2.5-1.5B-Instruct
python3 src/run_casewise_logit_inference.py --benchmark heartbench --models Qwen/Qwen2.5-0.5B-Instruct

# Score and analyze corrected HeartBench results
python3 src/score_casewise_results.py --benchmark heartbench
python3 src/analyze_casewise_results.py --benchmark heartbench

# Optional exploratory secondary benchmark
python3 src/run_casewise_logit_inference.py --benchmark moral_stories_supported --models Qwen/Qwen2.5-1.5B-Instruct
python3 src/run_casewise_logit_inference.py --benchmark moral_stories_supported --models Qwen/Qwen2.5-0.5B-Instruct
python3 src/score_casewise_results.py --benchmark moral_stories_supported
python3 src/analyze_casewise_results.py --benchmark moral_stories_supported
```

## Project Layout

```text
heartbench_project/
  archive/
    pairwise_ab_pipelines/        # Historical pairwise A/B materials
  benchmark/
    heartbench_240.jsonl
    moral_stories_supported.jsonl
    ...
  configs/
    experiment_casewise.yaml
    experiment_casewise_logit.yaml
    models.yaml
    prompts_casewise.yaml
    prompts_casewise_logit.yaml
  prompts/
    casewise_*.txt
    casewise_logit_*.txt
  reports/
    bias_resistant_rerun_report.md
    final_status.md
    benchmark_confound_audit.md
    benchmark_summary.md
    moral_stories_benchmark_summary.md
  results_casewise_logit/
    heartbench/
    heartbench_dev/
    moral_stories_supported/
  src/
    run_casewise_logit_inference.py
    score_casewise_results.py
    analyze_casewise_results.py
    ...
```

## Bottom Line

The corrected evaluation does **not** show a robust improvement from Christian heart-focused framing, but it also does **not** support the earlier strong claim that Christian framing makes the model worse on the primary benchmark. On the benchmark we currently trust most, prompt-condition differences are small for `1.5B`, while `0.5B` remains weak regardless of framing.
