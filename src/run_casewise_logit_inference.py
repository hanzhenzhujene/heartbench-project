#!/usr/bin/env python3
"""Run fast casewise scoring from next-token logits over digits 1-5."""

import argparse
import time
from pathlib import Path

import torch
from tqdm import tqdm

from model_inference_utils import load_model_and_tokenizer
from utils import PROJECT_ROOT, ensure_dir, get_config, load_benchmark, load_jsonl, load_prompt, save_jsonl


def render_case_prompt(template: str, case_text: str) -> str:
    return template.replace("{{CASE_TEXT}}", case_text)


def get_digit_tokens(tokenizer):
    mapping = {}
    for digit in ["1", "2", "3", "4", "5"]:
        token_ids = tokenizer.encode(digit, add_special_tokens=False)
        if len(token_ids) != 1:
            raise ValueError(f"Digit {digit!r} is not a single token: {token_ids}")
        mapping[digit] = token_ids[0]
    return mapping


def score_case(model, tokenizer, prompt: str, digit_tokens: dict) -> dict:
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt")
    inputs = {key: value.to(model.device) for key, value in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    next_token_logits = outputs.logits[0, -1]
    token_ids = torch.tensor(list(digit_tokens.values()), device=next_token_logits.device)
    digit_logits = next_token_logits.index_select(0, token_ids)
    digit_probs = torch.softmax(digit_logits, dim=0).tolist()

    digits = list(digit_tokens.keys())
    best_idx = max(range(len(digits)), key=lambda idx: digit_probs[idx])
    score = int(digits[best_idx])
    expected = sum((idx + 1) * prob for idx, prob in enumerate(digit_probs))

    return {
        "heart_score": score,
        "expected_heart_score": expected,
        "digit_probs": {digits[idx]: digit_probs[idx] for idx in range(len(digits))},
    }


def run_condition(model, tokenizer, items: list, prompt_template: str, condition_id: str, model_name: str, digit_tokens: dict) -> list:
    results = []
    for item in tqdm(items, desc=f"{model_name}/{condition_id}"):
        for case_label, case_text in [("A", item["case_A"]), ("B", item["case_B"])]:
            prompt = render_case_prompt(prompt_template, case_text)
            scored = score_case(model, tokenizer, prompt, digit_tokens)
            results.append(
                {
                    "item_id": item["item_id"],
                    "case_label": case_label,
                    "model": model_name,
                    "condition": condition_id,
                    "heart_score": scored["heart_score"],
                    "expected_heart_score": scored["expected_heart_score"],
                    "digit_probs": scored["digit_probs"],
                    "parse_success": True,
                }
            )
    return results


def resolve_benchmark_path(benchmark_name: str):
    experiment_config = get_config("experiment_casewise_logit")
    benchmarks = experiment_config["benchmarks"]
    if benchmark_name not in benchmarks:
        benchmark_name = experiment_config["default_benchmark"]
    return PROJECT_ROOT / benchmarks[benchmark_name]["benchmark_file"], benchmark_name


def main():
    parser = argparse.ArgumentParser(description="Run casewise logit inference")
    parser.add_argument("--benchmark", type=str, default=None, help="Benchmark key")
    parser.add_argument("--models", nargs="+", default=None, help="Models to run")
    parser.add_argument("--conditions", nargs="+", default=None, help="Conditions to run")
    parser.add_argument("--limit", type=int, default=None, help="Optional item limit")
    parser.add_argument("--output-dir", type=str, default=None, help="Optional output directory")
    args = parser.parse_args()

    experiment_config = get_config("experiment_casewise_logit")
    prompt_config = get_config("prompts_casewise_logit")
    condition_map = {cond["id"]: cond for cond in prompt_config["conditions"]}

    benchmark_name = args.benchmark or experiment_config["default_benchmark"]
    benchmark_path, benchmark_key = resolve_benchmark_path(benchmark_name)
    items = load_benchmark(benchmark_path)
    if args.limit is not None:
        items = items[:args.limit]

    models = args.models or experiment_config["main"]["models"]
    conditions = args.conditions or experiment_config["main"]["conditions"]

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else PROJECT_ROOT / "materials/results/casewise_logit" / benchmark_key / "main"
    )
    ensure_dir(output_dir)

    print(f"\n{'=' * 60}")
    print(f"Benchmark: {benchmark_key}")
    print(f"Items: {len(items)}")
    print(f"{'=' * 60}")

    for model_id in models:
        model_short = model_id.split("/")[-1]
        model, tokenizer = load_model_and_tokenizer(model_id)
        digit_tokens = get_digit_tokens(tokenizer)
        for cond_id in conditions:
            if cond_id not in condition_map:
                print(f"Unknown condition: {cond_id}, skipping")
                continue

            cond = condition_map[cond_id]
            prompt_template = load_prompt(PROJECT_ROOT / cond["file"])
            print(f"\nRunning {model_short} / {cond_id} ({cond['name']})")
            start = time.time()
            results = run_condition(model, tokenizer, items, prompt_template, cond_id, model_short, digit_tokens)
            elapsed = time.time() - start
            print(f"  Done in {elapsed:.1f}s")

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
    print(f"\nSaved combined casewise logit results to {all_path}")


if __name__ == "__main__":
    main()
