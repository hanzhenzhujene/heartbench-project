# Staged Paper Status

## Date

2026-04-08

## Completed

- Full 30-item staged dev rerun for:
  - `qwen2.5:7b-instruct`
  - `qwen2.5:0.5b-instruct`
- Full 120-item staged main rerun for:
  - `qwen2.5:7b-instruct`
  - `qwen2.5:0.5b-instruct`

Output roots:

- `materials/results/staged_paper/heartbench_v2_dev/dev`
- `materials/results/staged_paper/heartbench_v2/main`

## Main Takeaway So Far

The completed staged results support the cleaner mechanism claim:

> Christian framing appears to affect explanation language more strongly than first-pass exposed judgment.

This pattern is already visible in the two-model dev rerun and remains visible in the completed `qwen2.5:0.5b-instruct` full main rerun.

## Completed Main Result: qwen2.5:7b-instruct

Direct Christian-versus-secular matched contrasts on `HeartBench-v2` main (`n = 120`):

- `christian_pre vs secular_pre`, `J1` heart correctness:
  - mean diff `+0.017`
  - 95% CI `[-0.033, 0.067]`
  - permutation `p = 0.7286`
- `christian_pre vs secular_pre`, `J1` act correctness:
  - mean diff `-0.008`
  - 95% CI `[-0.075, 0.058]`
  - permutation `p = 1.0`
- `christian_post vs secular_post`, explanation Christianization:
  - mean diff `+0.049`
  - 95% CI `[0.0451, 0.0528]`
  - permutation `p < 0.001`
- `christian_post vs secular_post`, lexical-controlled explanation heart focus:
  - mean diff `+0.015`
  - 95% CI `[0.0109, 0.0194]`
  - permutation `p < 0.001`
- `christian_post vs secular_post`, explanation restructuring:
  - mean diff `+0.196`
  - 95% CI `[0.158, 0.233]`
  - permutation `p < 0.001`

Interpretation:

1. On the larger model too, first-pass Christian-over-secular movement is weak.
2. Explanation-layer Christian-over-secular movement is large and highly reliable.
3. The explanation effect survives lexical control, so it is not reducible to simple frame-word echo.

## Completed Main Result: qwen2.5:0.5b-instruct

Direct Christian-versus-secular matched contrasts on `HeartBench-v2` main (`n = 120`):

- `christian_pre vs secular_pre`, `J1` heart correctness:
  - mean diff `+0.033`
  - 95% CI `[0.000, 0.075]`
  - permutation `p = 0.2095`
- `christian_pre vs secular_pre`, `J1` act correctness:
  - mean diff `+0.008`
  - 95% CI `[-0.017, 0.033]`
  - permutation `p = 1.0`
- `christian_post vs secular_post`, explanation Christianization:
  - mean diff `+0.013`
  - 95% CI `[0.0078, 0.0177]`
  - permutation `p < 0.001`
- `christian_post vs secular_post`, lexical-controlled explanation heart focus:
  - mean diff `+0.015`
  - 95% CI `[0.0085, 0.0223]`
  - permutation `p < 0.001`
- `christian_post vs secular_post`, explanation restructuring:
  - mean diff `+0.069`
  - 95% CI `[0.010, 0.129]`
  - permutation `p = 0.0366`

Interpretation:

1. First-pass Christian-over-secular movement is weak.
2. Explanation-layer Christian-over-secular movement is clearer.
3. The explanation effect survives lexical control, so it is not just direct frame-word echo.

## Same-J1 Explanation Shift

The strongest mechanism result in the completed main runs is that explanation changes persist even when first-pass judgment does not:

- `qwen2.5:7b-instruct`:
  - `same_j1_rate = 1.0`
  - lexical-controlled explanation heart-focus shift `+0.015`, permutation `p < 0.001`
  - Christianization shift `+0.049`, permutation `p < 0.001`
  - restructuring shift `+0.196`, permutation `p < 0.001`
- `same_j1_rate = 1.0`
- lexical-controlled explanation heart-focus shift `+0.015`, permutation `p < 0.001`
- Christianization shift `+0.013`, permutation `p < 0.001`
- restructuring shift `+0.069`, permutation `p = 0.0366`

This is direct evidence for stage dissociation.

## Dev Result: qwen2.5:7b-instruct

The dev rerun (`n = 30`) still matches the same pattern seen in the full main run:

- `christian_pre vs secular_pre`, `J1` heart correctness: `-0.067`, permutation `p = 0.4979`
- `christian_pre vs secular_pre`, `J1` act correctness: `-0.100`, permutation `p = 0.2421`
- `christian_post vs secular_post`, explanation Christianization: `+0.052`, permutation `p < 0.001`
- `christian_post vs secular_post`, lexical-controlled explanation heart focus: `+0.020`, permutation `p < 0.001`
- `christian_post vs secular_post`, explanation restructuring: `+0.225`, permutation `p = 0.0001`
- `same_j1_rate = 1.0`

Interpretation:

The dev result was an accurate preview of the final main result: little sign of Christian-over-secular movement in `J1`, but clear explanation-layer movement after post framing.

## Revision Metrics

Revision behavior should not currently be the paper’s main headline:

- on `qwen2.5:0.5b-instruct`, `christian_post` modestly lowers revision rates relative to `secular_post`
- on `qwen2.5:7b-instruct` dev, revision differences are weak or null

Revision is still worth reporting, but it is weaker evidence than the explanation-layer contrasts.

## Next

1. Backfill the manuscript-ready prose in `materials/research/reports/staged_paper_revision_packet.md` with the completed main numbers.
2. Decide whether to keep the one-paraphrase-per-family main text as confirmatory and move multi-paraphrase runs to robustness.
3. If needed, launch the multi-paraphrase robustness rerun now that the single-paraphrase main result is complete.
