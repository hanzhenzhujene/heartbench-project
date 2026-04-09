#!/usr/bin/env python3
"""Audit experiment plans, prompts, benchmarks, and result completeness."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import yaml

from utils import PROJECT_ROOT, load_jsonl


def load_yaml(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def prompt_stats(paths: list[Path]) -> list[dict]:
    stats = []
    for path in paths:
        text = path.read_text().strip()
        stats.append(
            {
                "name": path.name,
                "words": len(text.split()),
                "chars": len(text),
                "lines": len(text.splitlines()),
            }
        )
    return stats


def benchmark_summary(path: Path) -> dict:
    items = load_jsonl(path)
    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "n_items": len(items),
        "families": dict(sorted(Counter(item["family"] for item in items).items())),
        "gold_heart_worse": dict(sorted(Counter(item["gold_heart_worse"] for item in items).items())),
        "gold_act_worse": dict(sorted(Counter(item.get("gold_act_worse", "legacy") for item in items).items())),
        "dissociation_target_n": sum(1 for item in items if item.get("dissociation_target")),
        "benchmark_versions": sorted({item.get("benchmark_version", "legacy") for item in items}),
        "label_provenance_case_scores": sorted({item.get("label_provenance_case_scores", "legacy") for item in items}),
        "label_provenance_heart_pair": sorted({item.get("label_provenance_heart_pair", "legacy") for item in items}),
    }


def result_completeness(results_dir: Path, models: list[str], conditions: list[str]) -> dict:
    present = {}
    for model in models:
        short = model.split("/")[-1]
        for condition in conditions:
            path = results_dir / f"{short}_{condition}.jsonl"
            present[f"{short}/{condition}"] = path.exists()
    return present


def group_completeness(base_results_root: Path, groups: dict) -> dict:
    status = {}
    for group_name, group_cfg in groups.items():
        results_dir = base_results_root / group_cfg["benchmark"] / "main"
        status[group_name] = result_completeness(
            results_dir,
            group_cfg["models"],
            group_cfg["conditions"],
        )
    return status


def audit() -> dict:
    dual_exp = load_yaml(PROJECT_ROOT / "materials" / "research" / "configs" / "experiment_dual_logit_v2.yaml")
    dual_prompts = load_yaml(PROJECT_ROOT / "materials" / "research" / "configs" / "prompts_dual_logit_v2.yaml")
    structured_exp = load_yaml(PROJECT_ROOT / "materials" / "research" / "configs" / "experiment_structured_v2.yaml")
    structured_prompts = load_yaml(PROJECT_ROOT / "materials" / "research" / "configs" / "prompts_structured_v2.yaml")

    dual_prompt_paths = [PROJECT_ROOT / cond["file"] for cond in dual_prompts["conditions"]]
    structured_prompt_paths = [PROJECT_ROOT / cond["file"] for cond in structured_prompts["conditions"]]

    heartbench_v2_path = PROJECT_ROOT / dual_exp["benchmarks"]["heartbench_v2"]["benchmark_file"]
    heartbench_v2_dev_path = PROJECT_ROOT / dual_exp["benchmarks"]["heartbench_v2_dev"]["benchmark_file"]
    results_dir = PROJECT_ROOT / "materials/results/dual_logit_v2" / "heartbench_v2" / "main"

    dual_condition_ids = [cond["id"] for cond in dual_prompts["conditions"]]
    structured_condition_ids = [cond["id"] for cond in structured_prompts["conditions"]]

    heartbench_v2_summary = benchmark_summary(heartbench_v2_path)
    heartbench_v2_dev_summary = benchmark_summary(heartbench_v2_dev_path)

    warnings = []
    if dual_exp["main"]["conditions"] != dual_condition_ids:
        warnings.append("Dual-logit experiment conditions do not exactly match prompt config condition order.")
    if structured_exp["main"]["conditions"] != structured_condition_ids:
        warnings.append("Structured-v2 experiment conditions do not exactly match prompt config condition order.")

    dual_stats = prompt_stats(dual_prompt_paths)
    max_words = max(row["words"] for row in dual_stats)
    min_words = min(row["words"] for row in dual_stats)
    if max_words - min_words > 50:
        warnings.append(
            "Dual-logit prompt length spread is large; C0 vs scaffold comparisons combine intervention content and prompt length."
        )

    if "family_template_v1" in heartbench_v2_summary["label_provenance_case_scores"]:
        warnings.append(
            "HeartBench-v2 case-level 1-5 scores are still template-assigned rather than freshly human-annotated."
        )

    execution_groups = dual_exp.get("execution_groups", {})
    group_status = group_completeness(PROJECT_ROOT / "materials/results/dual_logit_v2", execution_groups)
    missing_by_group = {}
    for group_name, completeness in group_status.items():
        missing = [label for label, done in completeness.items() if not done]
        if missing:
            missing_by_group[group_name] = missing

    if missing_by_group:
        warnings.append(
            "Some configured execution groups are incomplete: "
            + "; ".join(f"{group}: {', '.join(labels)}" for group, labels in missing_by_group.items())
        )

    return {
        "dual_logit": {
            "config_name": dual_exp["experiment"]["name"],
            "default_benchmark": dual_exp["default_benchmark"],
            "conditions": dual_condition_ids,
            "models": dual_exp["main"]["models"],
            "prompt_stats": dual_stats,
            "execution_groups": execution_groups,
        },
        "structured_v2": {
            "config_name": structured_exp["experiment"]["name"],
            "default_benchmark": structured_exp["default_benchmark"],
            "conditions": structured_condition_ids,
            "prompt_stats": prompt_stats(structured_prompt_paths),
        },
        "benchmarks": {
            "heartbench_v2": heartbench_v2_summary,
            "heartbench_v2_dev": heartbench_v2_dev_summary,
        },
        "results": {
            "results_dir": str(results_dir.relative_to(PROJECT_ROOT)),
            "completeness": group_status,
        },
        "warnings": warnings,
    }


def to_markdown(audit_obj: dict) -> str:
    lines = ["# Experiment Settings Audit", ""]

    lines.append("## Dual-Logit V2")
    dual = audit_obj["dual_logit"]
    lines.append(f"- config: `{dual['config_name']}`")
    lines.append(f"- default benchmark: `{dual['default_benchmark']}`")
    lines.append(f"- conditions: `{', '.join(dual['conditions'])}`")
    lines.append(f"- models: `{', '.join(dual['models'])}`")
    lines.append("- execution groups:")
    for group_name, group_cfg in dual["execution_groups"].items():
        lines.append(
            f"  - `{group_name}`: benchmark=`{group_cfg['benchmark']}`, "
            f"models=`{', '.join(group_cfg['models'])}`, conditions=`{', '.join(group_cfg['conditions'])}`"
        )
    lines.append("- prompt lengths:")
    for row in dual["prompt_stats"]:
        lines.append(
            f"  - `{row['name']}`: {row['words']} words, {row['chars']} chars, {row['lines']} lines"
        )
    lines.append("")

    lines.append("## Structured V2")
    structured = audit_obj["structured_v2"]
    lines.append(f"- config: `{structured['config_name']}`")
    lines.append(f"- default benchmark: `{structured['default_benchmark']}`")
    lines.append(f"- conditions: `{', '.join(structured['conditions'])}`")
    lines.append("")

    lines.append("## Benchmarks")
    for name, summary in audit_obj["benchmarks"].items():
        lines.append(f"### {name}")
        lines.append(f"- path: `{summary['path']}`")
        lines.append(f"- items: `{summary['n_items']}`")
        lines.append(f"- families: `{summary['families']}`")
        lines.append(f"- gold_heart_worse: `{summary['gold_heart_worse']}`")
        lines.append(f"- gold_act_worse: `{summary['gold_act_worse']}`")
        lines.append(f"- dissociation_target_n: `{summary['dissociation_target_n']}`")
        lines.append(f"- benchmark_versions: `{summary['benchmark_versions']}`")
        lines.append(f"- label_provenance_case_scores: `{summary['label_provenance_case_scores']}`")
        lines.append(f"- label_provenance_heart_pair: `{summary['label_provenance_heart_pair']}`")
        lines.append("")

    lines.append("## Results Completeness")
    lines.append(f"- results dir: `{audit_obj['results']['results_dir']}`")
    for group_name, completeness in audit_obj["results"]["completeness"].items():
        lines.append(f"- group `{group_name}`:")
        for label, done in completeness.items():
            lines.append(f"  - `{label}`: {'present' if done else 'missing'}")
    lines.append("")

    lines.append("## Warnings")
    if audit_obj["warnings"]:
        for warning in audit_obj["warnings"]:
            lines.append(f"- {warning}")
    else:
        lines.append("- none")
    lines.append("")

    return "\n".join(lines)


def main():
    audit_obj = audit()
    out_path = PROJECT_ROOT / "reports" / "experiment_settings_audit.md"
    out_path.write_text(to_markdown(audit_obj))
    print(f"Saved audit report to {out_path}")
    if audit_obj["warnings"]:
        print("Warnings:")
        for warning in audit_obj["warnings"]:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
