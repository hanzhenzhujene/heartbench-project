#!/usr/bin/env python3
"""Build corrected benchmark artifacts for the order-balanced setup."""

import json
from collections import Counter
from pathlib import Path

from utils import load_jsonl, save_benchmark, PROJECT_ROOT

EXPLICIT_MOTIVE_MARKERS = [
    "because",
    "so that",
    "in order to",
    "hoping",
    "wanting",
    "trying to",
    "to impress",
    "to help",
    "to hurt",
    "to get",
    "so he can",
    "so she can",
    "mainly because",
    "primarily because",
    "genuinely",
    "privately",
    "expecting",
    "because they",
    "because he",
    "because she",
]


def has_explicit_motive_support(item: dict) -> bool:
    text = f"{item['case_A']} {item['case_B']}".lower()
    return any(marker in text for marker in EXPLICIT_MOTIVE_MARKERS)


def build_moral_stories_supported() -> list[dict]:
    traced_path = PROJECT_ROOT / "materials" / "benchmark" / "moral_stories_subset_traced.jsonl"
    if not traced_path.exists():
        raise FileNotFoundError(f"Missing traced Moral Stories subset: {traced_path}")

    traced_items = load_jsonl(traced_path)
    supported = [item for item in traced_items if has_explicit_motive_support(item)]

    benchmark_dir = PROJECT_ROOT / "materials" / "benchmark"
    benchmark_dir.mkdir(exist_ok=True)

    core_fields = [
        "item_id", "family", "source_type", "setting_type", "domain",
        "difficulty", "case_A", "case_B", "gold_heart_worse",
        "gold_morally_worse", "gold_primary_cue", "notes",
    ]

    core_items = [{field: item[field] for field in core_fields} for item in supported]
    save_benchmark(core_items, benchmark_dir / "moral_stories_supported.jsonl")
    save_benchmark(supported, benchmark_dir / "moral_stories_supported_traced.jsonl")

    return supported


def main():
    supported = build_moral_stories_supported()
    print(f"Wrote supported Moral Stories subset: {len(supported)} items")
    print(f"Family distribution: {dict(sorted(Counter(item['family'] for item in supported).items()))}")
    print(f"Cue distribution: {dict(sorted(Counter(item['gold_primary_cue'] for item in supported).items()))}")


if __name__ == "__main__":
    main()
