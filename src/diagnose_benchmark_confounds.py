#!/usr/bin/env python3
"""Generate a focused audit of benchmark and evaluation confounds."""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

from utils import load_jsonl, PROJECT_ROOT

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
STOPWORDS = {
    "a", "an", "the", "to", "of", "and", "or", "is", "are", "was", "were",
    "in", "on", "at", "for", "with", "that", "this", "it", "as", "but",
    "their", "his", "her", "they", "them", "he", "she",
}


def explicit_motive_supported(item: dict) -> bool:
    text = f"{item['case_A']} {item['case_B']}".lower()
    return any(marker in text for marker in EXPLICIT_MOTIVE_MARKERS)


def jaccard(case_a: str, case_b: str) -> float:
    toks_a = {tok for tok in re.findall(r"[a-z']+", case_a.lower()) if tok not in STOPWORDS}
    toks_b = {tok for tok in re.findall(r"[a-z']+", case_b.lower()) if tok not in STOPWORDS}
    if not toks_a and not toks_b:
        return 0.0
    return len(toks_a & toks_b) / len(toks_a | toks_b)


def benchmark_summary(label: str, items: list[dict], traced_items: Optional[list[dict]] = None) -> list[str]:
    heart_equals_moral = sum(
        item["gold_heart_worse"] == item["gold_morally_worse"] for item in items
    )
    explicit_supported = sum(explicit_motive_supported(item) for item in items)
    overlap_by_family = defaultdict(list)
    suspicious_same_act = []
    for item in items:
        overlap = jaccard(item["case_A"], item["case_B"])
        overlap_by_family[item["family"]].append(overlap)
        if item["family"] == "same_act_different_motive" and overlap < 0.55:
            suspicious_same_act.append((item["item_id"], overlap))

    lines = [
        f"### {label}",
        f"- items: {len(items)}",
        f"- heart==moral labels: {heart_equals_moral}/{len(items)}",
        f"- explicit motive support in shipped case text: {explicit_supported}/{len(items)}",
        f"- suspicious same_act_different_motive items with low lexical overlap: {len(suspicious_same_act)}",
    ]

    if traced_items is not None:
        omitted_intentions = sum(
            item["ms_intention"].strip().rstrip(".") not in item["case_A"]
            and item["ms_intention"].strip().rstrip(".") not in item["case_B"]
            for item in traced_items
        )
        lines.append(f"- traced intentions omitted from final case text: {omitted_intentions}/{len(traced_items)}")

    lines.append("- average lexical overlap by family:")
    for family, values in sorted(overlap_by_family.items()):
        lines.append(f"  - {family}: {sum(values) / len(values):.3f}")

    if suspicious_same_act:
        sample = ", ".join(item_id for item_id, _ in suspicious_same_act[:8])
        lines.append(f"- sample low-overlap same_act items: {sample}")

    return lines


def result_summary(label: str, benchmark_items: list[dict], results: list[dict]) -> list[str]:
    gold = {item["item_id"]: item for item in benchmark_items}
    lines = [f"### {label}"]

    by_model_condition = defaultdict(list)
    for row in results:
        if row["item_id"] in gold:
            by_model_condition[(row["model"], row["condition"])].append(row)

    for (model, condition), rows in sorted(by_model_condition.items()):
        parsed = [row for row in rows if row.get("heart_worse")]
        pred_counts = Counter(row["heart_worse"] for row in parsed)
        reason_counts = Counter(row.get("reason_focus") for row in parsed)
        acc_by_reason = defaultdict(list)
        for row in parsed:
            correct = row["heart_worse"] == gold[row["item_id"]]["gold_heart_worse"]
            acc_by_reason[row.get("reason_focus", "unknown")].append(correct)
        lines.append(f"- {model}/{condition}:")
        if parsed:
            total = len(parsed)
            lines.append(
                f"  - answer distribution: "
                f"A={pred_counts.get('A', 0) / total:.3f}, B={pred_counts.get('B', 0) / total:.3f}"
            )
            if reason_counts:
                top_reason = ", ".join(
                    f"{reason}={count / total:.3f}" for reason, count in reason_counts.most_common(3)
                )
                lines.append(f"  - top reason_focus rates: {top_reason}")
            for reason, values in sorted(acc_by_reason.items()):
                lines.append(f"  - heart accuracy when reason_focus={reason}: {sum(values) / len(values):.3f} (n={len(values)})")
        else:
            lines.append("  - no parsed outputs")

    return lines


def write_report(lines: list[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write("# Benchmark Confound Audit\n\n")
        f.write("\n".join(lines))
        f.write("\n")


def main():
    report_lines = []

    ms = load_jsonl(PROJECT_ROOT / "benchmark" / "moral_stories_subset.jsonl")
    ms_traced = load_jsonl(PROJECT_ROOT / "benchmark" / "moral_stories_subset_traced.jsonl")
    hb = load_jsonl(PROJECT_ROOT / "benchmark" / "heartbench_240.jsonl")

    report_lines.extend(benchmark_summary("Moral Stories Subset", ms, ms_traced))
    report_lines.append("")
    report_lines.extend(benchmark_summary("HeartBench-240", hb))

    ms_results_path = PROJECT_ROOT / "results" / "moral_stories" / "main" / "all_results.jsonl"
    if ms_results_path.exists():
        report_lines.append("")
        ms_results = load_jsonl(ms_results_path)
        report_lines.extend(result_summary("Moral Stories Main Results", ms, ms_results))

    hb_results_path = PROJECT_ROOT / "results" / "heartbench" / "main" / "all_results.jsonl"
    if hb_results_path.exists():
        report_lines.append("")
        hb_results = load_jsonl(hb_results_path)
        report_lines.extend(result_summary("HeartBench Main Results", hb, hb_results))

    report_path = PROJECT_ROOT / "reports" / "benchmark_confound_audit.md"
    write_report(report_lines, report_path)
    print(f"Wrote audit report to {report_path}")


if __name__ == "__main__":
    main()
