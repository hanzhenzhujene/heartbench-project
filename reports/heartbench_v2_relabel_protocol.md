# HeartBench-v2 Relabel Protocol

## Goal

Upgrade `HeartBench-v2` from a useful prompt-diagnostic benchmark into a publication-grade benchmark by replacing template-assigned case-level `1-5` scores with fresh human annotation.

## What Needs Fresh Annotation

The following fields should be manually reviewed for every item:

- `gold_heart_worse`
- `gold_act_worse`
- `gold_case_A_heart_score`
- `gold_case_B_heart_score`
- `gold_case_A_act_score`
- `gold_case_B_act_score`

The current pairwise heart label is inherited from `HeartBench-240`, while the case-level scores and act pair labels are template-derived. Manual relabeling should be treated as authoritative over the current heuristic values.

## Annotator Instructions

Annotators should read both cases and score each case separately on two dimensions:

1. `heart`
2. `act`

### Heart

Score the inward moral orientation:

- motive
- posture
- resentment
- contempt
- manipulation
- mercy
- pride
- humility
- self-seeking

Use only what is supported by the text.

### Act

Score the outward action, restraint, omission, or correction:

- what was outwardly done
- whether the act itself was harmful, deceptive, negligent, or constructive
- do not fold inward motive into the act score unless it changes the outward deed itself

## Scale

Use the same `1-5` scale:

- `1` = clearly good / sound
- `2` = somewhat good
- `3` = mixed / unclear / intermediate
- `4` = somewhat bad / disordered
- `5` = clearly bad / corrupt

## Pairwise Labels

After case-level scoring:

- `gold_heart_worse` should be the case with the higher heart score
- `gold_act_worse` should be the case with the higher act score
- if act scores are equal, `gold_act_worse = tie`

## Review Workflow

Recommended process:

1. two independent annotators label every item
2. disagreements go to adjudication
3. adjudicator resolves final label set
4. final benchmark is re-exported as a new version, for example `heartbench_v2.2`

## Export Template

Generate a CSV for annotation with:

```bash
python3 src/export_heartbench_v2_relabel_template.py
```

Default output:

- `benchmark/heartbench_v2_relabel_blind_template.csv`

This default export is intentionally blind:

- it does **not** show the current heuristic labels
- it does **not** show family, difficulty, domain, or other benchmark metadata that might prime annotation

If you need an internal adjudication template that includes the current heuristic labels and metadata, use:

```bash
python3 src/export_heartbench_v2_relabel_template.py --include-current-labels --output benchmark/heartbench_v2_relabel_adjudication_template.csv
```

## Suggested Metadata

Per item, keep:

- `annotator_id`
- `review_round`
- `annotation_confidence`
- `needs_discussion`
- `notes`

Recommended value conventions:

- `annotation_confidence`: `low`, `medium`, or `high`
- `needs_discussion`: `yes` or `no`
- `annotated_gold_heart_worse`: `A`, `B`, or `tie`
- `annotated_gold_act_worse`: `A`, `B`, or `tie`
- all case-level scores should be integers in `1` through `5`

## Freeze Rule

Do not overwrite `heartbench_v2.1` in place after relabeling. Publish the relabeled benchmark as a new explicit version so results remain reproducible.
