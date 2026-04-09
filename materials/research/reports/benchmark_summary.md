# HeartBench-240: Benchmark Summary (Secondary/Supplementary)

## Overview

HeartBench-240 is a pairwise A/B moral comparison benchmark designed to test whether language models can distinguish outward action from inward motive and heart-level moral orientation.

**Note**: HeartBench-240 serves as the **secondary/supplementary** benchmark. The **primary** benchmark is the Moral Stories subset (see `moral_stories_benchmark_summary.md`), which derives from the externally sourced, peer-reviewed Moral Stories dataset (Emelin et al., 2021). Both benchmarks use identical formats and scoring.

- **Total items**: 240
- **Format**: Pairwise A/B comparison (Case A vs Case B)
- **Primary label**: `heart_worse` (which case reveals worse inward moral orientation)
- **Secondary label**: `morally_worse` (which case is more morally problematic overall)
- **Splits**: Dev (60 items) / Test (180 items)

## Family Distribution

| Family | Count | Description |
|--------|-------|-------------|
| Same act, different motive | 40 | Both perform the same outward action; motive differs |
| Same restraint, different posture | 40 | Both refrain from acting; inner reason differs |
| Same correction, different heart | 40 | Both confront/correct someone; intent differs |
| Good act, corrupt motive | 40 | Prosocial act with distorted motive vs less flashy but inwardly sound |
| Flawed act, benevolent motive | 40 | Rough outward act with good motive vs smoother but inwardly worse |
| Mixed-motive hard cases | 40 | Both have mixed motives; one is more disordered |

## Source Distribution

| Source | Count |
|--------|-------|
| Adapted (source-inspired) | 120 |
| Original (controlled) | 120 |

## Difficulty Distribution

| Difficulty | Count |
|------------|-------|
| Easy | 68 |
| Medium | 125 |
| Hard | 47 |

## Gold Label Balance

| Label | A | B |
|-------|---|---|
| heart_worse | 120 | 120 |
| morally_worse | 120 | 120 |

## Case Length Statistics

- Case A: min=14 words, max=32 words, avg=22.5 words
- Case B: min=14 words, max=32 words, avg=22.3 words
- Mean A-B length difference: 3.5 words (max: 13 words)

## Domain Coverage

| Domain | Count |
|--------|-------|
| workplace | 67 |
| community | 60 |
| family | 41 |
| school | 37 |
| friendship | 35 |

## Primary Cue Distribution

| Cue | Count |
|-----|-------|
| motive | 65 |
| manipulation | 58 |
| vanity | 57 |
| contempt | 56 |
| responsibility | 3 |
| compassion | 1 |

## Design Principles

1. **Theology-neutral items**: No theological vocabulary in case text
2. **Controlled contrasts**: Each pair varies inward orientation while holding outward features as constant as possible
3. **Behavioral motive cues**: Motives shown through behavior, not labels
4. **No outcome domination**: Items should not be solvable from consequence alone
5. **Balanced counterbalancing**: Exactly 50% A, 50% B gold labels

## Files

- `materials/benchmark/heartbench_240.jsonl` - Full benchmark (240 items)
- `materials/benchmark/heartbench_240.csv` - CSV format
- `materials/benchmark/heartbench_dev.jsonl` - Dev split (60 items, 10 per family)
- `materials/benchmark/heartbench_test.jsonl` - Test split (180 items, 30 per family)
- `materials/benchmark/heartbench_240_swapped.jsonl` - A/B swapped version (for position bias checks)
- `materials/benchmark/annotation_guide.md` - Annotation guidelines
- `materials/benchmark/construction_notes.md` - Construction methodology notes
