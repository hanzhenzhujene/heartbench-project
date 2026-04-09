#!/usr/bin/env python3
"""Run bias-resistant casewise heart scoring."""

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
    load_jsonl,
    load_prompt,
    parse_json_output,
    save_jsonl,
)

VALID_FOCUS = {"outward_act", "motive", "consequence", "rule", "unclear"}
VALID_SCORES = {1, 2, 3, 4, 5}


def render_case_prompt(template: str, case_text: str) -> str:
    return template.replace("{{CASE_TEXT}}", case_text)


def validate_casewise(parsed: dict) -> bool:
    if not isinstance(parsed, dict):
        return False
    if parsed.get("reason_focus") not in VALID_FOCUS:
        return False
    return parsed.get("heart_score") in VALID_SCORES


def run_case(
    model,
    tokenizer,
    item_id: str,
    case_label: str,
    case_text: str,
    prompt_template: str,
    repair_prompt_text: str,
    condition_id: str,
    model_name: str,
    max_new_tokens: int,
) -> dict:
    prompt = render_case_prompt(prompt_template, case_text)
    raw_output = generate_response(model, tokenizer, prompt, max_new_tokens)

    parsed = parse_json_output(raw_output)
    parse_ok = parsed is not None and validate_casewise(parsed)

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
        if parsed is not None and validate_casewise(parsed):
            repair_success = True
            raw_output = raw_output + " [REPAIRED] " + repair_output
        else:
            parsed = None

    return {
        "item_id": item_id,
        "case_label": case_label,
        "model": model_name,
        "condition": condition_id,
        "raw_output": raw_output,
        "heart_score": parsed.get("heart_score") if parsed else None,
        "reason_focus": parsed.get("reason_focus") if parsed else None,
        "parse_success": parse_ok or repair_success,
        "repair_attempted": repair_attempted,
        "repair_success": repair_success,
    }


def run_condition(
    model,
    tokenizer,
    items: list,
    prompt_template: str,
    repair_prompt_text: str,
    condition_id: str,
    model_name: str,
    max_new_tokens: int,
) -> list:
    results = []
    for item in tqdm(items, desc=f"{model_name}/{condition_id}"):
        results.append(
            run_case(
                model,
                tokenizer,
                item["item_id"],
                "A",
                item["case_A"],
                prompt_template,
                repair_prompt_text,
                condition_id,
                model_name,
                max_new_tokens,
            )
        )
        results.append(
            run_case(
                model,
                tokenizer,
                item["item_id"],
                "B",
                item["case_B"],
                prompt_template,
                repair_prompt_text,
                condition_id,
                model_name,
                max_new_tokens,
            )
        )
    return results


def resolve_benchmark_path(benchmark_name: str):
    experiment_config = get_config("experiment_casewise")
    benchmarks = experiment_config["benchmarks"]
    if benchmark_name not in benchmarks:
        benchmark_name = experiment_config["default_benchmark"]
    return PROJECT_ROOT / benchmarks[benchmark_name]["benchmark_file"], benchmark_name


def main():
    parser = argparse.ArgumentParser(description="Run casewise heart scoring inference")
    parser.add_argument("--benchmark", type=str, default=None, help="Benchmark key")
    parser.add_argument("--models", nargs="+", default=None, help="Models to run")
    parser.add_argument("--conditions", nargs="+", default=None, help="Conditions to run")
    parser.add_argument("--max-new-tokens", type=int, default=None, help="Max new tokens")
    parser.add_argument("--limit", type=int, default=None, help="Optional item limit")
    parser.add_argument("--output-dir", type=str, default=None, help="Optional output directory")
    args = parser.parse_args()

    experiment_config = get_config("experiment_casewise")
    prompt_config = get_config("prompts_casewise")
    condition_map = {cond["id"]: cond for cond in prompt_config["conditions"]}

    benchmark_name = args.benchmark or experiment_config["default_benchmark"]
    benchmark_path, benchmark_key = resolve_benchmark_path(benchmark_name)
    items = load_benchmark(benchmark_path)
    if args.limit is not None:
        items = items[:args.limit]

    models = args.models or experiment_config["main"]["models"]
    conditions = args.conditions or experiment_config["main"]["conditions"]
    max_new_tokens = args.max_new_tokens or experiment_config["evaluation"]["max_new_tokens"]

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else PROJECT_ROOT / "results" / "casewise_ab" / benchmark_key / "main"
    )
    ensure_dir(output_dir)

    repair_prompt_text = load_prompt(PROJECT_ROOT / prompt_config["repair_prompt_file"])

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
        all_results.extend(load_jsonl(path))

    all_path = output_dir / "all_results.jsonl"
    save_jsonl(all_results, all_path)
    print(f"\nSaved combined casewise results to {all_path}")


if __name__ == "__main__":
    main()
