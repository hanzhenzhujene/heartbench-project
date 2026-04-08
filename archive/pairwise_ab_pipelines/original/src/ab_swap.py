#!/usr/bin/env python3
"""Generate A/B swapped version of the benchmark for position-bias evaluation."""

import json
from pathlib import Path


def swap_item(item: dict) -> dict:
    """Swap case A and case B, flipping gold labels accordingly."""
    swap_map = {"A": "B", "B": "A"}
    swapped = dict(item)
    swapped["item_id"] = item["item_id"] + "_swap"
    swapped["case_A"] = item["case_B"]
    swapped["case_B"] = item["case_A"]
    swapped["gold_heart_worse"] = swap_map[item["gold_heart_worse"]]
    swapped["gold_morally_worse"] = swap_map[item["gold_morally_worse"]]
    swapped["notes"] = (item.get("notes", "") + " [A/B swapped]").strip()
    return swapped


def create_swapped_benchmark(input_path: Path, output_path: Path) -> int:
    """Create a fully A/B-swapped version of the benchmark."""
    items = []
    with open(input_path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))

    swapped = [swap_item(item) for item in items]

    with open(output_path, "w") as f:
        for item in swapped:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return len(swapped)


def main():
    project_root = Path(__file__).parent.parent
    benchmark_dir = project_root / "benchmark"

    swap_files = [
        "heartbench_240.jsonl", "heartbench_dev.jsonl", "heartbench_test.jsonl",
        "moral_stories_subset.jsonl", "moral_stories_dev.jsonl", "moral_stories_test.jsonl",
    ]
    for name in swap_files:
        input_path = benchmark_dir / name
        if not input_path.exists():
            continue
        output_name = name.replace(".jsonl", "_swapped.jsonl")
        output_path = benchmark_dir / output_name
        n = create_swapped_benchmark(input_path, output_path)
        print(f"Created {output_path} ({n} items)")


if __name__ == "__main__":
    main()
