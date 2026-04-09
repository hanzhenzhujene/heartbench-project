# Experiment Plan V2

## Summary

This experiment replaces the older pairwise A/B setup with a benchmark and intervention that explicitly target **heart vs act separation**.

Core design choices:

- benchmark: `HeartBench-v2-120`
- benchmark role: primary
- intervention strength: framing plus explicit scaffold
- primary analysis focus: margin/compression on the heart dimension, especially on dissociation-target items
- model matrix:
  - `Qwen2.5-0.5B-Instruct`: full `C0-C4` matrix
  - `Qwen2.5-1.5B-Instruct`: focused confirmatory contrasts `C0`, `C2`, `C4`
- reference baseline: the older corrected casewise-logit pipeline remains available as the last fully completed benchmark track; it is not archived, but it is not the dissociation-focused instrument for this experiment

## Benchmark Design

`HeartBench-v2-120` is a high-precision subset derived from the existing `HeartBench-240`, rebuilt to store separate gold labels for:

- case-level heart score
- case-level outward act score
- pairwise `gold_heart_worse`
- pairwise `gold_act_worse`
- `dissociation_target`

Design goals:

1. make heart and act explicit, rather than collapsing them into one binary label
2. include many items where act is tied but heart differs
3. include a smaller slice where act and heart genuinely cross
4. preserve family balance with `20` items per family

Current label provenance:

- `gold_heart_worse` is inherited from the source `HeartBench-240` pairwise label
- the new case-level `1-5` heart and act scores are currently assigned by family-specific templates, not by fresh human annotation
- that means pairwise dissociation analyses are already meaningful, but the exact numeric score magnitudes should still be treated as provisional until manual relabeling

Current benchmark balance:

- `120` total items
- `20` items in each of `6` families
- `100/120` items marked `dissociation_target = true`
- `gold_heart_worse`: `A=59`, `B=61`
- `gold_act_worse`: `A=19`, `B=21`, `tie=80`

Files:

- `benchmark/heartbench_v2_120.jsonl`
- `benchmark/heartbench_v2_dev.jsonl`
- `benchmark/heartbench_v2_test.jsonl`
- `src/build_heartbench_v2.py`

## Intervention Design

The new conditions are stronger than simple framing. They explicitly scaffold separation between outward deed and inward orientation.

Conditions:

- `C0`: baseline dual-logit
- `C1`: neutral scaffold
- `C2`: Christian scaffold
- `C3`: scripture-style scaffold
- `C4`: secular matched scaffold

All conditions:

- ask for one dimension at a time
- preserve the distinction between outward act and inward heart
- use the same 1-5 scale
- reply with a single digit only

The Christian intervention is now stronger because it explicitly instructs the model to distinguish outward deed from the heart, and to attend to categories like pride, mercy, contempt, manipulation, and self-seeking when the text supports them.

## Inference and Metrics

Primary inference pipeline:

- `src/run_dual_logit_v2_inference.py`
- `research/configs/experiment_dual_logit_v2.yaml`
- `research/configs/prompts_dual_logit_v2.yaml`

For each case, the model is scored twice:

1. outward act dimension
2. inward heart dimension

Primary metrics:

- `mean_aligned_heart_margin_target`
- `dissociation_success_rate`
- `collapse_rate`

Secondary metrics:

- resolved heart accuracy
- act pair accuracy
- heart tie rate
- act tie rate

Confirmatory paired comparisons:

- `C0 vs C2`
- `C2 vs C4`

Interpretation guardrail:

- `C0 vs C2` is not a pure worldview-wording contrast. It changes both scaffold strength and explicitly Christian framing.
- `C2 vs C4` is the closest approximation to a Christian-vs-secular semantic contrast within the v2 design.

Exploratory paired comparisons:

- `C0 vs C1`
- `C2 vs C3`

Statistical tests:

- paired bootstrap confidence intervals for margin differences
- Wilcoxon signed-rank for paired margin outcomes
- McNemar plus paired bootstrap for dissociation success

## Commands

```bash
# rebuild benchmark
python3 src/build_heartbench_v2.py

# run primary experiment
python3 src/run_dual_logit_v2_inference.py --group primary_0p5b_full
python3 src/run_dual_logit_v2_inference.py --group primary_1p5b_confirmatory

# score and analyze
python3 src/score_structured_casewise_results.py --benchmark heartbench_v2 --results-root results/dual_logit_v2
python3 src/analyze_structured_casewise_results.py --benchmark heartbench_v2 --results-root results/dual_logit_v2
```

## Interpretation Standard

The experiment will count as successful if it shows any of the following on the new primary benchmark:

1. stronger heart-margin separation under scaffolded conditions than under `C0`
2. improved dissociation success on items where heart and act are intentionally separated
3. a meaningful difference between `C2` and `C4`, or a clear null showing the effect is semantic rather than distinctly Christian

Even if raw heart accuracy stays flat, the experiment is still informative if it shows that intervention changes how strongly the model separates heart from act.

Interpretation notes:

- `heart_resolved_accuracy` is secondary because a strong scaffold can increase ties or calibration changes without necessarily making the discrete winner more often correct.
- `mean_aligned_heart_margin_target` is the main readout for whether a condition increases heart-sensitive separation on items intentionally built to separate heart from act.
- `dissociation_success_rate` is the clearest direct test of the benchmark's central construct: whether the model can get heart and act right at the same time when they come apart.
