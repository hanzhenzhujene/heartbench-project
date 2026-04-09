# HeartBench-v2 Rebuild Notes

## Why the Original Setup Was Not Enough

The earlier benchmark and evaluation setup had three important weaknesses:

1. it often collapsed heart and act into the same gold answer,
2. it allowed strong position-channel artifacts in pairwise `A/B` evaluation,
3. it did not make dissociation an explicit stored target in the benchmark schema.

Those issues made it hard to tell whether a prompt was truly improving inward-motive reasoning, or merely shifting the model's answer style.

## What HeartBench-v2 Changes

`HeartBench-v2-120` is a dissociation-focused rebuild derived from `HeartBench-240`. It keeps the original family structure, but changes the benchmark schema so that heart and act are represented separately.

Each item now stores:

- `gold_case_A_heart_score`
- `gold_case_B_heart_score`
- `gold_case_A_act_score`
- `gold_case_B_act_score`
- `gold_heart_worse`
- `gold_act_worse`
- `dissociation_target`
- `source_item_id`

This makes it possible to evaluate whether a model:

- separates inward disorder from outward act,
- keeps act tied when the act should remain tied,
- succeeds on intentionally dissociative cases instead of collapsing heart and act into one judgment.

Important provenance note:

- `gold_heart_worse` is inherited from the source benchmark
- the new case-level `heart` and `act` scores are currently family-template assignments rather than fresh human annotations

So the v2 benchmark is already useful for testing dissociation-oriented prompting, but the numeric `1-5` label magnitudes should still be treated as provisional rather than publication-final.

## Selection Strategy

The v2 subset is not a random slice. It is a higher-precision slice chosen to make motive evidence more explicit and to reduce cheap surface shortcuts.

The selection heuristic favors:

- explicit motive markers such as `because`, `hoping`, `trying to`, `privately`
- higher lexical overlap between paired cases when families are supposed to be closely matched
- smaller length gaps between case A and case B

The heuristic penalizes:

- strong lexical giveaways such as `cruel`, `evil`, `wicked`, `kind`

## Current Benchmark Composition

Current `HeartBench-v2-120` properties:

- `120` total items
- `20` items in each of `6` families
- `100/120` items marked `dissociation_target = true`
- `gold_heart_worse`: `A=59`, `B=61`
- `gold_act_worse`: `A=19`, `B=21`, `tie=80`

That last line is the key design change: most dissociation-target items now expect the outward act comparison to remain tied, while the heart comparison still differs.

## New Evaluation Logic

The old pairwise answer-channel was replaced with a casewise dual-logit scorer:

- each case is scored independently on the `heart` dimension
- each case is scored independently on the `act` dimension
- the pairwise comparison is derived offline from those score distributions

This makes the main evaluation robust to raw `A/B` answer bias.

## Stronger Intervention

The new interventions are stronger than simple framing:

- `C0`: baseline
- `C1`: neutral scaffold
- `C2`: Christian scaffold
- `C3`: scripture-style scaffold
- `C4`: secular matched scaffold

All of them now explicitly tell the model to keep outward act and inward heart separate, and to answer with a single `1-5` digit on one dimension at a time.

## What the New Metrics Mean

Primary v2 metrics:

- `mean_aligned_heart_margin_target`
- `dissociation_success_rate`
- `collapse_rate`

These are more diagnostic than raw accuracy alone:

- `mean_aligned_heart_margin_target` asks whether the model separates the correct heart-worse case more strongly on items designed to stress that distinction
- `dissociation_success_rate` asks whether the model gets both heart and act right on the same dissociation item
- `collapse_rate` asks whether the model still collapses heart and act into the same predicted pairwise winner

## Files

- `src/build_heartbench_v2.py`
- `benchmark/heartbench_v2_120.jsonl`
- `benchmark/heartbench_v2_dev.jsonl`
- `benchmark/heartbench_v2_test.jsonl`
- `src/run_dual_logit_v2_inference.py`
- `src/score_structured_casewise_results.py`
- `src/analyze_structured_casewise_results.py`

## Commands

```bash
python3 src/build_heartbench_v2.py
python3 src/run_dual_logit_v2_inference.py --benchmark heartbench_v2 --prefer-mps
python3 src/score_structured_casewise_results.py --benchmark heartbench_v2 --results-root results/dual_logit_v2
python3 src/analyze_structured_casewise_results.py --benchmark heartbench_v2 --results-root results/dual_logit_v2
```
