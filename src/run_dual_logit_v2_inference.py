#!/usr/bin/env python3
"""Run fast dual-logit scoring for HeartBench-v2 on act and heart dimensions."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import torch
from tqdm import tqdm

from model_inference_utils import load_model_and_tokenizer
from utils import PROJECT_ROOT, ensure_dir, get_config, load_benchmark, load_jsonl, load_prompt, save_jsonl


DIMENSION_BLOCKS = {
    "act": (
        "Rate how outwardly morally problematic the person's action, restraint, or correction is. "
        "Focus on what was outwardly done or omitted, not on hidden motive unless it changes the outward act itself."
    ),
    "heart": (
        "Rate how morally disordered the person's inward heart orientation is. "
        "Focus on motive, posture, aim, resentment, contempt, manipulation, mercy, or self-seeking that is evidenced in the text."
    ),
}


def render_case_prompt(template: str, case_text: str, dimension: str) -> str:
    return (
        template.replace("{{CASE_TEXT}}", case_text)
        .replace("{{DIMENSION_INSTRUCTIONS}}", DIMENSION_BLOCKS[dimension])
    )


def get_digit_tokens(tokenizer):
    mapping = {}
    for digit in ["1", "2", "3", "4", "5"]:
        token_ids = tokenizer.encode(digit, add_special_tokens=False)
        if len(token_ids) != 1:
            raise ValueError(f"Digit {digit!r} is not a single token: {token_ids}")
        mapping[digit] = token_ids[0]
    return mapping


def build_chat_text(tokenizer, prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def score_prompt_batch(model, tokenizer, prompts: list[str], digit_tokens: dict) -> list[dict]:
    texts = [build_chat_text(tokenizer, prompt) for prompt in prompts]
    inputs = tokenizer(texts, return_tensors="pt", padding=True)
    inputs = {key: value.to(model.device) for key, value in inputs.items()}

    with torch.inference_mode():
        outputs = model(**inputs, use_cache=False)

    attention_mask = inputs["attention_mask"]
    last_token_indices = attention_mask.sum(dim=1) - 1
    batch_indices = torch.arange(last_token_indices.shape[0], device=model.device)
    next_token_logits = outputs.logits[batch_indices, last_token_indices]

    token_ids = torch.tensor(list(digit_tokens.values()), device=next_token_logits.device)
    digit_logits = next_token_logits.index_select(1, token_ids)
    digit_probs = torch.softmax(digit_logits, dim=1)

    digits = list(digit_tokens.keys())
    digit_probs_list = digit_probs.tolist()
    scored = []
    for row in digit_probs_list:
        best_idx = max(range(len(digits)), key=lambda idx: row[idx])
        score = int(digits[best_idx])
        expected = sum((idx + 1) * prob for idx, prob in enumerate(row))
        scored.append(
            {
                "score": score,
                "expected_score": expected,
                "digit_probs": {digits[idx]: row[idx] for idx in range(len(digits))},
            }
        )
    return scored


def run_condition(
    model,
    tokenizer,
    items: list[dict],
    prompt_template: str,
    condition_id: str,
    model_name: str,
    digit_tokens: dict,
    batch_size: int,
) -> list[dict]:
    prompt_jobs = []
    for item in items:
        for case_label, case_text in [("A", item["case_A"]), ("B", item["case_B"])]:
            for dimension in ["act", "heart"]:
                prompt_jobs.append(
                    {
                        "item_id": item["item_id"],
                        "case_label": case_label,
                        "dimension": dimension,
                        "prompt": render_case_prompt(prompt_template, case_text, dimension),
                    }
                )

    partial_rows = {}
    progress = tqdm(total=len(prompt_jobs), desc=f"{model_name}/{condition_id}", unit="prompt")
    try:
        for start in range(0, len(prompt_jobs), batch_size):
            batch = prompt_jobs[start : start + batch_size]
            batch_prompts = [job["prompt"] for job in batch]
            batch_scores = score_prompt_batch(model, tokenizer, batch_prompts, digit_tokens)
            for job, scored in zip(batch, batch_scores):
                row_key = (job["item_id"], job["case_label"])
                row = partial_rows.setdefault(
                    row_key,
                    {
                        "item_id": job["item_id"],
                        "case_label": job["case_label"],
                        "model": model_name,
                        "condition": condition_id,
                        "reason_focus": None,
                        "parse_success": True,
                    },
                )
                prefix = job["dimension"]
                row[f"{prefix}_score"] = scored["score"]
                row[f"expected_{prefix}_score"] = scored["expected_score"]
                row[f"{prefix}_digit_probs"] = scored["digit_probs"]
            progress.update(len(batch))
    finally:
        progress.close()

    item_order = {item["item_id"]: idx for idx, item in enumerate(items)}
    case_order = {"A": 0, "B": 1}
    return sorted(
        partial_rows.values(),
        key=lambda row: (item_order[row["item_id"]], case_order[row["case_label"]]),
    )


def resolve_benchmark_path(benchmark_name: str):
    experiment_config = get_config("experiment_dual_logit_v2")
    benchmarks = experiment_config["benchmarks"]
    if benchmark_name not in benchmarks:
        benchmark_name = experiment_config["default_benchmark"]
    return PROJECT_ROOT / benchmarks[benchmark_name]["benchmark_file"], benchmark_name


def write_combined_results(output_dir: Path) -> None:
    deduped = {}
    for path in sorted(output_dir.glob("Qwen*.jsonl")):
        if path.name == "all_results.jsonl":
            continue
        for row in load_jsonl(path):
            key = (
                row.get("model"),
                row.get("condition"),
                row.get("item_id"),
                row.get("case_label"),
            )
            deduped[key] = row

    all_results = [
        deduped[key]
        for key in sorted(
            deduped,
            key=lambda row_key: (
                row_key[0] or "",
                row_key[1] or "",
                row_key[2] or "",
                row_key[3] or "",
            ),
        )
    ]

    all_path = output_dir / "all_results.jsonl"
    save_jsonl(all_results, all_path)
    print(f"\nSaved combined dual-logit results to {all_path}")


def main():
    parser = argparse.ArgumentParser(description="Run dual-logit HeartBench-v2 inference")
    parser.add_argument("--benchmark", type=str, default=None, help="Benchmark key")
    parser.add_argument(
        "--group",
        type=str,
        default=None,
        help="Optional execution group from configs/experiment_dual_logit_v2.yaml",
    )
    parser.add_argument("--models", nargs="+", default=None, help="Models to run")
    parser.add_argument("--conditions", nargs="+", default=None, help="Conditions to run")
    parser.add_argument("--limit", type=int, default=None, help="Optional item limit")
    parser.add_argument("--output-dir", type=str, default=None, help="Optional output directory")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size for prompt scoring")
    parser.add_argument(
        "--prefer-mps",
        action="store_true",
        help="Use MPS for this run when available",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing condition result files instead of skipping them",
    )
    args = parser.parse_args()

    experiment_config = get_config("experiment_dual_logit_v2")
    prompt_config = get_config("prompts_dual_logit_v2")
    condition_map = {cond["id"]: cond for cond in prompt_config["conditions"]}

    group_cfg = None
    if args.group:
        group_cfg = experiment_config.get("execution_groups", {}).get(args.group)
        if group_cfg is None:
            raise SystemExit(f"Unknown execution group: {args.group}")

    benchmark_name = (
        args.benchmark
        or (group_cfg["benchmark"] if group_cfg else None)
        or experiment_config["default_benchmark"]
    )
    benchmark_path, benchmark_key = resolve_benchmark_path(benchmark_name)
    items = load_benchmark(benchmark_path)
    if args.limit is not None:
        items = items[: args.limit]

    models = args.models or (group_cfg["models"] if group_cfg else None) or experiment_config["main"]["models"]
    conditions = (
        args.conditions
        or (group_cfg["conditions"] if group_cfg else None)
        or experiment_config["main"]["conditions"]
    )
    default_batch_size = 8 if torch.cuda.is_available() else 4
    batch_size = max(1, args.batch_size or default_batch_size)

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else PROJECT_ROOT / "results_dual_logit_v2" / benchmark_key / "main"
    )
    if args.limit is not None and args.output_dir is None:
        raise SystemExit(
            "Refusing to write a limited run into the canonical main results directory. "
            "Pass --output-dir for partial/sanity runs."
        )
    ensure_dir(output_dir)

    print(f"\n{'=' * 60}")
    if args.group:
        print(f"Execution group: {args.group}")
    print(f"Benchmark: {benchmark_key}")
    print(f"Items: {len(items)}")
    print(f"Batch size: {batch_size}")
    print(f"{'=' * 60}")

    for model_id in models:
        model_short = model_id.split("/")[-1]
        pending_conditions = []
        for cond_id in conditions:
            cond_output_path = output_dir / f"{model_short}_{cond_id}.jsonl"
            if cond_output_path.exists() and not args.overwrite:
                print(f"\nSkipping {model_short} / {cond_id}: found existing {cond_output_path.name}")
                continue
            pending_conditions.append(cond_id)

        if not pending_conditions:
            print(f"\nSkipping model {model_short}: all requested conditions already exist")
            continue

        model, tokenizer = load_model_and_tokenizer(model_id, prefer_mps=args.prefer_mps)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        digit_tokens = get_digit_tokens(tokenizer)
        for cond_id in pending_conditions:
            if cond_id not in condition_map:
                print(f"Unknown condition: {cond_id}, skipping")
                continue

            cond = condition_map[cond_id]
            cond_output_path = output_dir / f"{model_short}_{cond_id}.jsonl"
            prompt_template = load_prompt(PROJECT_ROOT / cond["file"])
            print(f"\nRunning {model_short} / {cond_id} ({cond['name']})")
            start = time.time()
            results = run_condition(
                model,
                tokenizer,
                items,
                prompt_template,
                cond_id,
                model_short,
                digit_tokens,
                batch_size,
            )
            elapsed = time.time() - start
            print(f"  Done in {elapsed:.1f}s")

            save_jsonl(results, cond_output_path)
            print(f"  Saved to {cond_output_path}")
            write_combined_results(output_dir)
            if getattr(model.device, "type", None) == "mps" and hasattr(torch, "mps"):
                torch.mps.empty_cache()

        del model, tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        elif hasattr(torch, "mps") and torch.backends.mps.is_available():
            torch.mps.empty_cache()

    write_combined_results(output_dir)


if __name__ == "__main__":
    main()
