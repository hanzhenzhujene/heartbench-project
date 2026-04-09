# Staged Paper Revision Packet

## Scope Note

This repository did **not** contain the staged manuscript source (`.tex`, `.qmd`, manuscript markdown, or Word draft) described in the request. It also did **not** contain any live `gemma3:4b` references in tracked, non-archived code or docs.  

Accordingly, this packet does two things:

1. adds a new staged `J1 / E / J2` analysis and figure pipeline aligned with the requested paper design
2. provides manuscript-ready replacement text, captions, and reviewer-risk framing that can be pasted into the actual paper source once available

The new paper-facing experiment config now treats:

- main model: `qwen2.5:7b-instruct`
- smaller within-family robustness model: `qwen2.5:0.5b-instruct`

## 1. Concise Revision Plan

1. Re-anchor the paper around **stage dissociation**, not broad moral change.
   The core claim should be that Christian framing appears to move explanation language more strongly than first-pass exposed judgment.
2. Use direct Christian-vs-secular matched contrasts as the main identification strategy.
   Do not rely only on each condition versus baseline.
3. Treat the explanation stage as a separate mechanism layer and explicitly control for lexical echo.
   Report both raw explanation shifts and lexical-echo-controlled explanation shifts.
4. Use the staged structure fully.
   Report `J1`, `E`, and `J2` separately, and quantify revision pressure rather than collapsing them.
5. Evaluate robustness across **model scale within the Qwen family**.
   This is cleaner and more interpretable than a cross-family architecture comparison.
6. Keep weak or null first-pass Christian-over-secular effects visible.
   The stronger and cleaner claim should live at the explanation layer unless the reruns show otherwise.

## 1.1 Current Empirical Status (Completed Runs)

As of 2026-04-08, the staged pipeline has completed:

- a full 30-item dev rerun for both `qwen2.5:7b-instruct` and `qwen2.5:0.5b-instruct` at `results/staged_paper/heartbench_v2_dev/dev`
- a full 120-item main rerun for both `qwen2.5:7b-instruct` and `qwen2.5:0.5b-instruct` at `results/staged_paper/heartbench_v2/main`

The completed results already support the revised mechanism framing:

1. On both models in dev, the direct `christian_pre` versus `secular_pre` contrast on `J1` is weak or null.
2. On both models in dev, the direct `christian_post` versus `secular_post` contrast on explanation metrics is positive, and the lexical-controlled explanation effect survives.
3. On the completed `qwen2.5:0.5b-instruct` full main run, the same pattern persists at 120 items:
   - `christian_pre vs secular_pre`, `J1` heart correctness: `+0.033`, 95% CI `[0.000, 0.075]`, permutation `p = 0.2095`
   - `christian_pre vs secular_pre`, `J1` act correctness: `+0.008`, 95% CI `[-0.017, 0.033]`, permutation `p = 1.0`
   - `christian_post vs secular_post`, explanation Christianization: `+0.013`, 95% CI `[0.0078, 0.0177]`, permutation `p < 0.001`
   - `christian_post vs secular_post`, lexical-controlled explanation heart focus: `+0.015`, 95% CI `[0.0085, 0.0223]`, permutation `p < 0.001`
   - `christian_post vs secular_post`, explanation restructuring: `+0.069`, 95% CI `[0.010, 0.129]`, permutation `p = 0.0366`
4. In that same `qwen2.5:0.5b-instruct` full main run, the explanation-layer effect is not driven by overt `J1` movement:
   - `same_j1_rate = 1.0`
   - lexical-controlled explanation heart-focus still rises by `+0.015`, permutation `p < 0.001`
5. The completed `qwen2.5:7b-instruct` full main run shows the same pattern more strongly:
   - `christian_pre vs secular_pre`, `J1` heart correctness: `+0.017`, 95% CI `[-0.033, 0.067]`, permutation `p = 0.7286`
   - `christian_pre vs secular_pre`, `J1` act correctness: `-0.008`, 95% CI `[-0.075, 0.058]`, permutation `p = 1.0`
   - `christian_post vs secular_post`, explanation Christianization: `+0.049`, 95% CI `[0.0451, 0.0528]`, permutation `p < 0.001`
   - `christian_post vs secular_post`, lexical-controlled explanation heart focus: `+0.015`, 95% CI `[0.0109, 0.0194]`, permutation `p < 0.001`
   - `christian_post vs secular_post`, explanation restructuring: `+0.196`, 95% CI `[0.158, 0.233]`, permutation `p < 0.001`
   - `same_j1_rate = 1.0`

## 2. Code / Files to Modify

### Added

- `research/configs/experiment_staged_paper.yaml`
- `research/configs/prompts_staged_paper.yaml`
- `research/configs/explanation_lexicons.yaml`
- `research/prompts/staged_j1_baseline.txt`
- `research/prompts/staged_j1_with_pre_frame.txt`
- `research/prompts/staged_explanation_followup.txt`
- `research/prompts/staged_explanation_with_post_frame.txt`
- `research/prompts/staged_j2_followup.txt`
- `research/prompts/staged_repair_prompt.txt`
- `research/prompts/staged_frame_secular_v1.txt`
- `research/prompts/staged_frame_secular_v2.txt`
- `research/prompts/staged_frame_secular_v3.txt`
- `research/prompts/staged_frame_christian_v1.txt`
- `research/prompts/staged_frame_christian_v2.txt`
- `research/prompts/staged_frame_christian_v3.txt`
- `src/run_staged_paper_inference.py`
- `src/analyze_staged_paper_results.py`
- `src/plot_staged_paper_figures.py`
- `research/reports/staged_paper_revision_packet.md`

### Updated

- `src/model_inference_utils.py`
  Added generic multi-turn chat generation so the staged pipeline can run `J1`, explanation, and `J2` as separate turns.
- `src/stats_utils.py`
  Added numeric mean CIs, paired permutation tests, and paired effect sizes.

### Not directly modified because absent from repo

- manuscript source file(s)
- paper tables / figure source in LaTeX or Quarto
- any live Gemma-facing paper text

## 3. Updated Analysis Code / Pseudo-Code

### 3.1 Staged runner

The new staged runner is in:

- `src/run_staged_paper_inference.py`

Logic:

1. Load benchmark item
2. Pick condition
3. Pick prompt variant within frame family
4. Run `J1`
5. If condition is not `judgment_only`, run explanation stage
6. If condition supports `J2`, run re-judgment stage
7. Save one structured row per item with:
   - model name
   - benchmark split
   - seed
   - decoding settings
   - condition
   - frame family
   - frame placement
   - frame variant id
   - output file path
   - `J1` outputs
   - explanation text
   - `J2` outputs
   - skipped metrics

Pseudo-code:

```python
for model in models:
    for condition in conditions:
        for frame_variant in condition_variants(condition):
            for item in benchmark:
                j1 = run_first_pass(item, condition, frame_variant)
                if condition.run_explanation:
                    explanation = run_explanation(item, condition, frame_variant, j1)
                if condition.run_j2:
                    j2 = run_rejudgment(item, condition, frame_variant, j1, explanation)
                save_row(...)
```

### 3.2 Direct Christian-vs-secular paired analyses

Implemented in:

- `src/analyze_staged_paper_results.py`

Direct contrasts added:

1. `christian_pre` vs `secular_pre` on `J1` heart correctness
2. `christian_pre` vs `secular_pre` on `J1` act correctness
3. `christian_post` vs `secular_post` on:
   - explanation Christianization
   - explanation heart focus, inclusive
   - explanation heart focus, lexical controlled
   - explanation restructuring
4. `christian_post` vs `secular_post` on:
   - any `J1 -> J2` revision
   - heart revision
   - act revision

Each direct contrast reports:

- paired item-level mean difference
- bootstrap CI
- paired sign-flip permutation test
- paired effect size (`dz`)
- concise interpretation string

### 3.3 Lexical-echo-controlled explanation analysis

Config:

- `research/configs/explanation_lexicons.yaml`

Metrics:

- `explanation_direct_frame_echo_rate`
  Active frame-echo terms only
- `explanation_christianization_score`
  Christian lexicon uptake
- `explanation_heart_semantic_rate_inclusive`
  Broader motive / heart lexicon including frame terms
- `explanation_heart_semantic_rate_controlled`
  Same semantic space after removing direct Christian and secular frame-echo terms
- `explanation_heart_focus_inclusive`
  `heart_semantic - act_semantic`
- `explanation_heart_focus_controlled`
  `(heart_semantic without direct echo) - act_semantic`
- `explanation_structure_score`
  Causal + contrastive + mental-state + comparative reasoning markers

This supports the key mechanism question:

- does the explanation effect collapse once direct frame words are removed?
- or does a broader motive / heart explanation style remain?

### 3.4 `J1 / E / J2` mechanism analysis

Added metrics:

- `heart_revision`
- `act_revision`
- `any_revision`
- `heart_revision_toward_gold`
- `heart_revision_away_from_gold`
- `act_revision_toward_gold`
- `act_revision_away_from_gold`

Also added a targeted test for:

- explanation change **when J1 is unchanged**

This is captured in:

- `same_j1_explanation_shift.csv`

and directly addresses the mechanism claim that post-framing may alter explanation language without materially moving first-pass exposed judgment.

### 3.5 Heterogeneity

Configured in:

- `research/configs/experiment_staged_paper.yaml`

Current slices:

- `motive_salience_core`
- `appearance_vs_intention`
- `good_act_bad_motive`
- `bad_act_good_motive`
- `mixed_stakeholder_context`

The analysis script computes slice-level Christian-vs-secular contrasts for:

- `J1` heart correctness under pre framing
- lexical-controlled explanation heart focus under post framing

### 3.6 Prompt-paraphrase robustness

Implemented structurally via:

- frame families
- multiple Christian variants
- multiple secular variants
- aggregation across variants at analysis time

This means the paper no longer depends on a single Christian string and a single secular string.  

For smoke validation, the runner also supports:

- `--variant-limit-per-family`

so we can debug on one paraphrase per family without changing the full robustness design.

## 4. Updated Paper Text, Section by Section

Because the staged manuscript source is absent from this repository, the text below is written as paste-ready replacement language with bracketed placeholders where the final rerun numbers should be inserted from:

- `results/staged_paper/<benchmark>/<split>/direct_comparison_summary.csv`
- `results/staged_paper/<benchmark>/<split>/summary_by_condition.csv`
- `results/staged_paper/<benchmark>/<split>/heterogeneity_summary.csv`

### 4.1 Abstract

Replace the main result sentence with:

> We test whether Christian heart-focused framing changes first-pass exposed moral judgment or primarily reshapes post-hoc explanation. Across a staged `J1 / E / J2` design, we find that matched Christian framing produces [modest / small / near-zero] first-pass movement relative to a matched secular motive-focused control, but substantially larger movement in explanation language. This explanation-layer effect remains [partly / substantially / weakly] detectable after removing direct frame-echo terms, suggesting that Christian framing affects explanation style more strongly than first-pass exposed judgment.

Model sentence:

> We evaluate the main pattern on `qwen2.5:7b-instruct` and a smaller within-family robustness model, `qwen2.5:0.5b-instruct`, to test whether stage dissociation is stable across model scale within the same architecture family.

Calibration sentence:

> We treat “intuition” operationally, as the model’s first-pass exposed forced-choice judgment, rather than as an ontological claim about internal cognition.

### 4.2 Introduction

Add or revise the problem framing:

> Prior work can blur two distinct possibilities: framing may alter a model’s first-pass exposed judgment, or it may primarily alter the language used to justify a judgment after the fact. To separate these possibilities, we use a staged design with an initial forced-choice judgment (`J1`), an explanation stage (`E`), and a re-judgment stage (`J2`).

Add matched-control identification:

> A matched secular motive-focused control is essential for interpretation. It lets us distinguish generic motive salience from what is specifically associated with Christian framing.

Replace any architecture-robustness sentence with:

> Our robustness comparison is now within-family: we compare `qwen2.5:7b-instruct` to `qwen2.5:0.5b-instruct` to ask whether the same stage dissociation persists across scale within Qwen, rather than across unrelated architectures.

### 4.3 Methods: Design

Paste-ready text:

> We evaluate six conditions: `baseline`, `secular_pre`, `christian_pre`, `secular_post`, `christian_post`, and `judgment_only`. In pre conditions, the frame is shown before `J1`. In post conditions, the frame is introduced only after `J1`, before explanation and re-judgment. `judgment_only` elicits `J1` alone.

> Each item yields two parallel judgments: a `heart` judgment and an `act` judgment. This design allows us to test whether framing selectively affects inward-motive evaluation, outward-act evaluation, explanation content, or revision pressure.

### 4.4 Methods: Models

Use this exactly:

> Our main model is `qwen2.5:7b-instruct`. Our smaller comparison model is `qwen2.5:0.5b-instruct`. Using two scales within the same Qwen family reduces interpretive ambiguity relative to cross-family comparisons and helps test whether stage dissociation is stable across model size.

### 4.5 Methods: Primary Comparisons

Paste-ready text:

> Our primary inferential comparisons are direct Christian-versus-secular matched contrasts rather than only condition-versus-baseline contrasts. Specifically, we test `christian_pre` versus `secular_pre` on first-pass heart and act judgments, and `christian_post` versus `secular_post` on explanation-layer metrics and `J1 -> J2` revision behavior.

### 4.6 Methods: Explanation Analysis

Paste-ready text:

> Explanation analysis uses three nested measures. First, we measure direct lexical echo of frame words and close paraphrases. Second, we measure broader heart- and motive-related language with frame-echo terms retained. Third, we recompute the same semantic shift after removing direct frame-echo terms. This allows us to estimate how much of the explanation effect survives lexical control.

> We also track explanation restructuring beyond word reuse using causal, contrastive, mental-state, and comparative discourse markers.

### 4.7 Methods: Statistics

Paste-ready text:

> All reported condition contrasts are paired at the item level. For each contrast, we report the paired mean difference, bootstrap confidence intervals, a paired sign-flip permutation test, and a paired effect size (`dz`). Binary revision and correctness metrics are analyzed in the same paired framework by treating per-item outcomes as numeric proportions after prompt-variant aggregation.

### 4.8 Results: First-Pass Judgment

Use this calibrated framing:

> First-pass exposed judgment moves less than explanation language. On the main model, the direct Christian-versus-secular pre-frame contrast on `J1` heart judgment is [small / modest / null], with an estimated paired difference of [INSERT], 95% CI [INSERT], and permutation `p = [INSERT]`. The corresponding act-level contrast is [near zero / weak / null], consistent with the view that Christian framing does not produce broad first-pass outward-act movement.

> This pattern matters because it shifts the paper’s center of gravity away from broad “moral change” and toward stage-specific interpretive movement.

### 4.9 Results: Explanation Layer

Use this as the main claim paragraph:

> The clearest Christian-versus-secular difference appears at the explanation layer. Under post framing, Christian explanations show [higher / modestly higher] Christianization and [higher / modestly higher] heart-focused language than matched secular post framing. Crucially, [some / much / little] of this effect survives after direct frame-echo terms are removed, indicating that the explanation shift is not reducible to exact lexical reuse alone.

Add the lexical-control caution explicitly:

> At the same time, direct frame echo explains a non-trivial portion of the raw explanation effect, so explanation results should be interpreted as partly rhetorical unless the lexical-controlled metric remains clearly above zero.

### 4.10 Results: `J1 -> J2` Revision

Paste-ready text:

> Post framing exerts its strongest pressure after first-pass exposure. Relative to matched secular post framing, Christian post framing changes revision behavior by [INSERT], but the revision effect is [smaller than / comparable to / larger than] the explanation-layer shift. This again suggests that explanation language is the more responsive stage.

And a dissociation sentence:

> We also find that Christian post framing can alter explanation metrics even on items where `J1` is unchanged, providing a direct stage-dissociation result.

### 4.11 Results: Heterogeneity

Paste-ready text:

> Effects are strongest in item slices where inward motive should matter most, especially [INSERT SLICE NAMES WITH STRONGEST EFFECTS]. In contrast, slices dominated by outwardly clear act differences show [weaker / negligible] Christian-versus-secular separation. This concentration in motive-salient categories is consistent with the paper’s mechanism claim.

### 4.12 Results: Model-Scale Robustness

Paste-ready text:

> The robustness comparison now asks whether the same stage dissociation persists across model scale within Qwen. The smaller `qwen2.5:0.5b-instruct` model shows [weaker / noisier / qualitatively similar] separation between first-pass judgment and explanation movement, indicating that [INSERT RESULT]. This is a cleaner robustness test than comparing unrelated architectures because it changes scale while holding family constant.

### 4.13 Discussion

Use this more careful discussion frame:

> Our evidence is strongest for a stage-dissociation account: Christian framing appears to influence how the model explains and recontextualizes a judgment more strongly than it changes the first-pass exposed judgment itself. This does not mean that first-pass judgment is wholly unaffected; rather, the first-pass Christian-over-secular effect is [modest / small / weak] relative to the larger explanation-layer movement.

> More broadly, the matched secular control sharpens the interpretation. To the extent that Christian framing exceeds secular motive salience, the excess appears at explanation time more than at first-pass judgment time.

### 4.14 Limitations

Use this full paragraph block:

> Several limitations remain. First, explanation-layer effects remain vulnerable to lexical priming, even with explicit lexical controls. Second, benchmark construction still involves researcher degrees of freedom, especially in item family design and category mapping. Third, our results currently depend on open instruct models and may not generalize to proprietary or non-instruction-tuned systems. Fourth, if case-level human relabeling remains incomplete, the strongest mechanism benchmark should still be treated as partially provisional rather than final ground truth. Finally, any null or weak first-pass Christian-over-secular result should remain visible rather than being displaced by stronger explanation-layer findings.

### 4.15 Conclusion

Use this as the strongest honest conclusion:

> Christian framing does not primarily look like a broad first-pass moral override. Instead, the cleaner and stronger evidence is that it reshapes explanation language more than first-pass exposed judgment. The matched secular control shows that some of this movement is generic motive salience, while the residual Christian-over-secular difference is most plausibly located at the explanation layer and, more weakly, in revision pressure rather than in a large first-pass judgment shift.

## 5. Updated Figure Plan and Captions

The plotting code now supports all five requested figures:

- `src/plot_staged_paper_figures.py`

### Figure 1: First-pass judgment shift

File:

- `figure_1_first_pass_shift.png`

Takeaway:

- Shows heart-level movement versus near-zero act-level movement, all relative to baseline

Caption:

> **Figure 1. First-pass judgment shift remains concentrated in heart-sensitive movement rather than outward-act movement.** Each point shows the mean item-level shift relative to baseline, with bootstrap confidence intervals. Pre and post conditions are plotted for both `qwen2.5:7b-instruct` and `qwen2.5:0.5b-instruct`. The main visual contrast is whether Christian framing moves first-pass heart judgment more than act judgment; the paper’s mechanism claim is stronger when act-level first-pass movement remains near zero.

### Figure 2: Explanation-layer effect

Files:

- `figure_2_explanation_layer_effects.png`

Takeaway:

- Separates direct lexical echo from broader heart-language movement and structural explanation change

Caption:

> **Figure 2. Explanation-layer movement is larger than direct frame-word reuse alone.** The panels separate direct frame echo, inclusive heart-focused explanation language, lexical-echo-controlled heart-focused explanation language, and explanation restructuring. A surviving effect in the controlled panel supports the claim that Christian framing affects explanation style beyond simple repetition of frame words.

### Figure 3: Judgment-vs-explanation dissociation

Files:

- `figure_3_judgment_vs_explanation_dissociation.png`

Takeaway:

- Makes it visually obvious when explanation shift exceeds first-pass shift

Caption:

> **Figure 3. Explanation movement can exceed first-pass judgment movement.** Each point is a condition-level summary for a given model, with the x-axis showing first-pass heart shift relative to baseline and the y-axis showing lexical-controlled explanation shift relative to baseline. Conditions that move upward more than rightward support a stage-dissociation interpretation.

### Figure 4: `J1 -> J2` revision

Files:

- `figure_4_revision_rates.png`

Takeaway:

- Shows whether post framing changes re-judgment pressure

Caption:

> **Figure 4. Post framing can increase revision pressure without implying a large first-pass effect.** The figure reports any revision, heart revision, and act revision by condition and model. If Christian post framing changes explanation more strongly than first-pass judgment, revision effects should appear mainly after `J1`, not before it.

### Figure 5: Heterogeneity

Files:

- `figure_5_heterogeneity.png`

Takeaway:

- Tests whether effects concentrate in theoretically expected motive-salient slices

Caption:

> **Figure 5. Framing effects are strongest in motive-salient item slices.** Each point is the Christian-minus-secular paired effect within a theoretical slice. Effects concentrated in motive-salient categories support the claim that the mechanism is not a generic response artifact, but is more closely tied to inward-motive evaluation.

## 6. Reviewer-Risk Memo

### Reviewer concern 1

**“Your effect is just lexical priming.”**

Response:

- We now report direct frame echo separately from broader heart-language shift.
- We explicitly recompute the explanation effect after removing direct frame-echo terms.
- We also report explanation restructuring markers that are not reducible to word reuse.

Residual risk:

- Some rhetorical uptake may still survive lexical control because semantic drift is not fully captured by simple lexicons.

### Reviewer concern 2

**“Christian only beats baseline because any motive prompt would.”**

Response:

- The main identification contrast is now Christian versus matched secular, not just each versus baseline.
- All central claims should be anchored in `christian_pre vs secular_pre` and `christian_post vs secular_post`.

### Reviewer concern 3

**“You are over-claiming moral change.”**

Response:

- The revised paper should explicitly narrow the claim to stage dissociation.
- First-pass movement is described as modest or null unless the direct Christian-versus-secular `J1` contrast is clearly positive.
- The main claim now lives at the explanation layer.

### Reviewer concern 4

**“Your robustness model changed the story because it is a different architecture.”**

Response:

- The robustness comparison is now within-family: `qwen2.5:7b-instruct` versus `qwen2.5:0.5b-instruct`.
- This isolates model scale more cleanly than a cross-family robustness check.

### Reviewer concern 5

**“The item families are researcher degrees of freedom.”**

Response:

- We now report heterogeneity by pre-specified slices rather than only cherry-picked exemplars.
- The paper should keep benchmark-construction limitations visible and avoid treating the category mapping as perfectly theory-free.

### Reviewer concern 6

**“Your strongest benchmark still has partial heuristic labeling.”**

Response:

- The paper should state this directly.
- The repository now includes a blind relabel workflow, but until that process is complete, the strongest benchmark should be described as partly provisional.

## 7. Short Summary Table

| Analysis | Effect on claim | Why it matters |
|---|---|---|
| Direct `christian_pre vs secular_pre` on `J1` heart and act | Mainly refines, may weaken broad framing claims | Forces the paper to show whether first-pass Christian movement is actually stronger than matched secular motive salience |
| Direct `christian_post vs secular_post` on explanation metrics | Strengthens | This is the cleanest test of the mechanism claim that Christian framing affects explanation language |
| Lexical-echo-controlled explanation analysis | Can strengthen or weaken depending on survival | If the effect survives lexical control, the explanation claim is more reviewer-resistant; if it collapses, the rhetoric claim must be narrowed |
| `J1 -> J2` revision analysis | Refines | Shows whether post framing changes re-judgment pressure rather than first-pass judgment |
| “Explanation shift with J1 unchanged” test | Strongly strengthens if positive | Directly supports stage dissociation |
| Heterogeneity by motive-salient item type | Strengthens if concentrated where theory predicts | Helps argue mechanism rather than generic prompt response |
| Within-family scale robustness (`Qwen 7B` vs `Qwen 0.5B`) | Refines | Recasts robustness as scale stability within one architecture family |
| Honest visibility of null / weak first-pass Christian effects | May weaken the older headline, but improves credibility | Makes the revised paper more believable and less vulnerable to overclaim critiques |

## 8. Practical Run Order

For the full paper rerun, the recommended order is:

1. `python3 src/run_staged_paper_inference.py --group dev_smoke_qwen05 --variant-limit-per-family 1 --output-dir results/staged_paper_smoke/heartbench_v2_dev/dev`
2. `python3 src/analyze_staged_paper_results.py --benchmark heartbench_v2_dev --results-root results/staged_paper_smoke`
3. `python3 src/plot_staged_paper_figures.py --benchmark heartbench_v2_dev --results-root results/staged_paper_smoke`
4. full rerun on `heartbench_v2` with:
   - `qwen2.5:7b-instruct`
   - `qwen2.5:0.5b-instruct`
5. fill manuscript placeholders from:
   - `direct_comparison_summary.csv`
   - `summary_by_condition.csv`
   - `heterogeneity_summary.csv`
   - figure outputs
