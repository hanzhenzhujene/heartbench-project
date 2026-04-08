# Moral Stories Subset: Benchmark Summary (Primary)

## Overview

The Moral Stories subset is a 240-item pairwise A/B moral comparison benchmark derived from the Moral Stories dataset (Emelin et al., 2021). It serves as the **primary benchmark** for testing whether Christian heart-focused framing changes what small language models treat as morally diagnostic.

- **Source**: [Moral Stories](https://github.com/demelin/moral_stories) (Emelin et al., 2021)
- **Total items**: 240 (stratified subset from 12,000 source items)
- **Format**: Pairwise A/B comparison (Case A vs Case B)
- **Primary label**: `heart_worse` (which case reveals worse inward moral orientation)
- **Secondary label**: `morally_worse` (which case is more morally problematic overall)
- **Splits**: Dev (60 items) / Test (180 items)
- **Role**: Primary benchmark (externally sourced, peer-reviewed dataset)

## Why Moral Stories as Primary

1. **External sourcing**: Items derive from a published, peer-reviewed dataset rather than custom construction, reducing author bias
2. **Crowdsourced norms**: Each item is grounded in a human-written social norm, providing independent validation of the moral contrast
3. **Traceability**: Every item maps to a specific Moral Stories ID, norm, situation, intention, and action pair
4. **Reproducibility**: The selection and conversion pipeline is fully deterministic (seed=42)

## A/B Pair Construction

Each Moral Stories item contains:
- **situation**: Background context
- **intention**: The character's goal/motivation
- **moral_action**: The morally sound behavior
- **immoral_action**: The morally problematic behavior

We construct A/B pairs as:
- **Case A or B** = situation + immoral_action (heart-worse case)
- **Case B or A** = situation + moral_action (heart-better case)
- Counterbalanced: every other item per family is swapped for 50/50 A/B balance

## Family Distribution

| Family | Count | Description |
|--------|-------|-------------|
| Same act, different motive | 40 | Both perform similar actions; motive differs |
| Same restraint, different posture | 40 | Both refrain from acting; inner reason differs |
| Same correction, different heart | 40 | Both confront/correct someone; intent differs |
| Good act, corrupt motive | 40 | Prosocial act with distorted motive vs inwardly sound |
| Flawed act, benevolent motive | 40 | Rough outward act with good motive vs inwardly worse |
| Mixed-motive hard cases | 40 | Both have mixed motives; one is more disordered |

## Difficulty Distribution

| Difficulty | Count |
|------------|-------|
| Easy | 5 |
| Medium | 185 |
| Hard | 50 |

## Gold Label Balance

| Label | A | B |
|-------|---|---|
| heart_worse | 120 | 120 |
| morally_worse | 120 | 120 |

## Domain Coverage

| Domain | Count |
|--------|-------|
| community | 64 |
| workplace | 57 |
| family | 55 |
| friendship | 38 |
| school | 26 |

## Case Length Statistics

- Case A: min=14 words, max=50 words, avg=30.7 words
- Case B: min=14 words, max=54 words, avg=31.1 words
- Mean A-B length difference: 3.0 words (max: 14 words)

## Primary Cue Distribution

| Cue | Count |
|-----|-------|
| motive | 193 |
| manipulation | 34 |
| compassion | 8 |
| vanity | 4 |
| contempt | 1 |

## Selection Pipeline

1. Load all 12,000 Moral Stories items
2. Filter to heart-relevant candidates (11,724 pass)
3. Classify each into family, domain, difficulty, setting, and primary cue
4. Stratified selection: 40 items per family with domain diversity
5. Counterbalance: swap every other item per family for 50/50 A/B balance
6. Create dev/test splits: 60 dev (10 per family) + 180 test (30 per family)

## Files

- `benchmark/moral_stories_subset.jsonl` - Full benchmark (240 items)
- `benchmark/moral_stories_subset.csv` - CSV format
- `benchmark/moral_stories_subset_traced.jsonl` - With source tracing fields (ms_id, ms_norm, ms_intention)
- `benchmark/moral_stories_dev.jsonl` - Dev split (60 items)
- `benchmark/moral_stories_test.jsonl` - Test split (180 items)
- `benchmark/moral_stories_subset_swapped.jsonl` - A/B swapped version (for position bias checks)

## Relationship to HeartBench-240 (Secondary)

HeartBench-240 remains as a supplementary/secondary benchmark with 240 custom-constructed items. The Moral Stories subset and HeartBench-240 use identical:
- A/B comparison format
- Output schema (`heart_worse`, `morally_worse`, `reason_focus`)
- Family taxonomy (6 families)
- Scoring and analysis pipeline

Results are reported separately for each benchmark, enabling cross-benchmark validation.
