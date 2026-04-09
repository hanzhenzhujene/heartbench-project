# HeartBench-v2 Current Results

## Status

As of 2026-04-08, the rebuilt `HeartBench-v2-120` benchmark and the stronger scaffold intervention are implemented, audited, and run through the planned primary matrix.

Completed:

- benchmark rebuild: `HeartBench-v2-120`
- full primary-matrix run for `Qwen2.5-0.5B-Instruct` across `C0-C4`
- confirmatory primary-matrix run for `Qwen2.5-1.5B-Instruct` across `C0`, `C2`, `C4`
- scoring and paired analysis for all completed conditions
- settings audit and relabel-template export

Not yet complete:

- optional dev diagnostic group for `Qwen2.5-1.5B-Instruct`
- fresh human relabeling of case-level `1-5` heart and act scores

Labeling caveat:

- `gold_heart_worse` is inherited from the source benchmark
- case-level `heart` and `act` scores are currently assigned by family template rather than fresh human annotation

So these results are best read as strong prompt-diagnostic evidence, not yet as publication-final benchmark evidence.

Prompt-comparison caveat:

- `C0 vs C2` changes both scaffold strength and Christian framing.
- `C2 vs C4` is the cleaner test of whether any remaining effect is specifically Christian rather than scaffold-general.

## Why This New Setup Is More Informative

The original benchmark mostly rewarded a single collapsed heart/moral answer. `HeartBench-v2` changes that by storing separate heart and act labels and by making dissociation a first-class target.

That produces a much sharper failure signature:

- whether a model separates the heart signal strongly enough
- whether it preserves act ties when it should
- whether it collapses heart and act into the same pairwise judgment

## Main Completed Result: 0.5B Full Matrix

Full results:

- file: `materials/results/dual_logit_v2/heartbench_v2/main/analysis.json`

Summary for `Qwen2.5-0.5B-Instruct`:

- `C0`
  - `heart_resolved_accuracy = 0.627`
  - `mean_aligned_heart_margin_target = 0.038`
  - `dissociation_success_rate = 0.24`
  - `collapse_rate = 0.05`
- `C1`
  - `heart_resolved_accuracy = 0.513`
  - `mean_aligned_heart_margin_target = 0.004`
  - `dissociation_success_rate = 0.07`
  - `collapse_rate = 0.16`
- `C2`
  - `heart_resolved_accuracy = 0.575`
  - `mean_aligned_heart_margin_target = 0.063`
  - `dissociation_success_rate = 0.06`
  - `collapse_rate = 0.26`
- `C3`
  - `heart_resolved_accuracy = 0.500`
  - `mean_aligned_heart_margin_target = 0.069`
  - `dissociation_success_rate = 0.09`
  - `collapse_rate = 0.29`
- `C4`
  - `heart_resolved_accuracy = 0.489`
  - `mean_aligned_heart_margin_target = 0.027`
  - `dissociation_success_rate = 0.10`
  - `collapse_rate = 0.24`

## Paired Findings: 0.5B

Two patterns are already clear and statistically meaningful.

### 1. `C2` increases heart-margin separation, but hurts dissociation

Compared with `C0` on dissociation-target items:

- margin gain: `+0.0248`
- bootstrap 95% CI: `[+0.0042, +0.0458]`
- Wilcoxon `p = 0.0128`

But:

- dissociation-success gain: `-0.18`
- bootstrap 95% CI: `[-0.26, -0.11]`
- McNemar `p = 0.0000615`

Interpretation:

`C2` makes the model separate the heart-worse case more strongly, but it also makes the model much worse at keeping heart and act correctly distinguished on the same item. In other words, the Christian scaffold increases inward-focus signal but also increases collapse.

### 2. `C4` is a useful dissociation-aware control

Compared with `C2`:

- margin change for `C4`: `-0.0367` relative to `C2`
- bootstrap 95% CI: `[-0.0468, -0.0255]`
- Wilcoxon `p < 1e-7`

But:

- dissociation-success gain for `C4`: `+0.04`
- bootstrap 95% CI: `[-0.02, +0.10]`
- McNemar `p = 0.343`

Interpretation:

`C2` pushes heart separation harder than `C4`, but not in a way that translates into better dissociation success. `C4` is less aggressive on heart margin and somewhat less collapse-prone.

## Confirmatory Result: 1.5B Focused Matrix

Completed conditions:

- `Qwen2.5-1.5B-Instruct / C0`
  - `heart_resolved_accuracy = 0.552`
  - `heart_tie_rate = 0.20`
  - `act_pair_accuracy = 0.35`
  - `mean_aligned_heart_margin_target = 0.433`
  - `dissociation_success_rate = 0.01`
  - `collapse_rate = 0.70`
- `Qwen2.5-1.5B-Instruct / C2`
  - `heart_resolved_accuracy = 1.000`
  - `heart_tie_rate = 0.442`
  - `act_pair_accuracy = 0.367`
  - `mean_aligned_heart_margin_target = 1.041`
  - `dissociation_success_rate = 0.06`
  - `collapse_rate = 0.46`
- `Qwen2.5-1.5B-Instruct / C4`
  - `heart_resolved_accuracy = 1.000`
  - `heart_tie_rate = 0.375`
  - `act_pair_accuracy = 0.333`
  - `mean_aligned_heart_margin_target = 1.127`
  - `dissociation_success_rate = 0.08`
  - `collapse_rate = 0.51`

Interpretation:

The stronger `1.5B` model is not simply "better" on the rebuilt benchmark. Under baseline prompting it already shows large heart-margin separation, but it fails badly at keeping act and heart apart and collapses them together on most dissociation-target items. Both stronger scaffolds sharply increase heart-margin separation and reduce collapse relative to baseline, but neither scaffold produces a large or clearly reliable gain in full dissociation success.

### Paired Findings: 1.5B

Compared with `C0` on dissociation-target items:

- `C2` margin gain: `+0.6079`
- bootstrap 95% CI: `[+0.4322, +0.7869]`
- Wilcoxon `p = 4.48e-07`

But:

- `C2` dissociation-success gain: `+0.05`
- bootstrap 95% CI: `[+0.00, +0.10]`
- McNemar `p = 0.131`

Compared with `C2`:

- `C4` margin gain: `+0.0863`
- bootstrap 95% CI: `[+0.0544, +0.1175]`
- Wilcoxon `p = 9.11e-07`

But:

- `C4` dissociation-success gain: `+0.02`
- bootstrap 95% CI: `[-0.02, +0.06]`
- McNemar `p = 0.617`

Interpretation:

On `1.5B`, the main v2 effect is not a specifically Christian advantage. It is a broader scaffold effect: both `C2` and `C4` push heart-margin separation far above baseline and partly reduce the worst collapse behavior, while `C4` is at least as strong as `C2` on the confirmatory contrasts.

## Current Conclusion

The rebuilt benchmark is working in the intended sense: it produces much more interesting and theoretically diagnostic results than the older collapsed benchmark.

The clearest completed conclusion so far is:

1. `HeartBench-v2` reveals a real tradeoff between stronger heart-focused separation and successful heart-vs-act dissociation.
2. On `0.5B`, `C2` strengthens heart-margin separation but significantly harms dissociation success.
3. On `1.5B`, even baseline prompting exposes a major collapse problem that the earlier benchmark hid.
4. On `1.5B`, stronger scaffolds (`C2` and `C4`) greatly increase heart-margin separation and partly reduce collapse, but the confirmatory contrast does not support a specifically Christian advantage over the matched secular scaffold.

## Next Step

The highest-value remaining steps are now:

- finish the optional `diagnostic_1p5b_dev` group for quicker iteration checks
- run the human relabel workflow in `materials/benchmark/heartbench_v2_relabel_blind_template.csv`
- rebuild `HeartBench-v2` with fresh case-level labels before treating the v2 metrics as publication-final
