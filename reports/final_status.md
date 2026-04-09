# Final Status Report

## Date

2026-04-08

## Staged Paper Track

A separate paper-facing staged pipeline is now active under:

- `src/run_staged_paper_inference.py`
- `src/analyze_staged_paper_results.py`
- `src/plot_staged_paper_figures.py`
- `results_staged_paper/`

It is designed around:

- `J1`: first-pass forced-choice judgment
- `E`: explanation tied to `J1`
- `J2`: re-judgment after explanation

The intended paper models are:

- main model: `qwen2.5:7b-instruct`
- smaller within-family robustness model: `qwen2.5:0.5b-instruct`

Current staged status:

- completed 30-item dev rerun for both models at `results_staged_paper/heartbench_v2_dev/dev`
- completed 120-item full main rerun for `qwen2.5:0.5b-instruct` at `results_staged_paper/heartbench_v2/main`
- completed 120-item full main rerun for `qwen2.5:7b-instruct` at `results_staged_paper/heartbench_v2/main`

Completed staged results already support the cleaner mechanism claim:

1. direct `christian_pre` versus `secular_pre` effects on `J1` are weak or null
2. direct `christian_post` versus `secular_post` effects on explanation metrics are clearer
3. the explanation effect survives lexical-echo control
4. explanation changes can appear even when `J1` is unchanged itemwise

Most informative completed staged result so far (`qwen2.5:0.5b-instruct`, main, `n = 120`):

- `christian_pre vs secular_pre`, `J1` heart correctness: `+0.033`, 95% CI `[0.000, 0.075]`, permutation `p=0.2095`
- `christian_pre vs secular_pre`, `J1` act correctness: `+0.008`, 95% CI `[-0.017, 0.033]`, permutation `p=1.0`
- `christian_post vs secular_post`, explanation Christianization: `+0.013`, 95% CI `[0.0078, 0.0177]`, permutation `p<0.001`
- `christian_post vs secular_post`, lexical-controlled explanation heart-focus: `+0.015`, 95% CI `[0.0085, 0.0223]`, permutation `p<0.001`
- `same_j1_rate = 1.0` for the matched post comparison

Interpretation:

The staged evidence currently points more strongly to explanation-layer movement than to first-pass Christian-over-secular judgment movement.

This conclusion is now reinforced by the completed `qwen2.5:7b-instruct` full main rerun:

- `christian_pre vs secular_pre`, `J1` heart correctness: `+0.017`, 95% CI `[-0.033, 0.067]`, permutation `p=0.7286`
- `christian_pre vs secular_pre`, `J1` act correctness: `-0.008`, 95% CI `[-0.075, 0.058]`, permutation `p=1.0`
- `christian_post vs secular_post`, explanation Christianization: `+0.049`, 95% CI `[0.0451, 0.0528]`, permutation `p<0.001`
- `christian_post vs secular_post`, lexical-controlled explanation heart-focus: `+0.015`, 95% CI `[0.0109, 0.0194]`, permutation `p<0.001`
- `christian_post vs secular_post`, explanation restructuring: `+0.196`, 95% CI `[0.158, 0.233]`, permutation `p<0.001`
- `same_j1_rate = 1.0` for the matched post comparison

## New V2 Program

A new dissociation-focused benchmark/program now has a completed primary matrix for `0.5B` and a completed confirmatory matrix for `1.5B` (`C0`, `C2`, `C4`):

- benchmark rebuild notes: [benchmark_rebuild_v2.md](benchmark_rebuild_v2.md)
- experiment plan: [experiment_plan_v2.md](experiment_plan_v2.md)
- current results: [heartbench_v2_initial_results.md](heartbench_v2_initial_results.md)
- settings audit: [experiment_settings_audit.md](experiment_settings_audit.md)
- relabel protocol: [heartbench_v2_relabel_protocol.md](heartbench_v2_relabel_protocol.md)

That new program is designed to measure explicit `heart vs act` separation rather than only corrected heart attribution.

Its current benchmark labels are still partly heuristic: the case-level `1-5` heart/act scores are family-template assignments, so the v2 program should be treated as an active follow-on track rather than publication-final ground truth.

## V2 Result: HeartBench-v2-120

Current v2 summary on the rebuilt benchmark:

| Model | Cond | Heart Margin Target | Dissociation Success | Collapse Rate |
|-------|------|---------------------|----------------------|---------------|
| Qwen2.5-0.5B-Instruct | C0 | 0.038 | 0.24 | 0.05 |
| Qwen2.5-0.5B-Instruct | C2 | 0.063 | 0.06 | 0.26 |
| Qwen2.5-0.5B-Instruct | C4 | 0.027 | 0.10 | 0.24 |
| Qwen2.5-1.5B-Instruct | C0 | 0.433 | 0.01 | 0.70 |
| Qwen2.5-1.5B-Instruct | C2 | 1.041 | 0.06 | 0.46 |
| Qwen2.5-1.5B-Instruct | C4 | 1.127 | 0.08 | 0.51 |

Key v2 paired comparisons:

- `0.5B`, `C0 -> C2`: heart-margin gain `+0.0248`, 95% CI `[+0.0042, +0.0458]`, Wilcoxon `p=0.0128`; dissociation-success drops by `-0.18`, 95% CI `[-0.26, -0.11]`, McNemar `p=0.0000615`.
- `1.5B`, `C0 -> C2`: heart-margin gain `+0.6079`, 95% CI `[+0.4322, +0.7869]`, Wilcoxon `p=4.48e-07`; dissociation-success gain `+0.05`, 95% CI `[+0.00, +0.10]`, McNemar `p=0.131`.
- `1.5B`, `C2 -> C4`: heart-margin gain for `C4` `+0.0863`, 95% CI `[+0.0544, +0.1175]`, Wilcoxon `p=9.11e-07`; dissociation-success difference `+0.02`, 95% CI `[-0.02, +0.06]`, McNemar `p=0.617`.

Interpretation:

1. `HeartBench-v2` exposes a collapse problem that the older benchmark hid: both models often blur `heart` and `act`, especially `1.5B` under baseline prompting.
2. On `0.5B`, `C2` strengthens heart-margin separation but clearly worsens true heart-vs-act dissociation.
3. On `1.5B`, both stronger scaffolds sharply increase heart-margin separation and partly reduce collapse relative to baseline, but the confirmatory contrast does not support a specifically Christian advantage over the matched secular scaffold.

## Canonical Evaluation

The canonical evaluation is still the **bias-resistant casewise-logit pipeline**:

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

Active supported paths:

- `src/run_casewise_logit_inference.py`
- `src/score_casewise_results.py`
- `src/analyze_casewise_results.py`
- `results_casewise_logit/`
- `src/run_dual_logit_v2_inference.py`
- `src/score_structured_casewise_results.py`
- `src/analyze_structured_casewise_results.py`
- `results_dual_logit_v2/`

Historical material:

- Pairwise A/B pipelines: `archive/pairwise_ab_pipelines/`
- Detailed corrected rerun report: [bias_resistant_rerun_report.md](bias_resistant_rerun_report.md)
- Audit of the original confounds: [benchmark_confound_audit.md](benchmark_confound_audit.md)

## Bottom Line

The project no longer supports the old claim that Christian heart-focused framing hurts performance on the primary benchmark. The corrected legacy result is narrower, and the new v2 result is more mechanistic:

- `1.5B`: no robust framing advantage and no robust Christian-framing penalty on `HeartBench-240`.
- `0.5B`: weak overall on the corrected primary benchmark, with no evidence that Christian framing helps.
- `HeartBench-v2`: stronger scaffolds clearly change how models separate `heart` from `act`, but the current confirmatory contrast points to a general scaffold effect rather than a uniquely Christian advantage.
