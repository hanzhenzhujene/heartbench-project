# Archived Pairwise A/B Pipelines

This directory preserves the superseded pairwise evaluation paths that were used earlier in the project.

They are archived for historical reference and reproducibility of the older writeups, but they are no longer the supported evaluation surface of the repository.

## Why these were archived

The original pairwise setup was confounded by raw `A/B` answer-channel bias. That artifact was strong enough to create a misleading headline result about `C2`.

The active repository now uses the **casewise-logit** pipeline instead:

- `src/run_casewise_logit_inference.py`
- `src/score_casewise_results.py`
- `src/analyze_casewise_results.py`

## Contents

### `original/`

The original pairwise A/B pipeline and its outputs:

- legacy pairwise inference, scoring, and analysis scripts
- original pairwise configs and prompt templates
- original pairwise reports
- original pairwise result directories

### `transitional_corrected/`

The later order-balanced pairwise correction attempt:

- transitional corrected pairwise scripts
- corrected pairwise configs and prompt templates
- corrected pairwise report
- corrected pairwise result directories

## Important note

These archived materials are preserved as snapshots, not as first-class maintained entry points. The canonical result for the project is the bias-resistant casewise-logit rerun described in:

- [../../research/reports/bias_resistant_rerun_report.md](../../research/reports/bias_resistant_rerun_report.md)
- [../../research/reports/final_status.md](../../research/reports/final_status.md)
