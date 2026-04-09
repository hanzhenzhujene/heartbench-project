#!/usr/bin/env python3
"""Validate benchmark files across legacy and v2 schemas."""

import json
import sys
from collections import Counter
from pathlib import Path

from schemas import (
    FAMILIES, SOURCE_TYPES, SETTING_TYPES, DIFFICULTIES,
    AB_VALUES, PRIMARY_CUES,
    BenchmarkItem,
)


PROFILE_BY_STEM = {
    "heartbench_240": {
        "schema": "legacy",
        "expected_total": 240,
        "items_per_family": 40,
        "require_all_families": True,
        "split_names": ["heartbench_dev.jsonl", "heartbench_test.jsonl"],
    },
    "heartbench_dev": {
        "schema": "legacy",
        "expected_total": 60,
        "items_per_family": 10,
        "require_all_families": True,
        "split_names": [],
    },
    "heartbench_test": {
        "schema": "legacy",
        "expected_total": 180,
        "items_per_family": 30,
        "require_all_families": True,
        "split_names": [],
    },
    "moral_stories_subset": {
        "schema": "legacy",
        "expected_total": 240,
        "items_per_family": 40,
        "require_all_families": True,
        "split_names": ["moral_stories_dev.jsonl", "moral_stories_test.jsonl"],
    },
    "moral_stories_dev": {
        "schema": "legacy",
        "expected_total": 60,
        "items_per_family": 10,
        "require_all_families": True,
        "split_names": [],
    },
    "moral_stories_test": {
        "schema": "legacy",
        "expected_total": 180,
        "items_per_family": 30,
        "require_all_families": True,
        "split_names": [],
    },
    "moral_stories_supported": {
        "schema": "legacy",
        "expected_total": 52,
        "items_per_family": None,
        "require_all_families": False,
        "split_names": [],
    },
    "heartbench_v2_120": {
        "schema": "v2",
        "expected_total": 120,
        "items_per_family": 20,
        "require_all_families": True,
        "split_names": ["heartbench_v2_dev.jsonl", "heartbench_v2_test.jsonl"],
    },
    "heartbench_v2_dev": {
        "schema": "v2",
        "expected_total": 30,
        "items_per_family": 5,
        "require_all_families": True,
        "split_names": [],
    },
    "heartbench_v2_test": {
        "schema": "v2",
        "expected_total": 90,
        "items_per_family": 15,
        "require_all_families": True,
        "split_names": [],
    },
}


def load_items(path: Path) -> list[dict]:
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def get_profile(path: Path, items: list[dict]) -> dict:
    stem = path.stem
    if stem in PROFILE_BY_STEM:
        return PROFILE_BY_STEM[stem]
    if items and "gold_case_A_heart_score" in items[0]:
        return {
            "schema": "v2",
            "expected_total": len(items),
            "items_per_family": None,
            "require_all_families": False,
            "split_names": [],
        }
    return {
        "schema": "legacy",
        "expected_total": len(items),
        "items_per_family": None,
        "require_all_families": False,
        "split_names": [],
    }


def validate_legacy_item(item: dict, item_label: str) -> list[str]:
    issues = []
    required_fields = [
        "item_id", "family", "source_type", "setting_type", "domain",
        "difficulty", "case_A", "case_B", "gold_heart_worse",
        "gold_morally_worse", "gold_primary_cue",
    ]
    for field in required_fields:
        if field not in item or not str(item[field]).strip():
            issues.append(f"ERROR: Item {item_label} missing field '{field}'")

    bi = BenchmarkItem.from_dict(item)
    errs = bi.validate()
    for err in errs:
        issues.append(f"ERROR: Item {item_label}: {err}")
    return issues


def validate_v2_item(item: dict, item_label: str) -> list[str]:
    issues = []
    required_fields = [
        "benchmark_version", "item_id", "source_item_id", "family", "source_type", "setting_type", "domain",
        "difficulty", "case_A", "case_B", "gold_case_A_heart_score", "gold_case_B_heart_score",
        "gold_case_A_act_score", "gold_case_B_act_score", "gold_heart_worse", "gold_act_worse",
        "dissociation_target", "gold_primary_cue",
        "label_provenance_heart_pair", "label_provenance_case_scores", "label_provenance_act_pair",
    ]
    for field in required_fields:
        if field not in item:
            issues.append(f"ERROR: Item {item_label} missing field '{field}'")

    if item.get("family") not in FAMILIES:
        issues.append(f"ERROR: Item {item_label}: invalid family {item.get('family')}")
    if item.get("source_type") not in SOURCE_TYPES:
        issues.append(f"ERROR: Item {item_label}: invalid source_type {item.get('source_type')}")
    if item.get("setting_type") not in SETTING_TYPES:
        issues.append(f"ERROR: Item {item_label}: invalid setting_type {item.get('setting_type')}")
    if item.get("difficulty") not in DIFFICULTIES:
        issues.append(f"ERROR: Item {item_label}: invalid difficulty {item.get('difficulty')}")
    if item.get("gold_heart_worse") not in AB_VALUES:
        issues.append(f"ERROR: Item {item_label}: invalid gold_heart_worse {item.get('gold_heart_worse')}")
    if item.get("gold_act_worse") not in {"A", "B", "tie"}:
        issues.append(f"ERROR: Item {item_label}: invalid gold_act_worse {item.get('gold_act_worse')}")
    if item.get("gold_primary_cue") not in PRIMARY_CUES:
        issues.append(f"ERROR: Item {item_label}: invalid gold_primary_cue {item.get('gold_primary_cue')}")
    if not isinstance(item.get("dissociation_target"), bool):
        issues.append(f"ERROR: Item {item_label}: dissociation_target must be boolean")
    if not str(item.get("benchmark_version", "")).strip():
        issues.append(f"ERROR: Item {item_label}: benchmark_version is empty")

    for field in [
        "gold_case_A_heart_score", "gold_case_B_heart_score",
        "gold_case_A_act_score", "gold_case_B_act_score",
    ]:
        value = item.get(field)
        if not isinstance(value, int) or value not in {1, 2, 3, 4, 5}:
            issues.append(f"ERROR: Item {item_label}: {field} must be an integer in 1-5")

    heart_a = item.get("gold_case_A_heart_score")
    heart_b = item.get("gold_case_B_heart_score")
    act_a = item.get("gold_case_A_act_score")
    act_b = item.get("gold_case_B_act_score")
    if isinstance(heart_a, int) and isinstance(heart_b, int):
        expected_heart = "A" if heart_a > heart_b else "B" if heart_b > heart_a else "tie"
        if item.get("gold_heart_worse") != expected_heart:
            issues.append(
                f"ERROR: Item {item_label}: gold_heart_worse={item.get('gold_heart_worse')} "
                f"does not match heart scores ({heart_a}, {heart_b})"
            )
    if isinstance(act_a, int) and isinstance(act_b, int):
        expected_act = "A" if act_a > act_b else "B" if act_b > act_a else "tie"
        if item.get("gold_act_worse") != expected_act:
            issues.append(
                f"ERROR: Item {item_label}: gold_act_worse={item.get('gold_act_worse')} "
                f"does not match act scores ({act_a}, {act_b})"
            )
    return issues


def validate_benchmark(path: Path) -> list[str]:
    """Run all validation checks. Returns list of error/warning strings."""
    issues = []
    items = load_items(path)
    profile = get_profile(path, items)
    expected_total = profile["expected_total"]
    items_per_family = profile["items_per_family"]
    require_all_families = profile["require_all_families"]
    schema = profile["schema"]

    # 1. Total count
    if len(items) != expected_total:
        issues.append(f"ERROR: Expected {expected_total} items, got {len(items)}")

    # 2. Family counts
    fam_counts = Counter(it["family"] for it in items)
    for fam in FAMILIES:
        c = fam_counts.get(fam, 0)
        if items_per_family is not None and c != items_per_family:
            issues.append(f"ERROR: Family '{fam}' has {c} items, expected {items_per_family}")
        elif require_all_families and c == 0:
            issues.append(f"ERROR: Family '{fam}' has 0 items, expected >0")
    for fam in fam_counts:
        if fam not in FAMILIES:
            issues.append(f"ERROR: Unknown family '{fam}'")

    # 3. Required fields and valid values
    for i, item in enumerate(items):
        item_label = item.get("item_id", i)
        if schema == "v2":
            issues.extend(validate_v2_item(item, item_label))
        else:
            issues.extend(validate_legacy_item(item, item_label))

    # 4. Label balance
    hw_counts = Counter(it["gold_heart_worse"] for it in items)
    for v in AB_VALUES:
        c = hw_counts.get(v, 0)
        pct = c / len(items) * 100
        if pct < 40 or pct > 60:
            issues.append(f"WARNING: gold_heart_worse='{v}' is {c} ({pct:.1f}%), target is ~50%")
        else:
            issues.append(f"INFO: gold_heart_worse='{v}': {c} ({pct:.1f}%)")

    # 5. Duplicate item IDs
    id_counts = Counter(it["item_id"] for it in items)
    dups = {k: v for k, v in id_counts.items() if v > 1}
    if dups:
        issues.append(f"ERROR: Duplicate item_ids: {dups}")

    # 6. Case length differences
    length_diffs = []
    for item in items:
        a_words = len(item["case_A"].split())
        b_words = len(item["case_B"].split())
        diff = abs(a_words - b_words)
        length_diffs.append(diff)
        if diff > 30:
            issues.append(
                f"WARNING: Item {item['item_id']} case length diff = {diff} words "
                f"(A={a_words}, B={b_words})"
            )

    avg_diff = sum(length_diffs) / len(length_diffs) if length_diffs else 0
    max_diff = max(length_diffs) if length_diffs else 0
    issues.append(f"INFO: Case length diff: avg={avg_diff:.1f}, max={max_diff}")

    # 7. Case word counts
    a_lengths = [len(it["case_A"].split()) for it in items]
    b_lengths = [len(it["case_B"].split()) for it in items]
    issues.append(
        f"INFO: Case A words: min={min(a_lengths)}, max={max(a_lengths)}, "
        f"avg={sum(a_lengths)/len(a_lengths):.1f}"
    )
    issues.append(
        f"INFO: Case B words: min={min(b_lengths)}, max={max(b_lengths)}, "
        f"avg={sum(b_lengths)/len(b_lengths):.1f}"
    )

    # 8. Difficulty distribution
    diff_counts = Counter(it["difficulty"] for it in items)
    issues.append(f"INFO: Difficulty distribution: {dict(diff_counts)}")

    # 9. Source type distribution
    src_counts = Counter(it["source_type"] for it in items)
    issues.append(f"INFO: Source distribution: {dict(src_counts)}")

    # 10. Setting type distribution
    set_counts = Counter(it["setting_type"] for it in items)
    issues.append(f"INFO: Setting distribution: {dict(set_counts)}")

    # 11. Domain distribution
    dom_counts = Counter(it["domain"] for it in items)
    issues.append(f"INFO: Domain distribution: {dict(sorted(dom_counts.items()))}")

    # 12. Primary cue distribution
    cue_counts = Counter(it["gold_primary_cue"] for it in items)
    issues.append(f"INFO: Primary cue distribution: {dict(sorted(cue_counts.items()))}")

    # 13. Near-duplicate check (simple: check if any two case_A texts are identical)
    case_a_set = set()
    for item in items:
        if item["case_A"] in case_a_set:
            issues.append(f"WARNING: Duplicate case_A text in item {item['item_id']}")
        case_a_set.add(item["case_A"])

    # 14. Cue-word imbalance check
    cue_words = ["cruel", "kind", "selfish", "loving", "arrogant", "humble",
                 "generous", "greedy", "honest", "dishonest"]
    for word in cue_words:
        a_count = sum(1 for it in items if word.lower() in it["case_A"].lower())
        b_count = sum(1 for it in items if word.lower() in it["case_B"].lower())
        if a_count + b_count > 5:
            issues.append(
                f"INFO: Cue word '{word}' appears {a_count} times in case_A, "
                f"{b_count} times in case_B"
            )

    return issues


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate HeartBench benchmark files")
    parser.add_argument("--benchmark", type=str, default=None,
                        help="Path to benchmark file (default: heartbench_240.jsonl)")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent

    if args.benchmark:
        benchmark_path = Path(args.benchmark)
        if not benchmark_path.is_absolute():
            benchmark_path = project_root / benchmark_path
    else:
        benchmark_path = project_root / "benchmark" / "heartbench_240.jsonl"

    if not benchmark_path.exists():
        print(f"Benchmark file not found: {benchmark_path}")
        sys.exit(1)

    print(f"Validating: {benchmark_path}")
    print("=" * 60)

    issues = validate_benchmark(benchmark_path)

    errors = [i for i in issues if i.startswith("ERROR")]
    warnings = [i for i in issues if i.startswith("WARNING")]
    infos = [i for i in issues if i.startswith("INFO")]

    for issue in errors:
        print(issue)
    for issue in warnings:
        print(issue)
    for issue in infos:
        print(issue)

    print("=" * 60)
    print(f"Errors: {len(errors)}, Warnings: {len(warnings)}, Info: {len(infos)}")

    if errors:
        print("\nBenchmark FAILED validation.")
        sys.exit(1)
    else:
        print("\nBenchmark PASSED validation.")

    # Also validate known sibling splits for canonical stems
    stem = benchmark_path.stem
    bench_dir = benchmark_path.parent
    split_names = PROFILE_BY_STEM.get(stem, {}).get("split_names", [])

    for split_name in split_names:
        split_path = bench_dir / split_name
        if split_path.exists():
            split_items = load_items(split_path)
            print(f"\n{split_name}: {len(split_items)} items")
            split_fams = Counter(it["family"] for it in split_items)
            print(f"  Families: {dict(sorted(split_fams.items()))}")


if __name__ == "__main__":
    main()
