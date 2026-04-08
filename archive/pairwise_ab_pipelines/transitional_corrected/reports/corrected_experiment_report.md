# Corrected Experiment Report

## Why the original setup was misleading

The original experiment mixed three confounds:

1. **A/B position bias**: prompt conditions often caused the model to prefer a raw answer letter (`A` or `B`) regardless of content.
2. **Unsupported heart inference**: the Moral Stories conversion often asked for heart-level judgments without explicit motive evidence in the shipped case text.
3. **Unused secondary task**: prompts asked for `morally_worse`, but the shipped benchmarks had `gold_heart_worse == gold_morally_worse` for every item.

The audit in `benchmark_confound_audit.md` documents the largest benchmark-side issues:

- Moral Stories subset: 240/240 heart labels equal moral labels
- Moral Stories subset: 240/240 traced intentions omitted from final case text
- Moral Stories subset: only 52/240 shipped items contain explicit motive evidence in the case text
- HeartBench-240: 240/240 heart labels equal moral labels

## Corrected setup

The rerun used a corrected setup with three changes:

1. **Heart-only output schema**: removed the unused `morally_worse` task
2. **Evidence-grounded prompts**: all prompt conditions explicitly forbid inventing hidden motives
3. **Order-balanced scoring**: each item is run in both original and swapped A/B order, then normalized back to the original orientation

Two corrected benchmarks were used:

- `heartbench_dev`: 60-item stratified diagnostic slice
- `moral_stories_supported`: 52-item externally sourced subset filtered to explicit motive support in the shipped case text

## Corrected rerun results

### HeartBench dev (60 items), Qwen2.5-1.5B-Instruct

Completed conditions: `C0`, `C1`, `C2`

| Condition | Order-Avg Acc | Agreement | Resolved Coverage | Resolved Acc | Raw A Rate (orig) | Raw A Rate (swap) |
|-----------|---------------|-----------|-------------------|--------------|-------------------|-------------------|
| C0 | 0.675 | 0.450 | 27/60 | 0.889 | 0.267 | 0.217 |
| C1 | 0.525 | 0.050 | 3/60 | 1.000 | 0.033 | 0.017 |
| C2 | 0.500 | 0.000 | 0/60 | N/A | 1.000 | 1.000 |

Interpretation:

- Under corrected scoring, `C0` retains real order-invariant signal.
- `C1` largely collapses into order-instability rather than showing a trustworthy gain.
- `C2` no longer appears as a meaningful performance drop with statistical force; instead it is revealed as **pure raw-label bias** (`A` in both orders, 0% agreement).

### Moral Stories supported subset (52 items), Qwen2.5-1.5B-Instruct

Completed conditions: `C0`, `C2`

| Condition | Order-Avg Acc | Agreement | Resolved Coverage | Resolved Acc | Raw A Rate (orig) | Raw A Rate (swap) |
|-----------|---------------|-----------|-------------------|--------------|-------------------|-------------------|
| C0 | 0.683 | 0.365 | 19/52 | 1.000 | 0.269 | 0.327 |
| C2 | 0.500 | 0.000 | 0/52 | N/A | 1.000 | 1.000 |

Interpretation:

- The external benchmark shows the same corrected pattern.
- Baseline retains usable order-invariant signal.
- Christian framing (`C2`) again collapses to **raw `A` in both orders**, producing 0 resolved items.

## Main conclusion after correction

The original headline result, "Christian framing significantly hurts heart attribution," should **not** be treated as a clean benchmark finding.

After correcting the setup:

- the old `C2` degradation is best understood as a **prompt-induced A/B label bias artifact**
- the corrected evaluation does **not** support a robust positive effect for `C2`
- the corrected evaluation also does **not** support the old strong negative conclusion in its original form

What it supports instead is narrower:

- baseline prompts produce some genuine order-invariant heart judgments
- the heart-framed prompts, especially `C2`, still induce severe order-fixed behavior
- the corrected order-balanced metric prevents that bias from being mistaken for a real condition effect
