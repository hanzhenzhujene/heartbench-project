#!/usr/bin/env python3
"""
Build the Moral Stories subset benchmark for HeartBench.

Selects 240 items from the Moral Stories dataset (Emelin et al., 2021),
converts them into pairwise A/B comparisons for heart-level attribution,
and assigns family, difficulty, domain, and other metadata.

Source: https://github.com/demelin/moral_stories
HuggingFace: https://huggingface.co/datasets/demelin/moral_stories

Selection criteria:
- Intention must be morally informative (not just describing a goal)
- Both moral and immoral actions must be plausible
- Cases should support inward motive vs outward action contrasts
- Balanced across families and difficulty levels

The A/B construction:
- Each Moral Stories item has: situation, intention, moral_action, immoral_action
- We construct a Case A and Case B by combining situation + intention + one action
- The "heart_worse" label refers to which case reveals worse inward orientation
- For most items: the immoral_action reveals worse heart orientation
"""

import json
import os
import re
import csv
import random
import hashlib
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional

# ---------------------------------------------------------------------------
# Heuristic classifiers for filtering and metadata assignment
# ---------------------------------------------------------------------------

# Domain keywords
DOMAIN_KEYWORDS = {
    "workplace": ["boss", "coworker", "employee", "office", "job", "work", "company",
                   "manager", "colleague", "hired", "fired", "salary", "interview",
                   "promotion", "meeting", "deadline", "project"],
    "school": ["student", "teacher", "class", "school", "professor", "exam", "grade",
               "homework", "college", "university", "tutor", "classmate", "campus",
               "study", "assignment"],
    "family": ["parent", "child", "mother", "father", "son", "daughter", "sibling",
               "brother", "sister", "family", "husband", "wife", "spouse", "grandpa",
               "grandma", "uncle", "aunt", "nephew", "niece", "kid"],
    "friendship": ["friend", "buddy", "pal", "roommate", "roomie", "companion"],
    "community": ["neighbor", "store", "shop", "restaurant", "church", "park",
                   "volunteer", "community", "charity", "donation", "drive", "road",
                   "traffic", "customer", "waiter", "clerk", "stranger"],
}

# Family classification keywords/patterns
FAMILY_PATTERNS = {
    "motive_contrast": [
        # Indicators that intention differs while action surface may be similar
        "wants to", "decides to", "plans to", "intends to",
    ],
    "compliance_vs_heart": [
        # Following rules vs genuine care
        "rule", "law", "policy", "required", "obligation", "duty",
        "supposed to", "have to", "must",
    ],
    "correction_vs_harm": [
        # Correcting someone vs harming them
        "confront", "correct", "tell", "inform", "report", "warn",
        "criticize", "address", "call out",
    ],
    "prosocial_surface": [
        # Outwardly good actions
        "help", "donate", "volunteer", "support", "give", "share",
        "offer", "assist", "contribute",
    ],
}

# Cue word sets for quality filtering
STRONG_MORAL_CUES = {
    "evil", "wicked", "horrible", "terrible", "awful", "disgusting",
    "saintly", "angelic", "perfect", "heroic",
}


def classify_domain(text: str) -> str:
    """Classify domain from combined text."""
    text_lower = text.lower()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        scores[domain] = sum(1 for kw in keywords if kw in text_lower)
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return "community"  # default


def classify_family(item: dict) -> str:
    """Classify into one of 6 HeartBench families based on item content."""
    situation = item.get("situation", "").lower()
    intention = item.get("intention", "").lower()
    moral_act = item.get("moral_action", "").lower()
    immoral_act = item.get("immoral_action", "").lower()

    # Check if moral and immoral actions share significant surface similarity
    moral_words = set(moral_act.split())
    immoral_words = set(immoral_act.split())
    overlap = len(moral_words & immoral_words) / max(len(moral_words | immoral_words), 1)

    # High overlap → same act, different motive
    if overlap > 0.5:
        return "same_act_different_motive"

    # Check for correction/confrontation patterns
    combined = moral_act + " " + immoral_act
    if any(w in combined for w in ["confront", "correct", "tell", "report", "warn",
                                     "address", "call out", "criticize"]):
        return "same_correction_different_heart"

    # Check for prosocial surface in immoral action (outwardly good, inwardly corrupt)
    if any(w in immoral_act for w in ["help", "donate", "give", "offer", "support"]):
        return "good_act_corrupt_motive"

    # Check for restraint patterns
    if any(w in combined for w in ["doesn't", "does not", "refuses", "avoids",
                                     "refrains", "holds back", "decides not"]):
        return "same_restraint_different_posture"

    # Check for flawed surface in moral action
    moral_neg = any(w in moral_act for w in ["awkward", "rough", "blunt", "harsh",
                                                "difficult", "struggle"])
    if moral_neg:
        return "flawed_act_benevolent_motive"

    # Default: mixed motive
    return "mixed_motive_hard"


def classify_difficulty(item: dict) -> str:
    """Assign difficulty based on how clearly the motive contrast emerges."""
    intention = item.get("intention", "")
    moral_act = item.get("moral_action", "")
    immoral_act = item.get("immoral_action", "")

    # Easy: immoral action is clearly worse on the surface too
    immoral_lower = immoral_act.lower()
    easy_signals = ["steal", "lie", "cheat", "trick", "deceive", "ignore",
                    "refuse to", "doesn't care", "takes advantage"]
    if any(s in immoral_lower for s in easy_signals):
        return "easy"

    # Hard: both actions sound plausible and surface differences are small
    moral_words = set(moral_act.lower().split())
    immoral_words = set(immoral_act.lower().split())
    overlap = len(moral_words & immoral_words) / max(len(moral_words | immoral_words), 1)
    if overlap > 0.4:
        return "hard"

    return "medium"


def classify_setting(item: dict) -> str:
    """Classify as public or private setting."""
    text = (item.get("situation", "") + " " + item.get("moral_action", "")).lower()
    public_cues = ["public", "meeting", "crowd", "everyone", "office", "school",
                   "store", "restaurant", "park", "event", "party", "group",
                   "class", "team", "community"]
    private_cues = ["alone", "private", "home", "bedroom", "secret", "quietly",
                    "by himself", "by herself", "personal"]
    pub = sum(1 for c in public_cues if c in text)
    priv = sum(1 for c in private_cues if c in text)
    return "public" if pub >= priv else "private"


def intention_is_morally_informative(item: dict) -> bool:
    """Check if the intention reveals something about moral character."""
    intention = item.get("intention", "").lower()
    # Skip very generic intentions
    generic = ["wants to", "decides to", "plans to"]
    if len(intention.split()) < 4:
        return False
    # Check for motive-revealing language
    motive_words = ["help", "care", "protect", "support", "improve", "benefit",
                    "harm", "take advantage", "get revenge", "impress", "show off",
                    "avoid", "save", "give", "share", "manipulate", "control",
                    "please", "respect", "earn", "contribute"]
    return any(w in intention for w in motive_words) or len(intention.split()) >= 5


def is_heart_relevant(item: dict) -> bool:
    """Check if this item tests heart-level vs surface-level moral judgment."""
    intention = item.get("intention", "")
    moral_act = item.get("moral_action", "")
    immoral_act = item.get("immoral_action", "")

    # Must have all fields non-empty
    if not all([intention, moral_act, immoral_act]):
        return False

    # Filter out items with extremely strong lexical giveaways
    combined = (moral_act + " " + immoral_act).lower()
    if any(cue in combined for cue in STRONG_MORAL_CUES):
        return False

    # Must have meaningful intention
    if not intention_is_morally_informative(item):
        return False

    # Actions should be reasonable length
    for act in [moral_act, immoral_act]:
        words = len(act.split())
        if words < 5 or words > 50:
            return False

    return True


def classify_primary_cue(item: dict) -> str:
    """Determine the primary moral cue that distinguishes the pair."""
    intention = item.get("intention", "").lower()
    immoral_act = item.get("immoral_action", "").lower()

    if any(w in immoral_act for w in ["manipulate", "trick", "deceive", "exploit",
                                        "take advantage", "use", "leverage"]):
        return "manipulation"
    if any(w in immoral_act for w in ["show off", "brag", "impress", "look good",
                                        "attention", "recognition", "credit"]):
        return "vanity"
    if any(w in immoral_act for w in ["mock", "humiliate", "belittle", "insult",
                                        "dismiss", "ignore", "disrespect"]):
        return "contempt"
    if any(w in intention for w in ["help", "care", "protect", "support", "safe"]):
        return "compassion"
    if any(w in intention for w in ["responsible", "duty", "obligation", "right thing"]):
        return "responsibility"

    return "motive"


def build_case_text(situation: str, intention: str, action: str) -> str:
    """Build a case description from Moral Stories components.

    Combines situation + intention + action into a coherent 1-3 sentence case.
    """
    # Clean up
    situation = situation.strip().rstrip(".")
    intention = intention.strip().rstrip(".")
    action = action.strip()

    # Build concise case: situation provides context, action is the behavior
    # We include intention implicitly through the action context
    case = f"{situation}. {action}"

    return case


def construct_ab_pair(item: dict, swap: bool = False) -> dict:
    """Convert a Moral Stories item into an A/B pair.

    By default:
    - Case A = situation + immoral_action (heart-worse)
    - Case B = situation + moral_action (heart-better)

    If swap=True, these are reversed (and gold labels flip).
    """
    situation = item["situation"]
    intention = item["intention"]

    immoral_case = build_case_text(situation, intention, item["immoral_action"])
    moral_case = build_case_text(situation, intention, item["moral_action"])

    if swap:
        case_a = moral_case
        case_b = immoral_case
        gold_hw = "B"
        gold_mw = "B"
    else:
        case_a = immoral_case
        case_b = moral_case
        gold_hw = "A"
        gold_mw = "A"

    return {
        "case_A": case_a,
        "case_B": case_b,
        "gold_heart_worse": gold_hw,
        "gold_morally_worse": gold_mw,
    }


def select_and_build_subset(
    all_items: list,
    target_size: int = 240,
    seed: int = 42,
) -> list:
    """Select a stratified subset and convert to A/B format."""

    rng = random.Random(seed)

    # Step 1: Filter to heart-relevant items
    candidates = [item for item in all_items if is_heart_relevant(item)]
    print(f"Heart-relevant candidates: {len(candidates)} / {len(all_items)}")

    # Step 2: Classify each candidate
    for item in candidates:
        combined_text = " ".join([
            item.get("situation", ""), item.get("intention", ""),
            item.get("moral_action", ""), item.get("immoral_action", ""),
        ])
        item["_family"] = classify_family(item)
        item["_domain"] = classify_domain(combined_text)
        item["_difficulty"] = classify_difficulty(item)
        item["_setting"] = classify_setting(item)
        item["_cue"] = classify_primary_cue(item)

    # Step 3: Stratified selection by family
    by_family = defaultdict(list)
    for item in candidates:
        by_family[item["_family"]].append(item)

    print("\nCandidate distribution by family:")
    for fam, items in sorted(by_family.items()):
        print(f"  {fam}: {len(items)}")

    # Target: equal items per family
    families = [
        "same_act_different_motive",
        "same_restraint_different_posture",
        "same_correction_different_heart",
        "good_act_corrupt_motive",
        "flawed_act_benevolent_motive",
        "mixed_motive_hard",
    ]
    per_family = target_size // len(families)  # 40

    selected = []
    for fam in families:
        pool = by_family.get(fam, [])
        rng.shuffle(pool)

        # Try to get diversity in domain and difficulty
        picked = []
        domains_seen = Counter()
        difficulties_seen = Counter()

        for item in pool:
            if len(picked) >= per_family:
                break
            # Soft diversity constraint: don't over-concentrate
            dom = item["_domain"]
            diff = item["_difficulty"]
            if domains_seen[dom] < per_family // 3 + 2 or len(pool) - len(picked) < per_family - len(picked):
                picked.append(item)
                domains_seen[dom] += 1
                difficulties_seen[diff] += 1

        # If we don't have enough, just take what we can
        while len(picked) < per_family and pool:
            remaining = [p for p in pool if p not in picked]
            if remaining:
                picked.append(remaining[0])
                pool.remove(remaining[0])
            else:
                break

        selected.extend(picked)
        print(f"  {fam}: selected {len(picked)}/{per_family}")

    print(f"\nTotal selected: {len(selected)} / target {target_size}")

    # Step 4: Convert to A/B pairs with counterbalancing
    results = []
    for i, item in enumerate(selected):
        swap = (i % 2 == 1)  # Swap every other item for A/B balance
        pair = construct_ab_pair(item, swap=swap)

        item_id = f"ms_{item['_family'][:4]}_{i+1:03d}"
        # Make IDs unique across families
        fam_abbrev = {
            "same_act_different_motive": "sadm",
            "same_restraint_different_posture": "srdp",
            "same_correction_different_heart": "scdh",
            "good_act_corrupt_motive": "gacm",
            "flawed_act_benevolent_motive": "fabm",
            "mixed_motive_hard": "mmhc",
        }.get(item["_family"], item["_family"][:4])
        fam_idx = sum(1 for r in results if r["family"] == item["_family"]) + 1
        item_id = f"ms_{fam_abbrev}_{fam_idx:03d}"

        result = {
            "item_id": item_id,
            "family": item["_family"],
            "source_type": "moral_stories",
            "setting_type": item["_setting"],
            "domain": item["_domain"],
            "difficulty": item["_difficulty"],
            "case_A": pair["case_A"],
            "case_B": pair["case_B"],
            "gold_heart_worse": pair["gold_heart_worse"],
            "gold_morally_worse": pair["gold_morally_worse"],
            "gold_primary_cue": item["_cue"],
            "notes": f"From Moral Stories ID={item['ID']}. Norm: {item['norm']}",
            # Extra metadata for traceability
            "ms_id": item["ID"],
            "ms_norm": item["norm"],
            "ms_intention": item["intention"],
        }
        results.append(result)

    return results


def create_splits(items: list, dev_size: int = 60) -> tuple:
    """Create dev/test split with stratification by family."""
    rng = random.Random(42)
    dev, test = [], []
    by_family = defaultdict(list)
    for item in items:
        by_family[item["family"]].append(item)

    dev_per_family = dev_size // max(len(by_family), 1)
    for fam, fam_items in sorted(by_family.items()):
        shuffled = list(fam_items)
        rng.shuffle(shuffled)
        n = min(dev_per_family, len(shuffled))
        dev.extend(shuffled[:n])
        test.extend(shuffled[n:])

    return dev, test


def main():
    project_root = Path(__file__).parent.parent

    # Load full Moral Stories dataset
    ms_path = Path.home() / ".cache/huggingface/hub/datasets--demelin--moral_stories/snapshots"
    # Find the snapshot
    snapshots = list(ms_path.iterdir()) if ms_path.exists() else []
    data_path = None
    for snap in snapshots:
        candidate = snap / "data" / "moral_stories_full.jsonl"
        if candidate.exists():
            data_path = candidate
            break

    if data_path is None:
        # Try downloading
        print("Downloading Moral Stories dataset...")
        from huggingface_hub import hf_hub_download
        data_path = Path(hf_hub_download(
            "demelin/moral_stories",
            "data/moral_stories_full.jsonl",
            repo_type="dataset",
        ))

    print(f"Loading from: {data_path}")
    all_items = []
    with open(data_path) as f:
        for line in f:
            line = line.strip()
            if line:
                all_items.append(json.loads(line))
    print(f"Total Moral Stories items: {len(all_items)}")

    # Build subset
    subset = select_and_build_subset(all_items, target_size=240, seed=42)

    # Save
    benchmark_dir = project_root / "benchmark"
    benchmark_dir.mkdir(exist_ok=True)

    # Core fields only (strip ms_ tracing fields for the benchmark file)
    core_fields = [
        "item_id", "family", "source_type", "setting_type", "domain",
        "difficulty", "case_A", "case_B", "gold_heart_worse",
        "gold_morally_worse", "gold_primary_cue", "notes",
    ]

    # Save JSONL
    jsonl_path = benchmark_dir / "moral_stories_subset.jsonl"
    with open(jsonl_path, "w") as f:
        for item in subset:
            core = {k: item[k] for k in core_fields}
            f.write(json.dumps(core, ensure_ascii=False) + "\n")
    print(f"\nWrote {len(subset)} items to {jsonl_path}")

    # Save CSV
    csv_path = benchmark_dir / "moral_stories_subset.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=core_fields)
        writer.writeheader()
        for item in subset:
            writer.writerow({k: item[k] for k in core_fields})
    print(f"Wrote {len(subset)} items to {csv_path}")

    # Save full tracing version (with ms_id, ms_norm, ms_intention)
    trace_path = benchmark_dir / "moral_stories_subset_traced.jsonl"
    with open(trace_path, "w") as f:
        for item in subset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Wrote traced version to {trace_path}")

    # Create dev/test splits
    dev, test = create_splits(subset, dev_size=60)
    dev_path = benchmark_dir / "moral_stories_dev.jsonl"
    test_path = benchmark_dir / "moral_stories_test.jsonl"
    with open(dev_path, "w") as f:
        for item in dev:
            core = {k: item[k] for k in core_fields}
            f.write(json.dumps(core, ensure_ascii=False) + "\n")
    with open(test_path, "w") as f:
        for item in test:
            core = {k: item[k] for k in core_fields}
            f.write(json.dumps(core, ensure_ascii=False) + "\n")
    print(f"Dev: {len(dev)} items, Test: {len(test)} items")

    # Print summary
    print("\n--- Distribution Summary ---")
    fam_counts = Counter(i["family"] for i in subset)
    for fam, count in sorted(fam_counts.items()):
        print(f"  {fam}: {count}")

    diff_counts = Counter(i["difficulty"] for i in subset)
    print("\nDifficulty:")
    for d, c in sorted(diff_counts.items()):
        print(f"  {d}: {c}")

    dom_counts = Counter(i["domain"] for i in subset)
    print("\nDomain:")
    for d, c in sorted(dom_counts.items()):
        print(f"  {d}: {c}")

    set_counts = Counter(i["setting_type"] for i in subset)
    print("\nSetting:")
    for s, c in sorted(set_counts.items()):
        print(f"  {s}: {c}")

    hw_counts = Counter(i["gold_heart_worse"] for i in subset)
    print("\nGold heart_worse:")
    for v, c in sorted(hw_counts.items()):
        print(f"  {v}: {c}")

    cue_counts = Counter(i["gold_primary_cue"] for i in subset)
    print("\nPrimary cue:")
    for c, n in sorted(cue_counts.items()):
        print(f"  {c}: {n}")


if __name__ == "__main__":
    main()
