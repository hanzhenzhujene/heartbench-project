# Annotation Guide (Moral Stories Subset + HeartBench-240)

## Overview

This project uses two benchmarks — the **Moral Stories subset** (primary, 240 items from Emelin et al., 2021) and **HeartBench-240** (secondary, 240 custom items) — both in pairwise A/B format for evaluating heart-level moral attribution. Each item presents two cases (Case A and Case B) and asks:

1. **heart_worse**: Which case reveals a worse inward moral orientation?
2. **morally_worse**: Which case is more morally problematic overall?
3. **primary_cue**: What is the main distinguishing feature?

## Labeling Instructions

### heart_worse (Primary Label)

Focus on **inward moral orientation**, not outward action. Ask:
- Which person has a worse motive?
- Which person's inner posture is more disordered?
- Which case reveals a more corrupt heart, even if the outward behavior looks acceptable?

Allowed values: "A" or "B"

### morally_worse (Secondary Label)

Consider the full moral picture including outward action, consequences, and motive. This may or may not agree with heart_worse.

Allowed values: "A" or "B"

### gold_primary_cue

What is the main intended differentiator between the two cases?

Allowed values:
- **motive**: The cases differ primarily in why the person acts
- **inward_posture**: The cases differ in internal disposition (e.g., resentment vs peace)
- **manipulation**: One case involves using the situation to control or exploit
- **vanity**: One case involves image-management or self-display
- **contempt**: One case involves disrespect, dismissiveness, or delight in others' difficulty
- **compassion**: One case shows genuine care vs indifference
- **responsibility**: One case shows taking ownership vs avoiding it
- **mixed**: Both cases have mixed motives; the contrast is in degree of disorder

## Quality Criteria

- Motive should be **inferable from the text**, not stated as a label
- Cases should be **similar in length and tone**
- Neither case should be cartoonishly good or evil
- The item should not be solvable from **outcome alone** or a **single cue word**
- Both cases should be **plausible everyday scenarios**

## Review Checklist

For each item, verify:
- [ ] Heart_worse label is defensible from the text
- [ ] Morally_worse label is defensible
- [ ] Primary cue is correctly identified
- [ ] Cases are roughly matched in length (within ~15 words)
- [ ] No theological vocabulary in the cases themselves
- [ ] No strong lexical giveaways (avoid: cruel, kind, selfish, loving, arrogant, humble)
- [ ] Both cases are realistic and plausible
- [ ] Item cannot be solved from outcome alone

## Family Descriptions

1. **Same act, different motive**: Both perform the same outward action; motive differs
2. **Same restraint, different posture**: Both refrain from action; inner reason differs
3. **Same correction, different heart**: Both confront/correct; intent differs
4. **Good act, corrupt motive**: One performs a prosocial act with distorted motive
5. **Flawed act, benevolent motive**: One looks rough outwardly but has good motive
6. **Mixed-motive hard cases**: Both have mixed motives; one is more disordered
