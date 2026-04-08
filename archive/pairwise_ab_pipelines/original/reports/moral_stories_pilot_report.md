# Moral Stories Subset Pilot Report

## Pilot Setup

- **Benchmark**: Moral Stories subset (primary), 30 items from dev set
- **Models**: Qwen2.5-0.5B-Instruct, Qwen2.5-1.5B-Instruct
- **Conditions**: C0 (baseline), C1 (neutral heart-sensitive), C2 (Christian heart-focused), C3 (scripture-style), C4 (secular matched)
- **Decoding**: temperature=0, top_p=1, do_sample=False, max_new_tokens=128
- **Total outputs**: 300 (2 models x 5 conditions x 30 items)

## Parse Success Rates

| Model | C0 | C1 | C2 | C3 | C4 |
|-------|----|----|----|----|-----|
| Qwen2.5-0.5B-Instruct | 86.7% | 76.7% | 93.3% | 83.3% | 83.3% |
| Qwen2.5-1.5B-Instruct | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

**Observation**: The 1.5B model achieves 100% parse success across all conditions — identical to HeartBench. The 0.5B model has lower parse rates (76.7-93.3%), consistent with the longer Moral Stories case texts (avg 31 vs 22 words).

## Heart Attribution Accuracy

| Model | C0 | C1 | C2 | C3 | C4 |
|-------|----|----|----|----|-----|
| Qwen2.5-0.5B-Instruct | 0.538 | 0.478 | 0.536 | 0.480 | 0.480 |
| Qwen2.5-1.5B-Instruct | 0.633 | 0.533 | 0.567 | 0.633 | 0.533 |

**Key observations**:
- 1.5B baseline (0.633) is higher than on HeartBench (0.567), suggesting Moral Stories items may be slightly easier for larger models
- For the 1.5B model: C3 (scripture-style) matches baseline at 0.633, while C1, C2, C4 all drop below
- The 0.5B model shows near-chance performance across all conditions
- C2 (Christian framing) does not improve over baseline for either model on Moral Stories

## Moral Attribution Accuracy

| Model | C0 | C1 | C2 | C3 | C4 |
|-------|----|----|----|----|-----|
| Qwen2.5-0.5B-Instruct | 0.462 | 0.522 | 0.464 | 0.520 | 0.520 |
| Qwen2.5-1.5B-Instruct | 0.467 | 0.433 | 0.467 | 0.467 | 0.500 |

## Reason Focus Distribution

| Model | C0 motive% | C0 outward% | C2 motive% | C2 outward% | C3 motive% | C3 outward% |
|-------|-----------|------------|-----------|------------|-----------|------------|
| Qwen2.5-0.5B-Instruct | 100% | 0% | 100% | 0% | 96% | 4% |
| Qwen2.5-1.5B-Instruct | 93.3% | 6.7% | 96.7% | 3.3% | 83.3% | 16.7% |

**Key finding**: Unlike HeartBench where the 1.5B model showed a clear shift from outward_act to motive under framing, the Moral Stories pattern is different:
- Baseline outward_act rate is only 6.7% (vs 23.3% on HeartBench)
- C3 (scripture-style) actually *increases* outward_act to 16.7%, an unexpected reversal

This suggests Moral Stories items may already elicit motive-focused reasoning at baseline, leaving less room for framing to shift attention.

## Comparison with HeartBench Pilot

| Metric | Moral Stories (1.5B) | HeartBench (1.5B) |
|--------|---------------------|-------------------|
| Baseline heart acc | 0.633 | 0.567 |
| C2 heart acc | 0.567 | 0.533 |
| C3 heart acc | 0.633 | 0.600 |
| Parse rate (all) | 100% | 100% |
| Baseline outward% | 6.7% | 23.3% |
| C2 outward% | 3.3% | 0% |

## Paired Statistical Analysis (1.5B model)

| Comparison | Heart Shift | Bootstrap CI | McNemar p |
|------------|-------------|-------------|-----------|
| C0 vs C1 | -0.100 | [-0.367, +0.200] | 0.628 |
| C0 vs C2 | -0.067 | [-0.233, +0.067] | 0.683 |
| C2 vs C4 | -0.033 | [-0.367, +0.333] | 1.000 |
| C2 vs C3 | +0.067 | [+0.000, +0.167] | 0.480 |

No comparisons are statistically significant at n=30. The C2 vs C3 comparison shows a directional trend (+0.067, 2 discordant pairs favoring C3).

## Recommendations for Full Run

1. Run full 240-item evaluation for statistical power
2. Focus analysis on the 1.5B model, which showed more sensitivity on HeartBench
3. Cross-benchmark comparison: items where framing helps on one benchmark but not the other
4. A/B swap evaluation to check position bias

## Reproduction Commands

```bash
# Run pilot (both models, all conditions, 30 items from dev)
python3 src/run_inference.py --benchmark moral_stories --pilot --pilot-n 30 \
    --models "Qwen/Qwen2.5-0.5B-Instruct" --conditions C0 C1 C2 C3 C4
python3 src/run_inference.py --benchmark moral_stories --pilot --pilot-n 30 \
    --models "Qwen/Qwen2.5-1.5B-Instruct" --conditions C0 C1 C2 C3 C4

# Combine results
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

# Score and analyze
python3 src/score_results.py
python3 src/analyze_results.py
```
