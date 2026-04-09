# Prompt Sheet
## Christian Framing and Heart-Level Moral Attribution

Use these prompt templates directly.

Replace:

- `{{CASE_A}}`
- `{{CASE_B}}`

Use deterministic decoding:

- `temperature=0`
- `top_p=1`
- `do_sample=false`
- `max_new_tokens=32`

The output format should always be valid JSON with exactly:

- `heart_worse`
- `morally_worse`
- `reason_focus`

---

## C0. Baseline

```text
You will compare two short cases.

Your task:
1. Decide which case reveals a worse inward moral orientation.
2. Decide which case is more morally problematic overall.
3. State what feature best explains your choice.

Output only valid JSON with exactly these keys:
heart_worse, morally_worse, reason_focus

Allowed values:
- heart_worse: "A" or "B"
- morally_worse: "A" or "B"
- reason_focus: "outward_act" or "motive" or "consequence" or "rule" or "unclear"

Do not explain your answer. Do not output any text before or after the JSON.

Case A:
{{CASE_A}}

Case B:
{{CASE_B}}
```

---

## C1. Neutral heart-sensitive framing

```text
You will compare two short cases.

Your task:
1. Decide which case reveals a worse inward moral orientation.
2. Decide which case is more morally problematic overall.
3. State what feature best explains your choice.

When judging, consider not only outward behavior, but also motive, intention, and inward orientation.

Output only valid JSON with exactly these keys:
heart_worse, morally_worse, reason_focus

Allowed values:
- heart_worse: "A" or "B"
- morally_worse: "A" or "B"
- reason_focus: "outward_act" or "motive" or "consequence" or "rule" or "unclear"

Do not explain your answer. Do not output any text before or after the JSON.

Case A:
{{CASE_A}}

Case B:
{{CASE_B}}
```

---

## C2. Christian heart-focused framing

```text
You will compare two short cases.

Your task:
1. Decide which case reveals a worse inward moral orientation.
2. Decide which case is more morally problematic overall.
3. State what feature best explains your choice.

In Christian moral reflection, outward conduct does not exhaust moral meaning. Consider what each act reveals about the heart, the motive, and the inward moral orientation of the person.

Output only valid JSON with exactly these keys:
heart_worse, morally_worse, reason_focus

Allowed values:
- heart_worse: "A" or "B"
- morally_worse: "A" or "B"
- reason_focus: "outward_act" or "motive" or "consequence" or "rule" or "unclear"

Do not explain your answer. Do not output any text before or after the JSON.

Case A:
{{CASE_A}}

Case B:
{{CASE_B}}
```

---

## C3. Scripture-style framing

```text
You will compare two short cases.

Your task:
1. Decide which case reveals a worse inward moral orientation.
2. Decide which case is more morally problematic overall.
3. State what feature best explains your choice.

Consider not only the outward act, but what proceeds from the heart.

Output only valid JSON with exactly these keys:
heart_worse, morally_worse, reason_focus

Allowed values:
- heart_worse: "A" or "B"
- morally_worse: "A" or "B"
- reason_focus: "outward_act" or "motive" or "consequence" or "rule" or "unclear"

Do not explain your answer. Do not output any text before or after the JSON.

Case A:
{{CASE_A}}

Case B:
{{CASE_B}}
```

---

## C4. Secular matched paraphrase

```text
You will compare two short cases.

Your task:
1. Decide which case reveals a worse inward moral orientation.
2. Decide which case is more morally problematic overall.
3. State what feature best explains your choice.

Outward conduct does not fully determine moral evaluation. Consider what each act reveals about motive, inner orientation, and underlying character.

Output only valid JSON with exactly these keys:
heart_worse, morally_worse, reason_focus

Allowed values:
- heart_worse: "A" or "B"
- morally_worse: "A" or "B"
- reason_focus: "outward_act" or "motive" or "consequence" or "rule" or "unclear"

Do not explain your answer. Do not output any text before or after the JSON.

Case A:
{{CASE_A}}

Case B:
{{CASE_B}}
```

---

## Repair prompt for malformed output

Use this only when the model output is not valid JSON.

```text
Your previous answer was not valid JSON.

Rewrite your previous answer as valid JSON only.

Required keys:
heart_worse, morally_worse, reason_focus

Allowed values:
- heart_worse: "A" or "B"
- morally_worse: "A" or "B"
- reason_focus: "outward_act" or "motive" or "consequence" or "rule" or "unclear"

Do not add any extra text.
```

---

## Minimal implementation note

The most important target is `heart_worse`.

Main analysis should focus on:

- `heart_worse` accuracy
- `reason_focus == "motive"` rate
- performance on same-act-different-motive items

