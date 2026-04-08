#!/usr/bin/env python3
"""Validate HeartBench-240 benchmark files."""

import json
import sys
from collections import Counter
from pathlib import Path

from schemas import (
    FAMILIES, SOURCE_TYPES, SETTING_TYPES, DIFFICULTIES,
    AB_VALUES, PRIMARY_CUES, ITEMS_PER_FAMILY, TOTAL_ITEMS,
    BenchmarkItem,
)


def load_items(path: Path) -> list[dict]:
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def validate_benchmark(path: Path) -> list[str]:
    """Run all validation checks. Returns list of error/warning strings."""
    issues = []
    items = load_items(path)

    # 1. Total count
    if len(items) != TOTAL_ITEMS:
        issues.append(f"ERROR: Expected {TOTAL_ITEMS} items, got {len(items)}")

    # 2. Family counts
    fam_counts = Counter(it["family"] for it in items)
    for fam in FAMILIES:
        c = fam_counts.get(fam, 0)
        if c != ITEMS_PER_FAMILY:
            issues.append(f"ERROR: Family '{fam}' has {c} items, expected {ITEMS_PER_FAMILY}")
    for fam in fam_counts:
        if fam not in FAMILIES:
            issues.append(f"ERROR: Unknown family '{fam}'")

    # 3. Required fields and valid values
    required_fields = [
        "item_id", "family", "source_type", "setting_type", "domain",
        "difficulty", "case_A", "case_B", "gold_heart_worse",
        "gold_morally_worse", "gold_primary_cue",
    ]
    for i, item in enumerate(items):
        for field in required_fields:
            if field not in item or not str(item[field]).strip():
                issues.append(f"ERROR: Item {i} missing field '{field}'")

        bi = BenchmarkItem.from_dict(item)
        errs = bi.validate()
        for e in errs:
            issues.append(f"ERROR: Item {item.get('item_id', i)}: {e}")

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

    # Also validate splits - infer split names from benchmark name
    stem = benchmark_path.stem  # e.g. heartbench_240 or moral_stories_subset
    bench_dir = benchmark_path.parent
    if "heartbench" in stem:
        split_names = ["heartbench_dev.jsonl", "heartbench_test.jsonl"]
    elif "moral_stories" in stem:
        split_names = ["moral_stories_dev.jsonl", "moral_stories_test.jsonl"]
    else:
        split_names = []

    for split_name in split_names:
        split_path = bench_dir / split_name
        if split_path.exists():
            split_items = load_items(split_path)
            print(f"\n{split_name}: {len(split_items)} items")
            split_fams = Counter(it["family"] for it in split_items)
            print(f"  Families: {dict(sorted(split_fams.items()))}")


if __name__ == "__main__":
    main()
