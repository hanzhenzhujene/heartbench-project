# Bias-Resistant Rerun Report

## Why the rerun was necessary

The original project headline, "Christian framing hurts heart attribution," was not trustworthy as stated.

The main problems were:

1. **Raw A/B answer-channel bias**: several prompt conditions induced strong letter preferences that were being scored as if they reflected substantive moral reasoning.
2. **Weak secondary benchmark construction**: the shipped Moral Stories subset often omitted explicit intention evidence and remained poorly separable under a cleaner evaluation.
3. **Unhelpful dual-label task design**: the pairwise prompts asked for both `heart_worse` and `morally_worse`, but the shipped benchmarks did not actually separate those gold labels.

The benchmark audit is in [benchmark_confound_audit.md](benchmark_confound_audit.md).

## Corrected experimental setup

The corrected setup removes the main A/B failure mode instead of trying to adjust for it afterward.

### Design changes

1. No `A/B` answer choices in the prompt.
2. Each case is scored independently on a single `1-5` heart scale.
3. Scoring reads the model's next-token preference over those digits.
4. The pairwise winner is computed offline from the two case scores.
5. The task is heart-only; there is no separate `morally_worse` output field.

### Canonical files

- `src/run_casewise_logit_inference.py`
- `src/score_casewise_results.py`
- `src/analyze_casewise_results.py`
- `materials/research/configs/experiment_casewise_logit.yaml`
- `materials/research/configs/prompts_casewise_logit.yaml`

Historical pairwise materials now live in [../archive/pairwise_ab_pipelines/README.md](../archive/pairwise_ab_pipelines/README.md).

## Primary benchmark: HeartBench-240

### Qwen2.5-1.5B-Instruct

#### Expected-score summary

| Condition | Expected Acc | Confident Acc | Confident Coverage | Expected Mean Margin |
|-----------|--------------|---------------|--------------------|----------------------|
| C0 | 0.933 | 0.981 | 0.867 | 0.535 |
| C1 | 0.942 | 0.969 | 0.929 | 0.779 |
| C2 | 0.938 | 0.972 | 0.904 | 0.547 |
| C3 | 0.938 | 0.959 | 0.904 | 0.674 |
| C4 | 0.942 | 0.982 | 0.913 | 0.746 |

Paired expected-score comparisons are effectively null:

- `C0` vs `C2`: gain `+0.004`, 95% CI `[-0.021, +0.029]`, McNemar `p=1.0`
- `C2` vs `C4`: gain `+0.004`, 95% CI `[-0.013, +0.025]`, `p=1.0`
- `C2` vs `C3`: gain `0.000`, 95% CI `[-0.021, +0.021]`, `p=0.683`

Interpretation:

- The old strong `C2` penalty disappears once raw answer-channel bias is removed.
- `C1` and `C4` are slightly more separating than `C2`, but not by a statistically convincing amount.
- The clean conclusion is **no robust framing advantage and no robust Christian-framing penalty** on the corrected primary benchmark.

### Qwen2.5-0.5B-Instruct

#### Expected-score summary

| Condition | Expected Acc | Confident Acc | Confident Coverage | Expected Mean Margin |
|-----------|--------------|---------------|--------------------|----------------------|
| C0 | 0.388 | 0.368 | 0.758 | 0.261 |
| C1 | 0.429 | 0.412 | 0.738 | 0.248 |
| C2 | 0.362 | 0.344 | 0.762 | 0.260 |
| C3 | 0.408 | 0.371 | 0.775 | 0.290 |
| C4 | 0.413 | 0.418 | 0.758 | 0.263 |

Notable paired expected-score comparisons:

- `C0` vs `C1`: gain `+0.042`, 95% CI `[+0.008, +0.079]`, McNemar `p=0.0339`
- `C0` vs `C2`: gain `-0.025`, 95% CI `[-0.067, +0.017]`, `p=0.307`
- `C2` vs `C4`: gain `+0.050`, 95% CI `[+0.017, +0.083]`, `p=0.0095`

Interpretation:

- The smaller model remains weak on the corrected primary benchmark.
- `C2` is not rescuing performance; if anything, it is slightly worse than the neutral and secular alternatives.
- Unlike `1.5B`, the issue here is not just separability. The overall model is simply not reliably solving the task.

## Secondary benchmark: Moral Stories supported

This benchmark remains exploratory and should not drive the project-level conclusion.

### Qwen2.5-1.5B-Instruct

| Condition | Expected Acc | Resolved Acc | Coverage | Tie Rate |
|-----------|--------------|--------------|----------|----------|
| C0 | 0.808 | 1.000 | 0.019 | 0.981 |
| C1 | 0.808 | 0.833 | 0.115 | 0.885 |
| C2 | 0.788 | 0.500 | 0.038 | 0.962 |
| C3 | 0.808 | 0.667 | 0.058 | 0.942 |
| C4 | 0.750 | 0.750 | 0.077 | 0.923 |

Interpretation:

- The expected-score view is usable, but the discrete task is still almost all ties.
- The benchmark is too weakly separable to support a serious framing comparison on its own.

### Qwen2.5-0.5B-Instruct

| Condition | Expected Acc | Resolved Acc | Coverage | Tie Rate |
|-----------|--------------|--------------|----------|----------|
| C0 | 0.327 | 0.333 | 0.346 | 0.654 |
| C1 | 0.327 | 0.500 | 0.346 | 0.654 |
| C2 | 0.288 | 0.200 | 0.192 | 0.808 |
| C3 | 0.269 | 0.250 | 0.385 | 0.615 |
| C4 | 0.250 | 0.385 | 0.250 | 0.750 |

Interpretation:

- The smaller model is poor across all conditions on this benchmark.
- `C2` again does not help.
- Because the benchmark itself is still weak, these numbers are best read as secondary diagnostics rather than core evidence.

## Project-level conclusion after the corrected reruns

The corrected reruns replace the earlier story with a more careful one:

1. The old claim that Christian heart-focused framing **hurts** heart attribution is **not supported** on the benchmark we currently trust most.
2. The original positive hypothesis that Christian framing **improves** heart attribution is also **not supported** by a robust gain.
3. On HeartBench-240, `Qwen2.5-1.5B-Instruct` is strong and largely insensitive to framing once the A/B artifact is removed.
4. `Qwen2.5-0.5B-Instruct` remains weak overall; Christian framing does not rescue it.
5. Moral Stories supported remains exploratory and should not be used as the main benchmark for the project's headline claim.

## Recommended canonical setup

If this project continues, the safest default is:

1. Use the **casewise-logit** pipeline as the primary evaluation.
2. Treat **HeartBench-240** as the primary benchmark.
3. Report expected accuracy together with coverage, tie rate, and margin.
4. Treat Moral Stories supported as exploratory only unless it is rebuilt into a more genuinely separable motive benchmark.
5. Keep the archived pairwise A/B materials as historical reference, not active evidence.
