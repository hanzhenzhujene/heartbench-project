# Experiment Blueprint
## Christian Framing and Heart-Level Moral Attribution

## 1. Core research question

Does Christian heart-focused framing make small LLMs attend more to inward motive and disposition, rather than overweighting outward action?

More specifically, this project asks whether Christian framing changes what the model treats as morally diagnostic.

The project does **not** ask whether Christian framing makes the model generally more moral.
The core target is **heart-level moral attribution**.

---

## 2. Main claim

The main claim to test is:

**Christian heart-focused framing increases sensitivity to inward moral orientation in cases where outward action and inner motive come apart.**

A more operational version:

Christian framing may shift the model from relying on outward behavioral surface toward attending to motive, intention, and inward orientation.

---

## 3. Model setup

Use the following models:

- `Qwen2.5-0.5B-Instruct`
- `Qwen2.5-1.5B-Instruct`

### Inference settings

Use deterministic decoding:

- `temperature = 0`
- `top_p = 1`
- `do_sample = false`
- `max_new_tokens = 32`
- fixed random seed where relevant

Use the same generation settings across all conditions.

### Output format

Force structured JSON output with exactly these keys:

- `heart_worse`
- `morally_worse`
- `reason_focus`

Example:

```json
{
  "heart_worse": "A",
  "morally_worse": "A",
  "reason_focus": "motive"
}
```

---

## 4. Benchmark design

Use a two-part benchmark.

### Part A. Adapted moral-story subset
- 120 items
- adapted into pairwise A/B comparison format
- intention-sensitive and heart-sensitive cases only

### Part B. Original HeartBench items
- 120 items
- written from scratch
- targeted to contrasts poorly covered by generic moral benchmarks

### Total
- 240 items

The benchmark must follow the construction rules in:
- `03_HEARTBENCH_240_CONSTRUCTION_PROTOCOL.md`

---

## 5. Item format

Each item should present two cases:

- Case A
- Case B

For each item, the model answers:

1. which case reveals a worse inward moral orientation?
2. which case is more morally problematic overall?
3. what feature best explains the choice?

### Why pairwise format

Pairwise A/B format is preferred because:

- it is more stable for small models
- it reduces generation noise
- it makes the construct more controlled
- it supports direct contrastive evaluation

---

## 6. Prompt conditions

Implement the following five conditions.

### C0. Baseline
No added framing.

### C1. Neutral heart-sensitive framing
Explicitly instruct the model to consider motive, intention, and inward orientation.

### C2. Christian heart-focused framing
Short Christian moral framing emphasizing the heart, motive, and inward orientation.

### C3. Scripture-style framing
Short scripture-style language emphasizing what proceeds from the heart.

### C4. Secular matched paraphrase
A secular paraphrase matched in semantic content to the Christian framing.

Prompt wording should come from:
- `02_PROMPT_SHEET.md`

---

## 7. Main hypotheses

### H1
Compared with baseline, heart-sensitive framing will improve heart attribution accuracy on conflict cases.

### H2
Christian heart-focused framing will improve performance especially on cases where outward act and inward motive diverge.

### H3
If Christian framing outperforms secular matched paraphrase, the effect may extend beyond semantic clarification.

### H4
If Christian framing and secular matched paraphrase perform similarly, the effect is likely semantic attentional repair rather than distinct religious authority.

---

## 8. Main dependent variables

## Primary metric
### Heart Attribution Accuracy
Whether the model correctly identifies which case reveals the worse inward moral orientation.

This is the main metric.

---

## Secondary metrics

### 1. Moral Attribution Accuracy
Accuracy on `morally_worse`.

### 2. Surface Overweighting Rate
For items where outward action is matched but motive differs, measure the rate at which the model fails to track the motive contrast.

### 3. Heart Shift Gain
Difference in heart attribution accuracy between a framing condition and baseline.

### 4. Moral-vs-Heart Dissociation
Rate at which the model gives the same answer to `heart_worse` and `morally_worse` in cases where the benchmark is designed to separate them.

### 5. Reason-Focus Distribution
Distribution over:

- `outward_act`
- `motive`
- `consequence`
- `rule`
- `unclear`

Desired interpretive effect:
Christian heart-focused framing should increase motive-focused selections and reduce outward-surface selections.

---

## 9. Gold labeling protocol

Each item must have:

- primary label: `heart_worse`
- secondary label: `morally_worse`
- primary intended cue label

### Annotation workflow

1. writer draft label
2. blind independent reviewer label
3. adjudication if needed

Only include items that become stable after revision.

---

## 10. Statistical analysis plan

### Main paired comparisons
For each model, compare:

- C0 vs C1
- C0 vs C2
- C2 vs C4
- C2 vs C3

### Statistical tests

#### Paired item-level binary comparisons
Use McNemar’s test.

#### Confidence intervals
Use bootstrap 95% confidence intervals for score differences.

#### Optional fuller model
Mixed-effects logistic regression:

```text
correct ~ condition + model_size + item_type + condition:model_size + (1 | item_id)
```

This supports analysis of:

- model-size sensitivity to framing
- which item families are most affected

---

## 11. Robustness checks

### R1. A/B order swap
Support swapping case order to control position bias.

### R2. Lexical neutralization
Reduce strong moral-valence cue words.

### R3. Style matching
Keep Christian and secular framing similar in length and abstraction level.

### R4. No-rationale subset
Run a subset without the `reason_focus` question to test whether explanation solicitation changes judgments.

### R5. Surface-harshness check
Check whether Christian framing merely makes the model harsher on overall moral judgment rather than more accurate on heart attribution.

---

## 12. Experimental phases

### Phase 1. Pilot
- 30 items
- all 5 conditions
- both models
- verify prompt stability and parse reliability

### Phase 2. Main run
- full 240 items
- all 5 conditions
- both models

Total model judgments:

- `240 x 5 x 2 = 2400`

### Phase 3. Error analysis
Inspect at least these buckets:

- baseline wrong, Christian right
- baseline right, Christian wrong
- Christian and secular paraphrase both right
- scripture-only effective, paraphrase ineffective

---

## 13. What results would be interesting

### Best-case result
Christian heart-focused framing improves heart attribution accuracy on same-act-different-motive items and outwardly-compliant-but-inwardly-corrupt items, while increasing `motive` as the selected reason focus.

This supports:

**Christian framing shifts moral attention from behavioral surface to inward orientation.**

### Also useful result
Christian framing and secular matched paraphrase perform similarly.

This supports:

**The main effect is semantic reorientation toward inward motive rather than uniquely religious authority.**

### Failure-but-informative result
Christian framing increases harshness on `morally_worse` without improving `heart_worse`.

This supports:

**Religious framing may increase moral seriousness without improving heart-level discrimination.**

---

## 14. What not to do

- do not use long scripture injections
- do not rely only on overall accuracy
- do not make `morally_worse` the primary target
- do not use open-ended essay-style output as the main evaluation mode
- do not contaminate benchmark items with overt theological vocabulary

---

## 15. One-sentence contribution

A good final contribution statement is:

**We show that Christian heart-focused framing does not simply change moral answers; it changes what small language models treat as morally diagnostic, selectively increasing attention to inward motive over outward action.**
