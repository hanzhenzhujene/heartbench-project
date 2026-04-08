# HeartBench Pilot Report

## Pilot Setup

- **Items**: 30 (from dev set, 5 per family)
- **Models**: Qwen2.5-0.5B-Instruct, Qwen2.5-1.5B-Instruct
- **Conditions**: C0 (baseline), C1 (neutral heart-sensitive), C2 (Christian heart-focused), C3 (scripture-style), C4 (secular matched)
- **Decoding**: temperature=0, top_p=1, do_sample=False, max_new_tokens=128
- **Total outputs**: 300 (2 models x 5 conditions x 30 items)

## Parse Success Rates

| Model | C0 | C1 | C2 | C3 | C4 |
|-------|----|----|----|----|-----|
| Qwen2.5-0.5B-Instruct | 100.0% | 86.7% | 96.7% | 83.3% | 86.7% |
| Qwen2.5-1.5B-Instruct | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

**Observation**: The 0.5B model has parse failures on C1, C3, and C4 (14-17% failure rate). The 1.5B model achieves 100% parse success across all conditions. The 0.5B model struggles more with structured JSON output when framing text is added.

## Heart Attribution Accuracy

| Model | C0 | C1 | C2 | C3 | C4 |
|-------|----|----|----|----|-----|
| Qwen2.5-0.5B-Instruct | 0.567 | 0.577 | 0.586 | 0.600 | 0.577 |
| Qwen2.5-1.5B-Instruct | 0.567 | 0.600 | 0.533 | 0.600 | 0.467 |

**Key observations**:
- Baseline accuracy is ~0.567 for both models, slightly above chance (0.50)
- For the 0.5B model, all framing conditions slightly improve over baseline (up to +0.033)
- For the 1.5B model, results are mixed: C1 and C3 improve (+0.033), C2 drops slightly (-0.033), and C4 drops (-0.100)
- The small sample (n=30 per condition) means these differences are not statistically significant

## Moral Attribution Accuracy

| Model | C0 | C1 | C2 | C3 | C4 |
|-------|----|----|----|----|-----|
| Qwen2.5-0.5B-Instruct | 0.433 | 0.423 | 0.414 | 0.400 | 0.423 |
| Qwen2.5-1.5B-Instruct | 0.467 | 0.433 | 0.533 | 0.467 | 0.533 |

**Note**: Moral accuracy is below 0.50 for most 0.5B conditions and around 0.47-0.53 for 1.5B. The 0.5B model appears to largely give the same answer for heart_worse and morally_worse (dissociation is low).

## Reason Focus Distribution

| Model | C0 motive% | C0 outward% | C2 motive% | C2 outward% |
|-------|-----------|------------|-----------|------------|
| Qwen2.5-0.5B-Instruct | 100% | 0% | 100% | 0% |
| Qwen2.5-1.5B-Instruct | 76.7% | 23.3% | 100% | 0% |

**Key finding**: The 1.5B model shows an interesting pattern: at baseline (C0), 23.3% of reason_focus responses cite outward_act. Under all heart-sensitive framing conditions (C1-C4), the outward_act rate drops to 0-10%. This is consistent with the hypothesis that framing shifts attention away from outward action.

The 0.5B model shows 100% motive across all conditions, which may reflect a tendency to always select "motive" regardless of actual reasoning.

## Paired Statistical Analysis (1.5B model)

| Comparison | Heart Shift | Bootstrap CI | McNemar p |
|------------|-------------|-------------|-----------|
| C0 vs C1 | +0.033 | [-0.233, +0.300] | 1.000 |
| C0 vs C2 | -0.033 | [-0.100, +0.000] | 1.000 |
| C2 vs C4 | -0.067 | [-0.400, +0.267] | 0.838 |
| C2 vs C3 | +0.067 | [+0.000, +0.167] | 0.480 |

No comparisons are statistically significant at this pilot sample size. The confidence intervals are wide, reflecting the small n=30.

## Notable Pilot Findings

1. **Parse reliability**: The 1.5B model is much more reliable for JSON output (100% vs ~87-100% for 0.5B). For production runs, the 0.5B model may need lower max_new_tokens or alternative prompting strategies.

2. **Reason focus shift**: The most interpretable signal in this pilot is the 1.5B model's shift from outward_act to motive under heart-focused framing. This is directionally consistent with the research hypothesis.

3. **Small effect sizes**: Heart accuracy differences across conditions are small (within ~0.07 points). The full 240-item benchmark and repeated runs will be needed to detect reliable effects.

4. **Heart vs moral dissociation**: The 1.5B model shows more dissociation between heart_worse and morally_worse judgments under C2 and C4. This is worth investigating in the full run.

## Recommendations for Full Run

1. Run the full 240-item benchmark for higher statistical power
2. Consider lowering max_new_tokens for the 0.5B model to reduce verbose outputs
3. Run A/B swapped evaluation to check for position bias
4. Focus error analysis on items where C0 is wrong but C2/C3 are correct (the key hypothesis test)

## Reproduction Commands

```bash
# Rebuild benchmark
python3 src/build_benchmark.py

# Run pilot (both models, all conditions, 30 items from dev)
python3 src/run_inference.py --pilot --pilot-n 30

# Score results
python3 src/score_results.py

# Run analysis
python3 src/analyze_results.py
```
