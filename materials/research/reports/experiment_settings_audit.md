# Experiment Settings Audit

## Dual-Logit V2
- config: `heartbench_v2_dual_logit`
- default benchmark: `heartbench_v2`
- conditions: `C0, C1, C2, C3, C4`
- models: `Qwen/Qwen2.5-0.5B-Instruct, Qwen/Qwen2.5-1.5B-Instruct`
- execution groups:
  - `primary_0p5b_full`: benchmark=`heartbench_v2`, models=`Qwen/Qwen2.5-0.5B-Instruct`, conditions=`C0, C1, C2, C3, C4`
  - `primary_1p5b_confirmatory`: benchmark=`heartbench_v2`, models=`Qwen/Qwen2.5-1.5B-Instruct`, conditions=`C0, C2, C4`
  - `diagnostic_1p5b_dev`: benchmark=`heartbench_v2_dev`, models=`Qwen/Qwen2.5-1.5B-Instruct`, conditions=`C0, C2, C4`
- prompt lengths:
  - `dual_logit_v2_baseline.txt`: 81 words, 477 chars, 19 lines
  - `dual_logit_v2_neutral_scaffold.txt`: 146 words, 908 chars, 26 lines
  - `dual_logit_v2_christian_scaffold.txt`: 154 words, 928 chars, 24 lines
  - `dual_logit_v2_scripture_scaffold.txt`: 125 words, 714 chars, 24 lines
  - `dual_logit_v2_secular_scaffold.txt`: 143 words, 896 chars, 24 lines

## Structured V2
- config: `heartbench_v2_structured_casewise`
- default benchmark: `heartbench_v2`
- conditions: `C0, C1, C2, C3, C4`

## Benchmarks
### heartbench_v2
- path: `materials/benchmark/heartbench_v2_120.jsonl`
- items: `120`
- families: `{'flawed_act_benevolent_motive': 20, 'good_act_corrupt_motive': 20, 'mixed_motive_hard': 20, 'same_act_different_motive': 20, 'same_correction_different_heart': 20, 'same_restraint_different_posture': 20}`
- gold_heart_worse: `{'A': 59, 'B': 61}`
- gold_act_worse: `{'A': 19, 'B': 21, 'tie': 80}`
- dissociation_target_n: `100`
- benchmark_versions: `['heartbench_v2.1']`
- label_provenance_case_scores: `['family_template_v1']`
- label_provenance_heart_pair: `['inherited_from_heartbench_240']`

### heartbench_v2_dev
- path: `materials/benchmark/heartbench_v2_dev.jsonl`
- items: `30`
- families: `{'flawed_act_benevolent_motive': 5, 'good_act_corrupt_motive': 5, 'mixed_motive_hard': 5, 'same_act_different_motive': 5, 'same_correction_different_heart': 5, 'same_restraint_different_posture': 5}`
- gold_heart_worse: `{'A': 16, 'B': 14}`
- gold_act_worse: `{'A': 6, 'B': 4, 'tie': 20}`
- dissociation_target_n: `25`
- benchmark_versions: `['heartbench_v2.1']`
- label_provenance_case_scores: `['family_template_v1']`
- label_provenance_heart_pair: `['inherited_from_heartbench_240']`

## Results Completeness
- results dir: `materials/results/dual_logit_v2/heartbench_v2/main`
- group `primary_0p5b_full`:
  - `Qwen2.5-0.5B-Instruct/C0`: present
  - `Qwen2.5-0.5B-Instruct/C1`: present
  - `Qwen2.5-0.5B-Instruct/C2`: present
  - `Qwen2.5-0.5B-Instruct/C3`: present
  - `Qwen2.5-0.5B-Instruct/C4`: present
- group `primary_1p5b_confirmatory`:
  - `Qwen2.5-1.5B-Instruct/C0`: present
  - `Qwen2.5-1.5B-Instruct/C2`: present
  - `Qwen2.5-1.5B-Instruct/C4`: present
- group `diagnostic_1p5b_dev`:
  - `Qwen2.5-1.5B-Instruct/C0`: missing
  - `Qwen2.5-1.5B-Instruct/C2`: missing
  - `Qwen2.5-1.5B-Instruct/C4`: missing

## Warnings
- Dual-logit prompt length spread is large; C0 vs scaffold comparisons combine intervention content and prompt length.
- HeartBench-v2 case-level 1-5 scores are still template-assigned rather than freshly human-annotated.
- Some configured execution groups are incomplete: diagnostic_1p5b_dev: Qwen2.5-1.5B-Instruct/C0, Qwen2.5-1.5B-Instruct/C2, Qwen2.5-1.5B-Instruct/C4
