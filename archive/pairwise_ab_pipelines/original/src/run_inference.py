#!/usr/bin/env python3
"""
Run inference on HeartBench using Qwen models with structured output.

Supports:
- All 5 prompt conditions (C0-C4)
- Both Qwen models (0.5B, 1.5B)
- Deterministic decoding (temperature=0, top_p=1, do_sample=False)
- JSON output parsing with repair
- Subset pilot runs
- A/B swap evaluation
"""

import argparse
import json
import os
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm

from utils import (
    load_benchmark, load_prompt, render_prompt,
    parse_json_output, validate_parsed_output,
    save_jsonl, get_config, ensure_dir, PROJECT_ROOT,
)


def get_inference_device():
    """Prefer local accelerators when available."""
    if torch.cuda.is_available():
        return torch.device("cuda"), torch.float16
    # Qwen2.5 currently triggers MPS matmul shape failures in this environment,
    # so prefer the stable CPU path unless CUDA is available.
    return torch.device("cpu"), torch.float32


def load_model_and_tokenizer(model_id: str):
    """Load model and tokenizer from HuggingFace cache."""
    print(f"Loading model: {model_id}")
    device, dtype = get_inference_device()
    print(f"Using device: {device}, dtype: {dtype}")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=dtype,
        trust_remote_code=True,
    )
    model.to(device)
    model.eval()
    return model, tokenizer


def generate_response(
    model,
    tokenizer,
    prompt: str,
    max_new_tokens: int = 128,
) -> str:
    """Generate a response using deterministic decoding."""
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(text, return_tensors="pt")
    inputs = {key: value.to(model.device) for key, value in inputs.items()}
    input_len = inputs["input_ids"].shape[1]

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=None,
            top_p=None,
            do_sample=False,
        )

    response = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
    return response.strip()


def attempt_repair(
    model,
    tokenizer,
    original_prompt: str,
    bad_output: str,
    repair_prompt_text: str,
    max_new_tokens: int = 128,
) -> str:
    """Attempt to repair malformed JSON output."""
    messages = [
        {"role": "user", "content": original_prompt},
        {"role": "assistant", "content": bad_output},
        {"role": "user", "content": repair_prompt_text},
    ]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(text, return_tensors="pt")
    inputs = {key: value.to(model.device) for key, value in inputs.items()}
    input_len = inputs["input_ids"].shape[1]

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=None,
            top_p=None,
            do_sample=False,
        )

    response = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
    return response.strip()


def run_condition(
    model,
    tokenizer,
    items: list[dict],
    prompt_template: str,
    repair_prompt_text: str,
    condition_id: str,
    model_name: str,
    max_new_tokens: int = 128,
) -> list[dict]:
    """Run inference for one condition on all items."""
    results = []
    for item in tqdm(items, desc=f"{model_name}/{condition_id}"):
        prompt = render_prompt(prompt_template, item["case_A"], item["case_B"])
        raw_output = generate_response(model, tokenizer, prompt, max_new_tokens)

        parsed = parse_json_output(raw_output)
        parse_ok = parsed is not None and validate_parsed_output(parsed)

        repair_attempted = False
        repair_success = False

        if not parse_ok:
            # Attempt repair
            repair_attempted = True
            repair_output = attempt_repair(
                model, tokenizer, prompt, raw_output,
                repair_prompt_text, max_new_tokens
            )
            parsed = parse_json_output(repair_output)
            if parsed is not None and validate_parsed_output(parsed):
                repair_success = True
                raw_output = raw_output + " [REPAIRED] " + repair_output
            else:
                parsed = None

        result = {
            "item_id": item["item_id"],
            "model": model_name,
            "condition": condition_id,
            "raw_output": raw_output,
            "heart_worse": parsed.get("heart_worse") if parsed else None,
            "morally_worse": parsed.get("morally_worse") if parsed else None,
            "reason_focus": parsed.get("reason_focus") if parsed else None,
            "parse_success": parse_ok or repair_success,
            "repair_attempted": repair_attempted,
            "repair_success": repair_success,
        }
        results.append(result)

    return results


def resolve_benchmark_paths(benchmark_name: str, pilot: bool) -> tuple:
    """Resolve benchmark file paths from experiment config."""
    experiment_config = get_config("experiment")
    benchmarks = experiment_config.get("benchmarks", {})

    if benchmark_name not in benchmarks:
        # Fall back to default
        benchmark_name = experiment_config.get("default_benchmark", "moral_stories")

    bench_cfg = benchmarks[benchmark_name]
    if pilot:
        bench_file = PROJECT_ROOT / bench_cfg["dev_file"]
    else:
        bench_file = PROJECT_ROOT / bench_cfg["benchmark_file"]

    swapped_file = PROJECT_ROOT / bench_cfg.get("swapped_file", "")
    return bench_file, swapped_file, benchmark_name


def main():
    parser = argparse.ArgumentParser(description="Run HeartBench inference")
    parser.add_argument("--benchmark", type=str, default=None,
                        choices=["moral_stories", "heartbench", "both"],
                        help="Benchmark to use (default: moral_stories)")
    parser.add_argument("--pilot", action="store_true",
                        help="Run pilot subset only (dev set)")
    parser.add_argument("--pilot-n", type=int, default=30,
                        help="Number of items for pilot (default: 30)")
    parser.add_argument("--conditions", nargs="+",
                        default=["C0", "C1", "C2", "C3", "C4"],
                        help="Conditions to run")
    parser.add_argument("--models", nargs="+",
                        default=["Qwen/Qwen2.5-0.5B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct"],
                        help="Models to run")
    parser.add_argument("--max-new-tokens", type=int, default=128,
                        help="Max new tokens for generation")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory")
    parser.add_argument("--swap", action="store_true",
                        help="Use A/B swapped benchmark")
    args = parser.parse_args()

    # Determine which benchmarks to run
    experiment_config = get_config("experiment")
    if args.benchmark is None:
        bench_name = experiment_config.get("default_benchmark", "moral_stories")
    else:
        bench_name = args.benchmark

    if bench_name == "both":
        benchmark_names = ["moral_stories", "heartbench"]
    else:
        benchmark_names = [bench_name]

    # Load configs
    prompts_config = get_config("prompts")
    condition_map = {c["id"]: c for c in prompts_config["conditions"]}

    for current_bench in benchmark_names:
        print(f"\n{'='*60}")
        print(f"Benchmark: {current_bench}")
        print(f"{'='*60}")

        benchmark_path, swapped_path, _ = resolve_benchmark_paths(current_bench, args.pilot)

        if args.swap:
            if swapped_path.exists():
                benchmark_path = swapped_path
            else:
                print(f"Swapped benchmark not found: {swapped_path}")
                print("Run ab_swap.py first.")
                continue

        if not benchmark_path.exists():
            print(f"Benchmark file not found: {benchmark_path}")
            continue

        items = load_benchmark(benchmark_path)
        if args.pilot and args.pilot_n < len(items):
            items = items[:args.pilot_n]

        print(f"Loaded {len(items)} items from {benchmark_path}")

        # Load repair prompt
        repair_prompt_text = load_prompt(PROJECT_ROOT / "prompts" / "repair_prompt.txt")

        # Set output directory — separate by benchmark
        if args.output_dir:
            output_dir = Path(args.output_dir)
        elif args.pilot:
            output_dir = PROJECT_ROOT / "results" / current_bench / "pilot"
        else:
            output_dir = PROJECT_ROOT / "results" / current_bench / "main"
        ensure_dir(output_dir)

        # Run each model x condition combination
        all_results = []
        for model_id in args.models:
            model_short = model_id.split("/")[-1]
            model, tokenizer = load_model_and_tokenizer(model_id)

            for cond_id in args.conditions:
                if cond_id not in condition_map:
                    print(f"Unknown condition: {cond_id}, skipping")
                    continue

                cond = condition_map[cond_id]
                prompt_template = load_prompt(PROJECT_ROOT / cond["file"])

                print(f"\nRunning {model_short} / {cond_id} ({cond['name']})")
                start = time.time()

                results = run_condition(
                    model, tokenizer, items, prompt_template,
                    repair_prompt_text, cond_id, model_short,
                    args.max_new_tokens,
                )

                elapsed = time.time() - start
                parse_rate = sum(1 for r in results if r["parse_success"]) / len(results) * 100
                print(f"  Done in {elapsed:.1f}s, parse rate: {parse_rate:.1f}%")

                # Save per-condition results
                cond_output_path = output_dir / f"{model_short}_{cond_id}.jsonl"
                save_jsonl(results, cond_output_path)
                print(f"  Saved to {cond_output_path}")

                all_results.extend(results)

            # Free memory
            del model, tokenizer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        # Save combined results
        combined_path = output_dir / "all_results.jsonl"
        save_jsonl(all_results, combined_path)
        print(f"\nAll results saved to {combined_path}")
        print(f"Total: {len(all_results)} outputs")


if __name__ == "__main__":
    main()
