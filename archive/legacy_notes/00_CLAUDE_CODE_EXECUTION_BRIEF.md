# Claude Code Execution Brief

## Objective

Execute a compact but rigorous research pipeline for the project:

**Christian Framing and Heart-Level Moral Attribution**

The core goal is to test whether Christian heart-focused framing changes what small language models treat as morally diagnostic, especially in cases where outward action and inward motive diverge.

This project should be implemented using:

- `Qwen2.5-0.5B-Instruct`
- `Qwen2.5-1.5B-Instruct`

The work should be organized so that it is reproducible, easy to audit, and easy to extend.

---

## High-level research question

Does Christian heart-focused framing make small LLMs attend more to inward motive and inward moral orientation, rather than overweighting outward behavioral surface?

This project is **not** about proving that Christian framing makes the model generally more moral.
It is about testing whether Christian framing changes **moral attention allocation**.

More specifically:

- does the model become more sensitive to inward motive?
- does it reduce outward-surface overweighting?
- does it distinguish heart-level corruption from socially positive outward action?
- does it distinguish inward integrity from socially rough or imperfect outward behavior?

---

## What Claude Code should build

You should build the following components.

### 1. Benchmark package

Implement a benchmark called `HeartBench-240`.

The benchmark should contain 240 pairwise A/B moral-comparison items with metadata, gold labels, and benchmark splits.

Required benchmark components:

- item schema
- storage format (`jsonl` preferred)
- writer/reviewer/adjudication workflow support
- A/B swap support
- split files for dev and test

The benchmark must follow the taxonomy and controls described in:

- `03_HEARTBENCH_240_CONSTRUCTION_PROTOCOL.md`

### 2. Prompt package

Implement all framing conditions from:

- `02_PROMPT_SHEET.md`

At minimum, implement:

- C0 baseline
- C1 neutral heart-sensitive framing
- C2 Christian heart-focused framing
- C3 scripture-style framing
- C4 secular matched paraphrase

All prompts should use the same structured output format.

### 3. Model runner

Build an inference pipeline for:

- `Qwen2.5-0.5B-Instruct`
- `Qwen2.5-1.5B-Instruct`

The runner should:

- use deterministic decoding
- support batched evaluation if possible
- parse JSON outputs robustly
- retry formatting repair when needed
- log raw generations and parsed outputs separately

### 4. Evaluation and analysis

Implement scoring for:

- heart attribution accuracy
- moral attribution accuracy
- surface overweighting rate
- heart shift gain relative to baseline
- moral-vs-heart dissociation
- reason-focus distribution

Implement paired statistical analysis where appropriate.

At minimum:

- McNemar tests for paired binary comparisons
- bootstrap confidence intervals for accuracy differences

Optional but preferred:

- mixed-effects logistic regression over item-level outcomes

### 5. Reporting

Produce:

- condition-by-model summary tables
- per-family results
- per-difficulty results
- reason-focus distributions
- error buckets
- selected qualitative examples

---

## Working principles

### Principle 1. Keep the benchmark construct-clean

The benchmark should test **heart-level attribution**, not generic moral judgment.

Avoid drift into:

- generic acceptability classification
- sentimental writing
- overtly theological item wording
- outcome-dominated reasoning

### Principle 2. Keep the intervention short and interpretable

Do not use long passages.
Do not use large scripture injections.
Use compact framing prompts only.

### Principle 3. Prioritize controlled contrasts over story richness

This project succeeds if the benchmark isolates the contrast:

- outward action
nvs
- inward motive / inward orientation

### Principle 4. Use paired comparisons everywhere possible

Same item, multiple prompt conditions.
Same item, both model sizes.
Same item, A/B swap support.

---

## Recommended repo layout

Use a structure close to this:

```text
heartbench_project/
  README.md
  data/
    raw/
    processed/
    benchmark/
      heartbench_240.jsonl
      dev.jsonl
      test.jsonl
      annotation_guidelines.md
  prompts/
    c0_baseline.txt
    c1_neutral_heart.txt
    c2_christian_heart.txt
    c3_scripture_style.txt
    c4_secular_matched.txt
    repair_prompt.txt
  src/
    build_benchmark.py
    validate_benchmark.py
    run_inference.py
    parse_outputs.py
    score_results.py
    stats_analysis.py
    error_analysis.py
    utils.py
  outputs/
    raw_generations/
    parsed_outputs/
    scores/
    figures/
    tables/
  reports/
    main_results.md
    error_analysis.md
```

---

## Concrete execution stages

### Stage 1. Implement benchmark schema and validators

Create a canonical schema for each item with fields such as:

- `item_id`
- `family`
- `source_type`
- `setting_type`
- `domain`
- `difficulty`
- `case_A`
- `case_B`
- `gold_heart_worse`
- `gold_morally_worse`
- `gold_primary_cue`
- `notes`

Add validation scripts to check:

- field completeness
- label validity
- family counts
- A/B balance
- case-length balance
- split integrity

### Stage 2. Build benchmark drafting workflow

Implement a drafting and review workflow that supports:

- initial draft items
- reviewer labels
- adjudication
- benchmark freeze status

The benchmark construction should follow the protocol exactly.

### Stage 3. Implement prompt conditions

Create template files and a prompt-rendering function that takes:

- framing condition
- case A text
- case B text

and emits a fully formatted prompt.

### Stage 4. Implement inference runner

Use deterministic decoding with:

- `temperature=0`
- `top_p=1`
- `do_sample=False`
- low `max_new_tokens`

Save:

- raw text output
- parsed JSON output
- parse success / failure
- repaired output if a repair pass is used

### Stage 5. Implement scoring

Main score:

- `heart_worse` accuracy

Secondary scores:

- `morally_worse` accuracy
- `reason_focus` distribution
- family-specific heart accuracy
- difficulty-specific heart accuracy
- surface overweighting rate
- dissociation rate between heart judgment and moral-overall judgment

### Stage 6. Implement robustness checks

Add support for:

- A/B order swap
- no-rationale subset
- lexical balance checks
- family-level balance checks
- wording-length checks

### Stage 7. Produce final report

The final report should clearly answer:

1. does Christian heart-focused framing improve heart-level attribution over baseline?
2. does it outperform neutral heart-sensitive framing?
3. does it outperform secular matched paraphrase?
4. is the effect concentrated in specific item families?
5. does it increase motive-focused reasoning rather than surface-only reasoning?

---

## Main hypotheses to preserve

### H1
Compared with baseline, heart-sensitive framing should improve heart attribution accuracy on cases where outward action and inward motive diverge.

### H2
Christian heart-focused framing should especially help on:

- same outward act, different motive
- outwardly compliant, inwardly corrupt
- outwardly harsh, inwardly benevolent vs malicious

### H3
If Christian framing beats secular matched paraphrase, that suggests a framing effect beyond generic semantic clarification.

### H4
If Christian framing and secular matched paraphrase are similar, then the effect is likely semantic attentional repair rather than religious authority per se.

---

## Success criteria

The project is successful if it produces:

- a clean HeartBench-240 benchmark
- stable outputs from both Qwen models
- interpretable results across framing conditions
- robust item-level analysis
- enough error analysis to support a paper-quality discussion

The project is **not** successful if it only produces aggregate accuracy without construct-specific interpretation.

---

## Important constraints

- keep prompts short
- do not contaminate the benchmark items with overt theological vocabulary
- do not let outcome dominate item logic
- do not overfit prompt wording on the full benchmark
- use dev/test separation
- preserve strict pairing and metadata cleanliness

---

## What to read next

After this brief, read:

1. `01_EXPERIMENT_BLUEPRINT.md`
2. `02_PROMPT_SHEET.md`
3. `03_HEARTBENCH_240_CONSTRUCTION_PROTOCOL.md`

Then implement the project.
