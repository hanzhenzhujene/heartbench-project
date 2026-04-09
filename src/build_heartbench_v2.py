#!/usr/bin/env python3
"""Build a high-precision HeartBench-v2 benchmark with explicit heart/act separation."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from utils import PROJECT_ROOT, load_jsonl, save_benchmark

SOURCE_BENCHMARK = PROJECT_ROOT / "benchmark" / "heartbench_240.jsonl"
OUTPUT_BENCHMARK = PROJECT_ROOT / "benchmark" / "heartbench_v2_120.jsonl"
OUTPUT_DEV = PROJECT_ROOT / "benchmark" / "heartbench_v2_dev.jsonl"
OUTPUT_TEST = PROJECT_ROOT / "benchmark" / "heartbench_v2_test.jsonl"
BENCHMARK_VERSION = "heartbench_v2.1"

ITEMS_PER_FAMILY = 20
FAMILY_ORDER = [
    "same_act_different_motive",
    "same_restraint_different_posture",
    "same_correction_different_heart",
    "good_act_corrupt_motive",
    "flawed_act_benevolent_motive",
    "mixed_motive_hard",
]

EXPLICIT_MOTIVE_MARKERS = [
    "because",
    "so that",
    "in order to",
    "hoping",
    "wanting",
    "trying to",
    "mainly because",
    "primarily because",
    "privately",
    "expecting",
    "so he can",
    "so she can",
    "because they",
    "because he",
    "because she",
    "only because",
    "partly because",
]

STRONG_LEXICAL_GIVEAWAYS = [
    "cruel",
    "kind",
    "selfish",
    "loving",
    "arrogant",
    "humble",
    "evil",
    "wicked",
]

TOKEN_RE = re.compile(r"[a-z']+")


def tokenize(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def lexical_overlap(case_a: str, case_b: str) -> float:
    tokens_a = tokenize(case_a)
    tokens_b = tokenize(case_b)
    if not tokens_a and not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / max(len(tokens_a | tokens_b), 1)


def marker_count(text: str) -> int:
    text_lower = text.lower()
    return sum(1 for marker in EXPLICIT_MOTIVE_MARKERS if marker in text_lower)


def strong_cue_penalty(text: str) -> int:
    text_lower = text.lower()
    return sum(1 for cue in STRONG_LEXICAL_GIVEAWAYS if cue in text_lower)


def selection_score(item: dict) -> tuple[float, int, float, int, str]:
    case_a = item["case_A"]
    case_b = item["case_B"]
    marker_cases = int(marker_count(case_a) > 0) + int(marker_count(case_b) > 0)
    overlap = lexical_overlap(case_a, case_b)
    length_gap = abs(len(case_a.split()) - len(case_b.split()))
    penalty = strong_cue_penalty(case_a + " " + case_b)

    score = 0.0
    score += 2.5 * marker_cases
    score += 1.25 * overlap
    score -= 0.05 * length_gap
    score -= 1.0 * penalty

    # Families 1/2/6 should rely more heavily on explicit motive evidence.
    if item["family"] in {
        "same_act_different_motive",
        "same_restraint_different_posture",
        "mixed_motive_hard",
    }:
        score += 0.5 * marker_count(case_a + " " + case_b)

    # Families 3/5 benefit from outwardly matched cases.
    if item["family"] in {
        "same_correction_different_heart",
        "flawed_act_benevolent_motive",
    }:
        score += 0.5 * overlap

    return (score, marker_cases, overlap, -length_gap, item["item_id"])


def family_score_template(family: str) -> dict[str, int | str | bool]:
    templates = {
        "same_act_different_motive": {
            "worse_heart": 5,
            "better_heart": 2,
            "worse_act": 3,
            "better_act": 3,
            "gold_act_worse": "tie",
            "dissociation_target": True,
        },
        "same_restraint_different_posture": {
            "worse_heart": 4,
            "better_heart": 2,
            "worse_act": 2,
            "better_act": 2,
            "gold_act_worse": "tie",
            "dissociation_target": True,
        },
        "same_correction_different_heart": {
            "worse_heart": 5,
            "better_heart": 2,
            "worse_act": 4,
            "better_act": 2,
            "gold_act_worse": "worse_case",
            "dissociation_target": False,
        },
        "good_act_corrupt_motive": {
            "worse_heart": 5,
            "better_heart": 2,
            "worse_act": 2,
            "better_act": 2,
            "gold_act_worse": "tie",
            "dissociation_target": True,
        },
        "flawed_act_benevolent_motive": {
            "worse_heart": 4,
            "better_heart": 2,
            "worse_act": 2,
            "better_act": 4,
            "gold_act_worse": "better_heart_case",
            "dissociation_target": True,
        },
        "mixed_motive_hard": {
            "worse_heart": 4,
            "better_heart": 3,
            "worse_act": 3,
            "better_act": 3,
            "gold_act_worse": "tie",
            "dissociation_target": True,
        },
    }
    return templates[family]


def assign_dual_scores(item: dict) -> dict:
    template = family_score_template(item["family"])
    worse_case = item["gold_heart_worse"]
    better_case = "B" if worse_case == "A" else "A"

    case_scores: dict[str, dict[str, int]] = {
        worse_case: {
            "heart": int(template["worse_heart"]),
            "act": int(template["worse_act"]),
        },
        better_case: {
            "heart": int(template["better_heart"]),
            "act": int(template["better_act"]),
        },
    }

    gold_act_worse_template = str(template["gold_act_worse"])
    if gold_act_worse_template == "tie":
        gold_act_worse = "tie"
    elif gold_act_worse_template == "worse_case":
        gold_act_worse = worse_case
    elif gold_act_worse_template == "better_heart_case":
        gold_act_worse = better_case
    else:
        raise ValueError(f"Unknown gold_act_worse template: {gold_act_worse_template}")

    return {
        "gold_case_A_heart_score": case_scores["A"]["heart"],
        "gold_case_B_heart_score": case_scores["B"]["heart"],
        "gold_case_A_act_score": case_scores["A"]["act"],
        "gold_case_B_act_score": case_scores["B"]["act"],
        "gold_heart_worse": worse_case,
        "gold_act_worse": gold_act_worse,
        "dissociation_target": bool(template["dissociation_target"]),
    }


def select_items(items: list[dict]) -> list[dict]:
    by_family: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_family[item["family"]].append(item)

    selected: list[dict] = []
    for family in FAMILY_ORDER:
        ranked = sorted(
            by_family[family],
            key=selection_score,
            reverse=True,
        )
        chosen = ranked[:ITEMS_PER_FAMILY]
        if len(chosen) != ITEMS_PER_FAMILY:
            raise ValueError(
                f"Expected {ITEMS_PER_FAMILY} items for {family}, got {len(chosen)}"
            )
        selected.extend(chosen)

    return selected


def build_heartbench_v2() -> list[dict]:
    if not SOURCE_BENCHMARK.exists():
        raise FileNotFoundError(f"Missing source benchmark: {SOURCE_BENCHMARK}")

    source_items = load_jsonl(SOURCE_BENCHMARK)
    selected = select_items(source_items)

    built = []
    for item in selected:
        scored = assign_dual_scores(item)
        marker_cases = int(marker_count(item["case_A"]) > 0) + int(marker_count(item["case_B"]) > 0)
        built.append(
            {
                "benchmark_version": BENCHMARK_VERSION,
                "item_id": item["item_id"].replace("hb_", "hbv2_"),
                "source_item_id": item["item_id"],
                "family": item["family"],
                "source_type": item["source_type"],
                "setting_type": item["setting_type"],
                "domain": item["domain"],
                "difficulty": item["difficulty"],
                "case_A": item["case_A"],
                "case_B": item["case_B"],
                "gold_case_A_heart_score": scored["gold_case_A_heart_score"],
                "gold_case_B_heart_score": scored["gold_case_B_heart_score"],
                "gold_case_A_act_score": scored["gold_case_A_act_score"],
                "gold_case_B_act_score": scored["gold_case_B_act_score"],
                "gold_heart_worse": scored["gold_heart_worse"],
                "gold_act_worse": scored["gold_act_worse"],
                "dissociation_target": scored["dissociation_target"],
                "label_provenance_heart_pair": "inherited_from_heartbench_240",
                "label_provenance_case_scores": "family_template_v1",
                "label_provenance_act_pair": "derived_from_family_template_v1",
                "gold_primary_cue": item["gold_primary_cue"],
                "selection_marker_cases": marker_cases,
                "selection_lexical_overlap": round(lexical_overlap(item["case_A"], item["case_B"]), 3),
                "notes": item.get("notes", ""),
            }
        )

    save_benchmark(built, OUTPUT_BENCHMARK)
    dev_items = []
    test_items = []
    by_family: dict[str, list[dict]] = defaultdict(list)
    for item in built:
        by_family[item["family"]].append(item)
    for family in FAMILY_ORDER:
        family_items = sorted(by_family[family], key=lambda row: row["item_id"])
        dev_items.extend(family_items[:5])
        test_items.extend(family_items[5:])

    save_benchmark(dev_items, OUTPUT_DEV)
    save_benchmark(test_items, OUTPUT_TEST)
    return built


def main():
    built = build_heartbench_v2()
    print(f"Wrote {len(built)} items to {OUTPUT_BENCHMARK}")
    print("Family distribution:", dict(sorted(Counter(item["family"] for item in built).items())))
    print(
        "Dissociation targets:",
        sum(1 for item in built if item["dissociation_target"]),
        "/",
        len(built),
    )
    print(
        "Act label distribution:",
        dict(sorted(Counter(item["gold_act_worse"] for item in built).items())),
    )
    print(f"Saved dev split to {OUTPUT_DEV} ({30} items)")
    print(f"Saved test split to {OUTPUT_TEST} ({90} items)")


if __name__ == "__main__":
    main()
