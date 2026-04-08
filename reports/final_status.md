# Final Status Report

## Date

2026-04-07

## Canonical Evaluation

The canonical evaluation is now the **bias-resistant casewise-logit pipeline**:

- `src/run_casewise_logit_inference.py`
- `src/score_casewise_results.py`
- `src/analyze_casewise_results.py`

The old pairwise A/B pipelines have been archived under [../archive/pairwise_ab_pipelines/README.md](../archive/pairwise_ab_pipelines/README.md).

## Primary Result: HeartBench-240

Expected heart accuracy on the corrected full primary benchmark:

| Model | C0 | C1 | C2 | C3 | C4 |
|-------|----|----|----|----|----|
| Qwen2.5-1.5B-Instruct | 0.933 | 0.942 | 0.938 | 0.938 | 0.942 |
| Qwen2.5-0.5B-Instruct | 0.388 | 0.429 | 0.362 | 0.408 | 0.413 |

Key paired comparisons:

- `1.5B`: all planned expected-score comparisons are effectively null. The old strong `C2` penalty is not supported once the A/B artifact is removed.
- `0.5B`: `C1` is modestly above `C0` (`+0.042`, 95% CI `[+0.008, +0.079]`, McNemar `p=0.0339`), and `C4` is above `C2` (`+0.050`, 95% CI `[+0.017, +0.083]`, `p=0.0095`), but the model remains weak overall.

Interpretation:

1. `Qwen2.5-1.5B-Instruct` is strong on the corrected primary benchmark and shows no robust framing advantage or penalty.
2. `Qwen2.5-0.5B-Instruct` remains unreliable on the corrected primary benchmark, with expected accuracy below `0.5` in every condition.
3. `C2` does not produce a robust benefit on either model.

## Secondary Result: Moral Stories Supported

Expected heart accuracy on the exploratory secondary benchmark:

| Model | C0 | C1 | C2 | C3 | C4 |
|-------|----|----|----|----|----|
| Qwen2.5-1.5B-Instruct | 0.808 | 0.808 | 0.788 | 0.808 | 0.750 |
| Qwen2.5-0.5B-Instruct | 0.327 | 0.327 | 0.288 | 0.269 | 0.250 |

Interpretation:

- `1.5B` is directionally decent on this benchmark, but the benchmark remains too tie-heavy and weakly separable to carry the main claim.
- `0.5B` is poor across all conditions.
- This benchmark should remain exploratory only.

## What Changed

The original headline result was confounded by raw `A/B` answer-channel bias. The corrected setup fixes that by:

1. removing `A/B` answer choices from the prompt,
2. scoring each case independently on a `1-5` heart scale,
3. deriving the pairwise winner offline from the score distributions.

That change removes the main artifact behind the earlier apparent `C2` penalty.

## Repository State

Active, supported path:

- `src/run_casewise_logit_inference.py`
- `src/score_casewise_results.py`
- `src/analyze_casewise_results.py`
- `results_casewise_logit/`

Historical material:

- Pairwise A/B pipelines: `archive/pairwise_ab_pipelines/`
- Detailed corrected rerun report: [bias_resistant_rerun_report.md](bias_resistant_rerun_report.md)
- Audit of the original confounds: [benchmark_confound_audit.md](benchmark_confound_audit.md)

## Bottom Line

The project no longer supports the old claim that Christian heart-focused framing hurts performance on the primary benchmark. The corrected result is narrower:

- `1.5B`: no robust framing advantage and no robust Christian-framing penalty.
- `0.5B`: weak overall, with no evidence that Christian framing helps.
- HeartBench-240 is the benchmark to trust most; Moral Stories supported remains exploratory.
