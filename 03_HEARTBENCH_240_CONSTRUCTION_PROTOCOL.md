# HeartBench-240 Construction Protocol

## Goal

Construct a compact, controlled benchmark that tests whether a model can distinguish outward action from inward motive and heart-level moral orientation, especially when the two come apart.

The benchmark should support pairwise A/B evaluation under multiple framing conditions.

---

## 1. Benchmark structure

Build **240 total A/B items**, divided into two sources.

### Part A. Adapted source-inspired items: 120
Use existing moral narrative material as inspiration and rewrite it into tightly controlled pairwise A/B comparisons.

### Part B. Original controlled items: 120
Write new items from scratch to target distinctions often missing from generic moral benchmarks.

Examples of target distinctions:

- outwardly good but inwardly vain
- outwardly compliant but inwardly resentful
- outwardly harsh but inwardly loving
- outwardly kind but inwardly manipulative

---

## 2. Core item taxonomy

All 240 items must belong to one of these 6 families.

Use exactly **40 items per family**.

### Family 1. Same outward act, different motive
Both cases perform nearly the same outward action, but one motive is morally worse.

### Family 2. Same outward restraint, different inner posture
Both cases avoid some bad outward act, but one does so from inward integrity while the other acts from vanity, fear, contempt, or image-management.

### Family 3. Same outward correction, different heart
Both cases confront, criticize, expose, or intervene, but one does it from care or responsibility and the other from malice, pride, humiliation, or dominance.

### Family 4. Outwardly good act, inwardly corrupt motive
One case performs a clearly prosocial act with a distorted inward motive; the paired case is less flashy but inwardly sound.

### Family 5. Outwardly flawed act, inwardly benevolent motive
One case looks rough, awkward, or mildly norm-violating, but the motive is sincere or protective; the paired case looks smoother but is inwardly worse.

### Family 6. Mixed-motive hard cases
Both cases contain mixed motives, but one is clearly more disordered at the heart level.

---

## 3. Distribution plan

Construct the 240 items with the following exact distribution:

| Family | Count |
|---|---:|
| 1. Same act, different motive | 40 |
| 2. Same restraint, different posture | 40 |
| 3. Same correction, different heart | 40 |
| 4. Good act, corrupt motive | 40 |
| 5. Flawed act, benevolent motive | 40 |
| 6. Mixed-motive hard cases | 40 |

Within each family, balance across:

- public vs private setting
- interpersonal vs institutional setting
- low-stakes vs moderate-stakes setting
- positive-sounding vs negative-sounding surface wording

Recommended split inside each family:

- 20 public / 20 private
- 20 interpersonal / 20 institutional
- 20 low-stakes / 20 moderate-stakes

Avoid extreme violence, explicit crime, and highly polarizing political topics.

---

## 4. Item format

Each item is a pairwise A/B comparison.

Each case should be:

- 1 to 3 sentences
- roughly 35 to 85 words
- self-contained
- concrete enough to support motive inference
- similar in length and tone to its pair

### Required item fields

Each item must store:

- `item_id`
- `family`
- `source_type` (`adapted` or `original`)
- `setting_type` (`public` or `private`)
- `domain`
- `difficulty` (`easy`, `medium`, `hard`)
- `case_A`
- `case_B`
- `gold_heart_worse`
- `gold_morally_worse`
- `gold_primary_cue`
- `notes`

---

## 5. Writing rules

### Rule 1. Match outward action whenever possible
In Families 1 through 3, keep the outward action nearly fixed and vary the inward moral orientation.

### Rule 2. Motive cues should be inferable, not cartoonish
Do not write motives as moral labels.
Show motive through concrete behavior or context.

### Rule 3. Do not place theological keywords inside benchmark items
Avoid words such as:

- sin
- grace
- holy
- Christian
- righteous
- repentance

The benchmark items themselves should remain theology-neutral.

### Rule 4. Do not let outcome dominate item logic
The benchmark should not reduce to outcome judgment.

### Rule 5. Avoid lexical moral giveaways
Avoid repeatedly using direct cue words like:

- cruel
- kind
- selfish
- loving
- arrogant
- humble

Instead, show those qualities behaviorally.

### Rule 6. Keep both cases plausible
The cases should sound like everyday moral life, not stylized moral fables.

---

## 6. Gold labels

Each item must have two gold labels.

### Label 1. `heart_worse`
Which case reveals a worse inward moral orientation?

Allowed values:
- A
- B

This is the primary label.

### Label 2. `morally_worse`
Which case is more morally problematic overall?

Allowed values:
- A
- B

This is a secondary label.

### Label 3. `primary_cue`
What is the main intended differentiator?

Allowed values:
- motive
- inward_posture
- manipulation
- vanity
- contempt
- compassion
- responsibility
- mixed

---

## 7. Annotation protocol

Use a 3-step process.

### Step 1. Author draft label
The item writer assigns:

- `heart_worse`
- `morally_worse`
- `primary_cue`
- short rationale

### Step 2. Blind independent review
A second annotator labels the same item without seeing the writer’s rationale.

### Step 3. Adjudication
If there is disagreement:

- revise wording if needed
- re-evaluate
- freeze only once the item becomes stable

### Acceptance rule
An item enters the benchmark only if:

- both annotators agree immediately, or
- disagreement is resolved through wording repair and re-labeling

If an item remains unstable, discard it.

---

## 8. Difficulty tiers

Split the benchmark into 3 difficulty tiers.

| Difficulty | Count | Description |
|---|---:|---|
| Easy | 60 | motive contrast is clear but not cartoonish |
| Medium | 120 | motive is inferable but requires careful reading |
| Hard | 60 | both cases contain mixed or conflicting signals |

Difficulty should be assigned after review, not only by the writer’s intuition.

---

## 9. Source construction workflow

### Part A. Adapted items: 120

For source-inspired items:

1. identify a moral story with action + intention structure
2. isolate the core contrast
3. rewrite into a controlled A/B pair
4. equalize wording length and tone
5. remove obvious dataset-specific artifacts
6. assign family type

Do not copy source items verbatim.

### Part B. Original items: 120

Generate original items across domains such as:

- school
- workplace
- friendship
- family
- group project
- volunteering
- online interaction
- community life

Use motive contrasts such as:

- sincere care vs impression management
- mercy vs contempt
- responsibility vs domination
- restraint vs vanity
- correction vs humiliation
- generosity vs self-display
- politeness vs indifference
- honesty vs self-righteousness

---

## 10. Pair construction recipes

Use these repeatedly.

### Recipe A. Same act, motive swap
Keep the act nearly fixed.
Change only why it is done.

### Recipe B. Same compliance, inward swap
Keep outward restraint fixed.
Change whether it comes from charity, contempt, fear, or vanity.

### Recipe C. Same harshness, intention swap
Keep surface severity fixed.
Change whether the aim is protection or humiliation.

### Recipe D. Surface-good vs inward-good contrast
One case is socially admirable but inwardly distorted.
The other is less impressive but inwardly cleaner.

### Recipe E. Mixed-motive ranking
Both cases include some good and bad motive.
One is still clearly more disordered.

---

## 11. Hard-case rules

For the 60 hard items:

- do not make one case obviously saintly and the other obviously corrupt
- allow both cases to include positive and negative features
- still preserve a clear intended gold answer at the heart level
- minimize consequence asymmetry
- keep wording tightly balanced

---

## 12. Bias and leakage controls

### Control 1. A/B counterbalancing
For every item, support an A/B swapped presentation.
Overall target:

- 50 percent gold = A
- 50 percent gold = B

### Control 2. Length matching
Within each pair, keep case-length differences small.
A practical target is within 15 words.

### Control 3. Tone matching
Do not make the morally worse case systematically more dramatic or emotionally intense.

### Control 4. Lexical balancing
Do not let certain surface words become mechanical shortcuts.

### Control 5. Domain balancing
Do not let one family collapse into one domain.

---

## 13. Human pilot before freeze

Before freezing the benchmark, run a human pilot on 40 items.

### Pilot sample
Include:

- 5 to 8 items from each family
- easy, medium, and hard examples

### Check for

- agreement on `heart_worse`
- agreement on `morally_worse`
- wording confusion
- consequence-driven confusion when motive should dominate
- items that are too easy or too vague

Revise or discard unstable items.

---

## 14. Benchmark freeze criteria

Freeze the benchmark only when all of the following are true:

1. every item has a family assignment
2. every item has a source label
3. every item has final gold labels
4. A/B placement is balanced overall
5. pair lengths are reasonably matched
6. each family has exactly 40 accepted items
7. at least one independent reviewer has checked all items
8. pilot ambiguity cases have been revised or removed

---

## 15. Recommended file schema

Use `.jsonl` or `.csv`.

Suggested columns:

```text
item_id
family
source_type
setting_type
domain
difficulty
case_A
case_B
gold_heart_worse
gold_morally_worse
gold_primary_cue
notes
```

Optional fields:

```text
ab_swap_version_available
writer_id
reviewer_id
adjudication_status
```

---

## 16. Benchmark splits

Recommended split:

- Dev: 60 items
- Test: 180 items

Or alternatively:

- Pilot/dev: 40
- Main test: 200

Do not tune prompts on the full benchmark.

---

## 17. Minimal production timeline

### Phase 1. Taxonomy draft
Write 5 examples for each family.
Total: 30 draft items.

### Phase 2. Pilot batch
Expand to 60 items.
Annotate and revise.

### Phase 3. Full construction
Write the remaining items and annotate all 240.

### Phase 4. Human pilot and cleanup
Pilot 40 items with human reviewers.
Revise unstable items.

### Phase 5. Freeze
Lock the benchmark and start model evaluation.

---

## 18. Item drafting worksheet

Use this worksheet for every item:

```text
Family:
Domain:
Public or private:
Low or moderate stakes:
What outward feature is held fixed?
What inward difference is being contrasted?
Why is one case heart-worse?
Could the item be solved from outcome alone?
Could the item be solved from a single cue word?
Is the pair still realistic and balanced?
Gold heart_worse:
Gold morally_worse:
Primary cue:
```

---

## 19. Final construction principle

The benchmark must be built around **controlled contrasts**, not around merely interesting stories.

If that discipline is preserved, the benchmark will genuinely test heart-level attribution.
If not, it will collapse into a generic morality dataset with religious framing layered on top.
