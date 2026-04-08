# Benchmark Construction Notes

## Dual Benchmark Architecture

This project uses two benchmarks:

1. **Moral Stories Subset (Primary)**: 240 items derived from the Moral Stories dataset (Emelin et al., 2021). Externally sourced, peer-reviewed. See `moral_stories_benchmark_summary.md` for details.
2. **HeartBench-240 (Secondary)**: 240 custom-constructed items. See below.

Both use identical A/B pairwise format, family taxonomy, and scoring pipeline.

---

## Moral Stories Subset Construction

### Source
- Moral Stories (Emelin et al., 2021): 12,000 crowdsourced items with situation, intention, moral/immoral action pairs
- Each item grounded in a human-written social norm

### Selection and Conversion
1. Filtered 12,000 items to 11,724 heart-relevant candidates (removed items with strong lexical giveaways, too-short actions, or non-informative intentions)
2. Classified each into families using heuristic rules on text overlap and keyword patterns
3. Selected 40 per family (240 total) with domain diversity constraints
4. Converted to A/B pairs: situation + immoral_action vs situation + moral_action
5. Counterbalanced: swapped every other item for 50/50 A/B balance
6. Created dev/test splits: 60 dev + 180 test (10/30 per family)
7. Saved traced version preserving source IDs, norms, and intentions

### Assumptions
- Gold labels (heart_worse = the case using immoral_action) are defensible but heuristic
- Family classification is based on keyword matching, not human annotation
- Difficulty labels are assigned based on lexical overlap heuristics

---

## HeartBench-240 Construction

### Item Generation
- 240 items total: 120 adapted (source-inspired) + 120 original
- 40 items per family, 6 families
- Items were written to follow controlled pairwise A/B comparison format
- Each item contrasts outward action vs inward motive/heart orientation

### Design Decisions

1. **Theology-neutral items**: No theological vocabulary in case text. Framing comes only from prompt conditions, not from the benchmark items themselves.

2. **A/B counterbalancing**: Half the items have gold_heart_worse=A, half have gold_heart_worse=B. This was achieved by swapping case A/B on every other item within each family (deterministic, seed=42).

3. **Length matching**: Cases were written to be 1-3 sentences, roughly 35-85 words. Average word count difference between case A and case B is ~3.5 words (max 13).

4. **Difficulty tiers**: Easy (68), Medium (125), Hard (47). Distribution skews toward medium as intended—most items require careful reading but are not ambiguous.

5. **Domain coverage**: workplace (67), community (60), family (41), school (37), friendship (35). Workplace and community are overrepresented because they naturally support more institutional/public contrasts.

6. **Setting balance**: public (145) vs private (95). Some imbalance exists because families 1-3 (same outward act/restraint/correction) naturally involve observable behavior.

### Motive Contrasts Used
- sincere care vs impression management
- mercy vs contempt
- responsibility vs domination
- restraint vs vanity
- correction vs humiliation
- generosity vs self-display
- empathy vs indifference
- honesty vs self-righteousness
- genuine help vs transactional leverage
- quiet integrity vs image protection

### Known Limitations

1. **Single annotator**: Items were drafted by a single system (Claude) rather than multiple human writers. The annotation workflow (writer → reviewer → adjudication) was simplified. Items should be reviewed by domain experts before use in publication.

2. **All items are in English**: No cross-lingual coverage.

3. **Cultural scope**: Scenarios reflect Western workplace/community/family norms. Cross-cultural validity is not established.

4. **Difficulty labels are author-assigned**: Ideally difficulty should be calibrated from human agreement data.

5. **No explicit outcome matching**: While care was taken to not let outcomes dominate, some items may have residual outcome asymmetry.

### Validation Results
- 0 errors, 0 warnings in automated validation
- All 240 items have complete metadata
- No duplicate item IDs
- No duplicate case texts
- Gold label balance: 120 A / 120 B (exactly 50/50)
- Low cue-word frequency (no lexical shortcuts)
