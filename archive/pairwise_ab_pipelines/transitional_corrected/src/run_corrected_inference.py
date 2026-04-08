#!/usr/bin/env python3
"""Run the corrected order-balanced heart-only evaluation."""

import argparse
import time
from pathlib import Path

import torch
from tqdm import tqdm

from model_inference_utils import load_model_and_tokenizer, generate_response, attempt_repair
from utils import (
    PROJECT_ROOT,
    ensure_dir,
    get_config,
    load_benchmark,
    load_prompt,
    parse_json_output,
    render_prompt,
    save_jsonl,
)

SWAP_MAP = {"A": "B", "B": "A"}
VALID_FOCUS = {"outward_act", "motive", "consequence", "rule", "unclear"}


def validate_heart_only(parsed: dict) -> bool:
    if not isinstance(parsed, dict):
        return False
    if parsed.get("heart_worse") not in SWAP_MAP:
        return False
    if parsed.get("reason_focus") not in VALID_FOCUS:
        return False
    return True


def run_order(
    model,
    tokenizer,
    item: dict,
    prompt_template: str,
    repair_prompt_text: str,
    condition_id: str,
    model_name: str,
    order: str,
    max_new_tokens: int,
) -> dict:
    case_a = item["case_A"] if order == "original" else item["case_B"]
    case_b = item["case_B"] if order == "original" else item["case_A"]
    prompt = render_prompt(prompt_template, case_a, case_b)

    raw_output = generate_response(model, tokenizer, prompt, max_new_tokens)
    parsed = parse_json_output(raw_output)
    parse_ok = parsed is not None and validate_heart_only(parsed)

    repair_attempted = False
    repair_success = False

    if not parse_ok:
        repair_attempted = True
        repair_output = attempt_repair(
            model,
            tokenizer,
            prompt,
            raw_output,
            repair_prompt_text,
            max_new_tokens,
        )
        parsed = parse_json_output(repair_output)
        if parsed is not None and validate_heart_only(parsed):
            repair_success = True
            raw_output = raw_output + " [REPAIRED] " + repair_output
        else:
            parsed = None

    heart_worse = parsed.get("heart_worse") if parsed else None
    normalized = None
    if heart_worse is not None:
        normalized = heart_worse if order == "original" else SWAP_MAP[heart_worse]

    return {
        "item_id": item["item_id"],
        "model": model_name,
        "condition": condition_id,
        "order": order,
        "raw_output": raw_output,
        "heart_worse": heart_worse,
        "normalized_heart_worse": normalized,
        "reason_focus": parsed.get("reason_focus") if parsed else None,
        "parse_success": parse_ok or repair_success,
        "repair_attempted": repair_attempted,
        "repair_success": repair_success,
    }


def run_condition(
    model,
    tokenizer,
    items: list[dict],
    prompt_template: str,
    repair_prompt_text: str,
    condition_id: str,
    model_name: str,
    max_new_tokens: int,
) -> list[dict]:
    results = []
    for item in tqdm(items, desc=f"{model_name}/{condition_id}"):
        results.append(
            run_order(
                model,
                tokenizer,
                item,
                prompt_template,
                repair_prompt_text,
                condition_id,
                model_name,
                "original",
                max_new_tokens,
            )
        )
        results.append(
            run_order(
                model,
                tokenizer,
                item,
                prompt_template,
                repair_prompt_text,
                condition_id,
                model_name,
                "swapped",
                max_new_tokens,
            )
        )
    return results


def resolve_benchmark_path(benchmark_name: str) -> tuple[Path, str]:
    experiment_config = get_config("experiment_corrected")
    benchmarks = experiment_config["benchmarks"]
    if benchmark_name not in benchmarks:
        benchmark_name = experiment_config["default_benchmark"]
    return PROJECT_ROOT / benchmarks[benchmark_name]["benchmark_file"], benchmark_name


def main():
    parser = argparse.ArgumentParser(description="Run corrected heart-only inference")
    parser.add_argument(
        "--benchmark",
        type=str,
        default=None,
        help="Benchmark to use from experiment_corrected.yaml, or 'both'",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help="Models to run",
    )
    parser.add_argument(
        "--conditions",
        nargs="+",
        default=None,
        help="Conditions to run",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=None,
        help="Max new tokens for generation",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional item limit for a quick sanity run",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Optional output directory",
    )
    args = parser.parse_args()

    experiment_config = get_config("experiment_corrected")
    prompt_config = get_config("prompts_corrected")
    condition_map = {cond["id"]: cond for cond in prompt_config["conditions"]}

    benchmark_names = (
        ["heartbench", "moral_stories_supported"]
        if args.benchmark == "both"
        else [args.benchmark or experiment_config["default_benchmark"]]
    )
    models = args.models or experiment_config["main"]["models"]
    conditions = args.conditions or experiment_config["main"]["conditions"]
    max_new_tokens = (
        args.max_new_tokens
        or experiment_config["evaluation"]["max_new_tokens"]
    )

    repair_prompt_text = load_prompt(PROJECT_ROOT / prompt_config["repair_prompt_file"])

    for current_bench in benchmark_names:
        benchmark_path, benchmark_key = resolve_benchmark_path(current_bench)
        if not benchmark_path.exists():
            print(f"Benchmark file not found: {benchmark_path}")
            continue

        items = load_benchmark(benchmark_path)
        if args.limit is not None:
            items = items[:args.limit]

        output_dir = (
            Path(args.output_dir)
            if args.output_dir
            else PROJECT_ROOT / "results_corrected" / benchmark_key / "main"
        )
        ensure_dir(output_dir)
        print(f"\n{'=' * 60}")
        print(f"Benchmark: {benchmark_key}")
        print(f"Items: {len(items)}")
        print(f"{'=' * 60}")

        for model_id in models:
            model_short = model_id.split("/")[-1]
            model, tokenizer = load_model_and_tokenizer(model_id)
            for cond_id in conditions:
                if cond_id not in condition_map:
                    print(f"Unknown condition: {cond_id}, skipping")
                    continue

                cond = condition_map[cond_id]
                prompt_template = load_prompt(PROJECT_ROOT / cond["file"])
                print(f"\nRunning {model_short} / {cond_id} ({cond['name']})")
                start = time.time()
                results = run_condition(
                    model,
                    tokenizer,
                    items,
                    prompt_template,
                    repair_prompt_text,
                    cond_id,
                    model_short,
                    max_new_tokens,
                )
                elapsed = time.time() - start
                parse_rate = sum(1 for row in results if row["parse_success"]) / len(results) * 100
                print(f"  Done in {elapsed:.1f}s, parse rate: {parse_rate:.1f}%")

                cond_output_path = output_dir / f"{model_short}_{cond_id}.jsonl"
                save_jsonl(results, cond_output_path)
                print(f"  Saved to {cond_output_path}")

            del model, tokenizer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        all_results = []
        for path in sorted(output_dir.glob("Qwen*.jsonl")):
            all_results.extend(load_benchmark(path))
        combined_path = output_dir / "all_results.jsonl"
        save_jsonl(all_results, combined_path)
        print(f"\nAll results saved to {combined_path}")
        print(f"Total: {len(all_results)} outputs")


if __name__ == "__main__":
    main()
