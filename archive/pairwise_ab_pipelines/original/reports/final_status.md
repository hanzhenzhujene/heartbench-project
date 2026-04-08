# Final Status Report

## Project: Christian Framing and Heart-Level Moral Attribution

**Date**: 2026-04-07 (updated)

## Important Correction

This report mostly documents the **legacy pairwise A/B pipeline** and should no longer be treated as the canonical conclusion of the project.

The current canonical result is the **bias-resistant casewise-logit rerun**, which removes the raw `A/B` answer-channel artifact that drove the earlier apparent `C2` penalty.

Use these files first:

- [Bias-resistant rerun report](bias_resistant_rerun_report.md)
- [Full corrected HeartBench analysis](../results_casewise_logit/heartbench/main/analysis.json)

### Current Canonical Conclusion

On the corrected full HeartBench-240 benchmark with `Qwen2.5-1.5B-Instruct`:

- `C0` expected accuracy: `0.933`
- `C1` expected accuracy: `0.942`
- `C2` expected accuracy: `0.938`
- `C3` expected accuracy: `0.938`
- `C4` expected accuracy: `0.942`

The paired corrected comparisons are effectively null. The old strong claim that Christian framing hurts heart attribution is **not supported** once the A/B artifact is removed.

The best current interpretation is:

1. No prompt condition shows a robust accuracy advantage on the corrected primary benchmark.
2. `C2` is not meaningfully worse than baseline on corrected scoring.
3. `C2` may be slightly less separating than `C1` or `C4`, but the effect is small.

---

## Architecture Change: Dual Benchmark Hierarchy

This section describes the legacy pairwise A/B benchmark hierarchy that produced the original result tables.

The project now uses two benchmarks:

| Benchmark | Role | Source | Items |
|-----------|------|--------|-------|
| **Moral Stories Subset** | Primary | Emelin et al., 2021 | 240 |
| **HeartBench-240** | Secondary | Custom-constructed | 240 |

**Rationale**: Using an externally sourced, peer-reviewed dataset as the primary benchmark reduces author bias and strengthens the validity of any observed effects. HeartBench-240 provides cross-benchmark validation with tighter construct control.

---

## What is Complete

### 1. Primary Benchmark (Moral Stories Subset)
- [x] 240 pairwise A/B items from Moral Stories (Emelin et al., 2021)
- [x] 6 families x 40 items, stratified selection from 12,000 source items
- [x] Heart-relevance filtering (11,724 candidates from 12,000)
- [x] Family, domain, difficulty, setting, and primary cue classification
- [x] Gold label balance: 120 A / 120 B (exactly 50/50)
- [x] Dev/test split: 60 dev + 180 test (10/30 per family)
- [x] A/B swapped versions for position bias evaluation
- [x] Full traceability (source IDs, norms, intentions preserved)
- [x] JSONL, CSV, and traced formats
- [x] Automated validation (passes all checks, 0 errors)
- [x] Pilot run on 30 dev items, all 5 conditions, both models

### 2. Secondary Benchmark (HeartBench-240)
- [x] 240 pairwise A/B items across 6 families (40 per family)
- [x] 120 adapted + 120 original items
- [x] All required metadata fields
- [x] Gold label balance: 120 A / 120 B
- [x] Dev/test split: 60 dev + 180 test
- [x] A/B swapped versions
- [x] JSONL and CSV formats
- [x] Annotation guide and construction notes
- [x] Automated validation (passes all checks)
- [x] Pilot run on 30 dev items, all 5 conditions, both models

### 3. Prompt Templates
- [x] C0 baseline
- [x] C1 neutral heart-sensitive framing
- [x] C2 Christian heart-focused framing
- [x] C3 scripture-style framing
- [x] C4 secular matched paraphrase
- [x] Repair prompt for malformed JSON output

### 4. Inference Pipeline
- [x] Model loading for both Qwen models (0.5B and 1.5B)
- [x] Deterministic decoding (temperature=0, top_p=1, do_sample=False)
- [x] JSON output parsing with fallback strategies
- [x] JSON repair via multi-turn prompting
- [x] `--benchmark` flag for selecting moral_stories / heartbench / both
- [x] Pilot subset support (--pilot flag)
- [x] A/B swap evaluation support (--swap flag)
- [x] Per-condition and combined result files
- [x] Separate result directories per benchmark

### 5. Scoring and Analysis
- [x] Heart attribution accuracy
- [x] Moral attribution accuracy
- [x] Reason focus distribution
- [x] Surface overweighting rate
- [x] Heart shift gain (relative to baseline)
- [x] Moral-vs-heart dissociation rate
- [x] Per-family accuracy breakdown
- [x] Per-difficulty accuracy breakdown
- [x] Bootstrap 95% confidence intervals
- [x] McNemar tests for all four paired comparisons
- [x] Summary tables
- [x] Dual benchmark scoring and analysis (separate reports per benchmark)

### 6. Pilot Runs
- [x] **Moral Stories pilot**: 30 items from dev set, 5 conditions, 2 models = 300 outputs
- [x] **HeartBench pilot**: 30 items from dev set, 5 conditions, 2 models = 300 outputs
- [x] Raw generations saved for both
- [x] Results parsed and scored for both

### 6b. Full Evaluation Runs
- [x] **Moral Stories 0.5B full**: 240 items x 5 conditions = 1,200 outputs
- [x] **HeartBench 0.5B full**: 240 items x 5 conditions = 1,200 outputs
- [x] **Moral Stories 1.5B full**: 240 items x 5 conditions = 1,200 outputs (100% parse rate)
- [ ] **HeartBench 1.5B full**: In progress

### 7. Documentation
- [x] moral_stories_benchmark_summary.md (primary benchmark)
- [x] benchmark_summary.md (secondary benchmark, updated)
- [x] pilot_report.md (HeartBench pilot)
- [x] final_status.md (this file)
- [x] annotation_guide.md (updated for dual benchmarks)
- [x] construction_notes.md (updated with Moral Stories section)
- [x] README.md (updated with dual benchmark architecture)
- [x] Exploratory analysis notebook (updated)

### 8. Configuration
- [x] models.yaml
- [x] prompts.yaml
- [x] experiment.yaml (updated with dual benchmark paths)
- [x] requirements.txt
- [x] pyproject.toml

---

## Moral Stories Pilot Results

*(Results from 30-item dev set pilot, both models, all 5 conditions)*

### Parse Success Rates

| Model | C0 | C1 | C2 | C3 | C4 |
|-------|----|----|----|----|-----|
| Qwen2.5-0.5B-Instruct | 86.7% | 76.7% | 93.3% | 83.3% | 83.3% |
| Qwen2.5-1.5B-Instruct | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

### Heart Attribution Accuracy

| Model | C0 | C1 | C2 | C3 | C4 |
|-------|----|----|----|----|-----|
| Qwen2.5-0.5B-Instruct | 0.538 | 0.478 | 0.536 | 0.480 | 0.480 |
| Qwen2.5-1.5B-Instruct | 0.633 | 0.533 | 0.567 | 0.633 | 0.533 |

### Key Observations
- 1.5B baseline heart accuracy (0.633) is above chance and higher than HeartBench baseline (0.567)
- C3 (scripture-style) matches baseline for 1.5B; C2 (Christian framing) slightly below baseline
- The 0.5B model shows near-chance performance across all conditions
- Reason focus: baseline outward_act rate is only 6.7% for 1.5B (vs 23.3% on HeartBench), suggesting less room for motive-shift effects

---

## HeartBench Pilot Results (from earlier run)

### Heart Attribution Accuracy

| Model | C0 | C1 | C2 | C3 | C4 |
|-------|----|----|----|----|-----|
| Qwen2.5-0.5B-Instruct | 0.567 | 0.577 | 0.586 | 0.600 | 0.577 |
| Qwen2.5-1.5B-Instruct | 0.567 | 0.600 | 0.533 | 0.600 | 0.467 |

### Reason Focus Shift (1.5B model)
- C0 baseline: 23.3% outward_act
- C2 Christian framing: 0% outward_act
- Directionally consistent with the hypothesis

---

## Full 240-Item Results

### Moral Stories (Primary) — Both Models

#### 0.5B Model

| Condition | Heart Acc | Moral Acc | Parse Rate | Motive% | Outward% |
|-----------|-----------|-----------|------------|---------|----------|
| C0 | 0.487 | 0.513 | 93.3% | 100.0% | 0.0% |
| C1 | 0.488 | 0.512 | 90.4% | 100.0% | 0.0% |
| C2 | 0.487 | 0.513 | 95.8% | 99.6% | 0.4% |
| C3 | 0.483 | 0.517 | 83.8% | 98.5% | 1.5% |
| C4 | 0.482 | 0.518 | 90.8% | 98.6% | 1.4% |

#### 1.5B Model ✅ COMPLETE

| Condition | Heart Acc | Moral Acc | Parse Rate | Motive% | Outward% |
|-----------|-----------|-----------|------------|---------|----------|
| C0 | **0.633** | 0.525 | 100.0% | 92.1% | 7.9% |
| C1 | 0.588 | 0.500 | 100.0% | 99.2% | 0.8% |
| C2 | **0.508** | 0.550 | 100.0% | 99.6% | 0.4% |
| C3 | 0.571 | 0.533 | 100.0% | 82.5% | 17.5% |
| C4 | 0.583 | 0.533 | 100.0% | 100.0% | 0.0% |

#### 1.5B Paired Statistical Tests (n=240)

| Comparison | Heart Shift | Bootstrap 95% CI | McNemar χ² | p-value | Discordant |
|------------|-------------|-------------------|------------|---------|------------|
| C0 vs C1 | −0.046 | [−0.138, +0.054] | 0.75 | 0.386 | 61 vs 72 |
| **C0 vs C2** | **−0.125** | **[−0.183, −0.067]** | **15.02** | **p=0.0001** | **13 vs 43** |
| C2 vs C4 | +0.075 | [−0.046, +0.192] | 1.40 | 0.236 | 112 vs 94 |
| **C2 vs C3** | **+0.062** | **[+0.025, +0.104]** | **8.52** | **p=0.0035** | **19 vs 4** |

### Legacy A/B Observation: Apparent C2 Penalty

Under the legacy pairwise A/B pipeline, the primary hypothesis appeared to be disconfirmed:

1. **C2 significantly reduces heart accuracy** relative to baseline (0.633 → 0.508, Δ=−12.5%, p=0.0001). The CI excludes zero.
2. **C3 (scripture-style) significantly outperforms C2** (0.508 → 0.571, Δ=+6.2%, p=0.0035). The CI excludes zero.
3. C2 nearly collapses reason_focus to 99.6% motive / 0.4% outward — forcing motive-only reasoning does NOT improve accuracy.
4. C3 has the HIGHEST outward_act rate (17.5%) yet better accuracy — suggesting balanced attention may be more diagnostic.
5. C4 (secular matched, 100% motive) is directionally better than C2 (0.583 vs 0.508) but not significant (p=0.236).

#### Per-Family Accuracy (1.5B)

| Family | C0 | C1 | C2 | C3 | C4 |
|--------|-----|-----|-----|-----|-----|
| same_act_different_motive | 0.675 | 0.650 | 0.525 | 0.625 | 0.675 |
| same_restraint_different_posture | 0.675 | 0.550 | 0.525 | 0.575 | 0.550 |
| same_correction_different_heart | 0.600 | 0.575 | 0.500 | 0.500 | 0.550 |
| good_act_corrupt_motive | 0.675 | 0.625 | 0.500 | 0.650 | 0.575 |
| flawed_act_benevolent_motive | 0.675 | 0.600 | 0.500 | 0.600 | 0.625 |
| mixed_motive_hard | 0.500 | 0.525 | 0.500 | 0.475 | 0.525 |

C2 drops **every family** to ~0.50 (chance). The hit is universal, not family-specific.

#### Moral-Heart Dissociation Rate (1.5B)

| Condition | Dissociation (heart ≠ moral) |
|-----------|------------------------------|
| C0 | 73.3% |
| C1 | 20.4% |
| C2 | **89.2%** |
| C3 | 86.3% |
| C4 | 7.5% |

Under C2, the model gives heart_worse and morally_worse answers that **disagree 89.2% of the time**, yet neither answer is accurate. Under C4, they almost always agree (7.5% dissociation) and heart accuracy is higher. This suggests Christian framing makes the model believe heart-worse and morally-worse are different things, but it confuses which direction to split them.

#### ⚠️ Root Cause: Position Bias, Not Heart Reasoning

Deeper analysis reveals the accuracy differences are driven by **position bias** (which letter the model defaults to), not by improved moral reasoning:

| Condition | % answers "A" | % answers "B" |
|-----------|---------------|---------------|
| C0 (baseline) | 75.8% | 24.2% |
| C1 (neutral heart) | — | — |
| C2 (Christian) | **99.2%** | 0.8% |
| C3 (scripture) | 89.6% | 10.4% |
| C4 (secular) | 13.3% | **86.7%** |

Gold labels are exactly 50/50 (120 A / 120 B). Under C2, the model answers "A" on 238/240 items, getting all 120 A-gold items right but missing 118/120 B-gold items → ~50% accuracy mechanistically. C4 shows the mirror image (B-bias).

The 43 discordant pairs (C0 right → C2 wrong) are entirely cases where gold=B but C2 flipped the answer to A. All 43 flips went in the same direction (toward A). This is consistent with position bias, not differential moral reasoning.

**Interpretation**: Different prompt framings induce different **position biases** in the 1.5B model. Christian framing pushes the model to an extreme A-preference; secular framing pushes it to B-preference. The baseline happens to be moderately A-biased, which (by luck of the 50/50 gold split) gives the best accuracy. The statistical significance of the C0-C2 difference (p=0.0001) is real but reflects a **bias shift**, not an improvement or degradation in moral reasoning ability. This would need A/B swap evaluation to fully disentangle.

### HeartBench (Secondary) — 0.5B Full Run

| Condition | Heart Acc | Moral Acc | Parse Rate | Motive% | Outward% |
|-----------|-----------|-----------|------------|---------|----------|
| C0 | 0.506 | 0.494 | 98.8% | 100.0% | 0.0% |
| C1 | 0.519 | 0.481 | 87.5% | 100.0% | 0.0% |
| C2 | 0.513 | 0.487 | 95.8% | 99.6% | 0.4% |
| C3 | 0.522 | 0.478 | 83.8% | 99.5% | 0.5% |
| C4 | 0.516 | 0.484 | 89.6% | 99.5% | 0.0% |

*(HeartBench 1.5B full run in progress — will update when complete)*

### 0.5B Model: Total A-Position Bias, Zero Sensitivity

The 0.5B model answers **"A" on 100% of items** across all conditions on Moral Stories. With 50/50 gold labels, this mechanistically produces ~49-50% accuracy. The zero discordant pairs in all McNemar tests arise because the model gives the exact same answer ("A") regardless of framing. The 0.5B model has no discriminative ability and no framing sensitivity whatsoever.

### 1.5B Position Bias Varies by Condition (Full Summary)

| Condition | % answers "A" | Acc\|gold=A | Acc\|gold=B | Overall |
|-----------|---------------|-------------|-------------|---------|
| C0 | 75.8% | 89.2% | 37.5% | 0.633 |
| C1 | 20.4% | 29.2% | 88.3% | 0.588 |
| C2 | **99.2%** | **100%** | **1.7%** | 0.508 |
| C3 | 89.6% | 96.7% | 17.5% | 0.571 |
| C4 | 13.3% | 21.7% | 95.0% | 0.583 |

C0 is A-biased, C1/C4 are B-biased, C2/C3 are extremely A-biased. Since gold labels are 50/50, the conditions that have more moderate bias (C0, C4, C1) achieve higher accuracy, while C2's extreme A-bias pushes it to chance.

**However**, even after accounting for position bias, conditions differ in discrimination ability: C0 achieves 0.633 (13.3 pp above chance), while C2 achieves only 0.508 (0.8 pp above chance). This means C2 doesn't just shift position bias — it **eliminates the model's ability to distinguish heart-worse from heart-better cases**. A/B swap evaluation would provide definitive evidence.

---

## What is Incomplete

### HeartBench 1.5B full run
Currently executing (~6s/item, ~2 hours remaining). Will provide cross-benchmark validation of whether the C2 accuracy-reduction and position bias effects replicate.

### A/B swap evaluation
Swapped benchmarks are generated for both datasets. Swap runs for C0 and C2 will be executed after HeartBench 1.5B completes. This is the **critical test**: if C2's extreme A-bias reverses to B-bias under A/B swap, it confirms position bias as the mechanism. If accuracy also drops in the swapped version, it confirms C2 truly degrades discrimination.

### Mixed-effects regression
Not implemented. Core McNemar and bootstrap analyses are in place.

---

## Exact Commands to Reproduce

```bash
# 1. Install dependencies
pip3 install torch transformers pyyaml pandas numpy scipy scikit-learn tqdm

# 2. Build benchmarks
python3 src/build_benchmark.py              # HeartBench-240
python3 src/build_moral_stories_subset.py   # Moral Stories subset

# 3. Validate benchmarks
python3 src/validate_benchmark.py --benchmark benchmark/moral_stories_subset.jsonl
python3 src/validate_benchmark.py --benchmark benchmark/heartbench_240.jsonl

# 4. Generate A/B swapped versions
python3 src/ab_swap.py

# 5. Run Moral Stories pilot
python3 src/run_inference.py --benchmark moral_stories --pilot --pilot-n 30 \
    --models "Qwen/Qwen2.5-0.5B-Instruct" --conditions C0 C1 C2 C3 C4
python3 src/run_inference.py --benchmark moral_stories --pilot --pilot-n 30 \
    --models "Qwen/Qwen2.5-1.5B-Instruct" --conditions C0 C1 C2 C3 C4

# 6. Combine results
python3 -c "
import json
from pathlib import Path
pilot_dir = Path('results/moral_stories/pilot')
all_results = []
for f in sorted(pilot_dir.glob('Qwen2.5-*_C*.jsonl')):
    with open(f) as fh:
        for line in fh:
            all_results.append(json.loads(line.strip()))
with open(pilot_dir / 'all_results.jsonl', 'w') as fh:
    for r in all_results:
        fh.write(json.dumps(r, ensure_ascii=False) + '\n')
print(f'Combined {len(all_results)} results')
"

# 7. Score and analyze
python3 src/score_results.py
python3 src/analyze_results.py
```

---

## Files to Inspect First

| File | Purpose |
|------|---------|
| `benchmark/moral_stories_subset.jsonl` | Primary: 240 Moral Stories items |
| `benchmark/heartbench_240.jsonl` | Secondary: 240 custom items |
| `results/moral_stories/pilot/all_results.jsonl` | Moral Stories pilot outputs |
| `results/pilot/all_results.jsonl` | HeartBench pilot outputs |
| `src/run_inference.py` | Inference pipeline (--benchmark flag) |
| `src/score_results.py` | Scoring logic (dual benchmark) |
| `src/analyze_results.py` | Statistical tests (dual benchmark) |
| `configs/experiment.yaml` | Dual benchmark configuration |

---

## Research Intent and Emerging Findings

This project tests whether Christian heart-focused framing changes **what small language models treat as morally diagnostic**. The dual-benchmark design strengthens the research:

- **Moral Stories (primary)**: Externally sourced items with independent norm validation
- **HeartBench (secondary)**: Custom items with tighter construct control

### Emerging Conclusion (Moral Stories, 1.5B, n=240)

The primary hypothesis is **disconfirmed**. Christian heart-focused framing (C2) does not improve heart-level moral attribution — it significantly degrades it (p=0.0001). The mechanism is primarily **position bias**: C2 pushes the model to answer "A" 99.2% of the time, while the baseline allows more balanced responding (75.8% A).

More importantly, C2 appears to eliminate the model's discriminative ability entirely (balanced accuracy = 0.508, near chance), whereas the baseline retains meaningful discrimination (balanced accuracy = 0.633). Scripture-style framing (C3) partially preserves discrimination while showing the highest outward_act reasoning rate (17.5%).

The analysis is centered on **inward motive vs outward action attribution**, not on generic moral judgment accuracy. The position bias finding adds a critical methodological insight: prompt framing effects in small LLMs may operate primarily through position preference shifts rather than through genuine reasoning changes. A/B swap evaluation is needed to fully confirm this.
