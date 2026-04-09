#!/usr/bin/env python3
"""Run the staged J1 / explanation / J2 paper pipeline."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import torch
from tqdm import tqdm

from model_inference_utils import generate_chat_response, load_model_and_tokenizer
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

VALID_LABELS = {"A", "B", "tie"}


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text)


def render_template(template: str, **replacements: str) -> str:
    text = template
    for key, value in replacements.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def validate_judgment(parsed: dict) -> bool:
    if not isinstance(parsed, dict):
        return False
    return (
        parsed.get("heart_worse") in VALID_LABELS
        and parsed.get("act_worse") in VALID_LABELS
    )


def validate_explanation(parsed: dict) -> bool:
    return isinstance(parsed, dict) and isinstance(parsed.get("explanation"), str) and bool(parsed["explanation"].strip())


def parse_or_repair_json(
    model,
    tokenizer,
    messages: list[dict],
    repair_prompt_text: str,
    validator,
    max_new_tokens: int,
    generation_cfg: dict,
) -> dict:
    raw_output = generate_chat_response(
        model,
        tokenizer,
        messages,
        max_new_tokens=max_new_tokens,
        temperature=generation_cfg["temperature"],
        top_p=generation_cfg["top_p"],
        do_sample=generation_cfg["do_sample"],
        seed=generation_cfg["seed"],
    )
    parsed = parse_json_output(raw_output)
    parse_success = parsed is not None and validator(parsed)
    repair_attempted = False
    repair_success = False
    effective_output = raw_output

    if not parse_success:
        repair_attempted = True
        repair_messages = messages + [
            {"role": "assistant", "content": raw_output},
            {"role": "user", "content": repair_prompt_text},
        ]
        repaired_output = generate_chat_response(
            model,
            tokenizer,
            repair_messages,
            max_new_tokens=max_new_tokens,
            temperature=generation_cfg["temperature"],
            top_p=generation_cfg["top_p"],
            do_sample=generation_cfg["do_sample"],
            seed=generation_cfg["seed"],
        )
        repaired = parse_json_output(repaired_output)
        if repaired is not None and validator(repaired):
            parsed = repaired
            parse_success = True
            repair_success = True
            effective_output = repaired_output

    return {
        "raw_output": raw_output,
        "effective_output": effective_output,
        "parsed": parsed if parse_success else None,
        "parse_success": bool(parse_success),
        "repair_attempted": repair_attempted,
        "repair_success": repair_success,
    }


def parse_explanation_stage(
    model,
    tokenizer,
    messages: list[dict],
    repair_prompt_text: str,
    max_new_tokens: int,
    generation_cfg: dict,
) -> dict:
    parsed_result = parse_or_repair_json(
        model,
        tokenizer,
        messages,
        repair_prompt_text,
        validate_explanation,
        max_new_tokens,
        generation_cfg,
    )
    explanation_text = None
    if parsed_result["parsed"] is not None:
        explanation_text = parsed_result["parsed"]["explanation"].strip()
    else:
        raw_text = parsed_result["effective_output"].strip()
        if raw_text:
            explanation_text = raw_text

    return {
        **parsed_result,
        "explanation_text": explanation_text,
        "parse_success": explanation_text is not None,
    }


def condition_variants(condition: dict, prompt_cfg: dict, variant_limit: int | None = None) -> list[dict]:
    family = condition["frame_family"]
    variants = prompt_cfg["frame_variants"][family]
    if variant_limit is not None:
        variants = variants[:variant_limit]
    resolved = []
    for variant in variants:
        if "file" in variant:
            frame_text = load_prompt(PROJECT_ROOT / variant["file"])
            frame_source = variant["file"]
        else:
            frame_text = variant.get("text", "")
            frame_source = None
        resolved.append(
            {
                "frame_variant_id": variant["id"],
                "frame_text": frame_text,
                "frame_source": frame_source,
            }
        )
    return resolved


def resolve_group_or_args(args, experiment_cfg: dict):
    if args.group:
        group = experiment_cfg["execution_groups"][args.group]
        return (
            group["benchmark"],
            group["models"],
            group["conditions"],
        )
    benchmark = args.benchmark or experiment_cfg["default_benchmark"]
    models = args.models or experiment_cfg["main"]["models"]
    conditions = args.conditions or experiment_cfg["main"]["conditions"]
    return benchmark, models, conditions


def benchmark_path(experiment_cfg: dict, benchmark_key: str) -> Path:
    return PROJECT_ROOT / experiment_cfg["benchmarks"][benchmark_key]["benchmark_file"]


def output_filename(model_short: str, condition_id: str, frame_variant_id: str) -> str:
    return f"{safe_name(model_short)}_{condition_id}_{frame_variant_id}.jsonl"


def main():
    parser = argparse.ArgumentParser(description="Run staged J1/E/J2 paper inference")
    parser.add_argument("--benchmark", type=str, default=None, help="Benchmark key")
    parser.add_argument("--models", nargs="+", default=None, help="Models to run")
    parser.add_argument("--conditions", nargs="+", default=None, help="Conditions to run")
    parser.add_argument("--group", type=str, default=None, help="Named execution group from config")
    parser.add_argument("--limit", type=int, default=None, help="Optional item limit")
    parser.add_argument("--output-dir", type=str, default=None, help="Optional output directory")
    parser.add_argument("--skip-existing", action="store_true", help="Skip completed condition-variant files")
    parser.add_argument("--prefer-mps", action="store_true", help="Prefer MPS if available")
    parser.add_argument(
        "--variant-limit-per-family",
        type=int,
        default=None,
        help="Optional limit on paraphrase variants per frame family for smoke runs",
    )
    args = parser.parse_args()

    experiment_cfg = get_config("experiment_staged_paper")
    prompt_cfg = get_config("prompts_staged_paper")
    condition_map = {condition["id"]: condition for condition in prompt_cfg["conditions"]}

    benchmark_key, models, condition_ids = resolve_group_or_args(args, experiment_cfg)
    if benchmark_key not in experiment_cfg["benchmarks"]:
        raise SystemExit(f"Unknown benchmark: {benchmark_key}")

    benchmark_cfg = experiment_cfg["benchmarks"][benchmark_key]
    items = load_benchmark(benchmark_path(experiment_cfg, benchmark_key))
    if args.limit is not None:
        items = items[: args.limit]

    default_output = (
        PROJECT_ROOT
        / experiment_cfg["metadata"]["save_results_root"]
        / benchmark_key
        / benchmark_cfg["split"]
    )
    output_dir = Path(args.output_dir) if args.output_dir else default_output
    ensure_dir(output_dir)

    repair_prompt_text = load_prompt(PROJECT_ROOT / prompt_cfg["prompt_templates"]["repair_prompt"])
    j1_baseline_template = load_prompt(PROJECT_ROOT / prompt_cfg["prompt_templates"]["j1_baseline"])
    j1_pre_template = load_prompt(PROJECT_ROOT / prompt_cfg["prompt_templates"]["j1_with_pre_frame"])
    explanation_template = load_prompt(PROJECT_ROOT / prompt_cfg["prompt_templates"]["explanation_followup"])
    explanation_post_template = load_prompt(PROJECT_ROOT / prompt_cfg["prompt_templates"]["explanation_with_post_frame"])
    j2_template = load_prompt(PROJECT_ROOT / prompt_cfg["prompt_templates"]["j2_followup"])

    generation_cfg = experiment_cfg["generation"]

    manifest = {
        "experiment_name": experiment_cfg["experiment"]["name"],
        "benchmark": benchmark_key,
        "split": benchmark_cfg["split"],
        "benchmark_file": benchmark_cfg["benchmark_file"],
        "item_count": len(items),
        "seed": generation_cfg["seed"],
        "generation": generation_cfg,
        "models": models,
        "conditions": condition_ids,
        "results_files": [],
    }

    print(f"\n{'=' * 72}")
    print(f"Staged benchmark: {benchmark_key}")
    print(f"Split: {benchmark_cfg['split']}")
    print(f"Items: {len(items)}")
    print(f"{'=' * 72}")

    for model_id in models:
        model_short = model_id.split("/")[-1]
        model, tokenizer = load_model_and_tokenizer(model_id, prefer_mps=args.prefer_mps)
        model_backend = model.get("backend", "huggingface") if isinstance(model, dict) else "huggingface"

        for condition_id in condition_ids:
            if condition_id not in condition_map:
                print(f"Unknown condition: {condition_id}, skipping")
                continue
            condition = condition_map[condition_id]
            for variant in condition_variants(condition, prompt_cfg, args.variant_limit_per_family):
                out_path = output_dir / output_filename(
                    model_short,
                    condition_id,
                    variant["frame_variant_id"],
                )
                if args.skip_existing and out_path.exists():
                    print(f"Skipping existing {out_path.name}")
                    manifest["results_files"].append(str(out_path))
                    continue

                stage_rows = []
                start = time.time()
                desc = f"{model_short}/{condition_id}/{variant['frame_variant_id']}"
                for item in tqdm(items, desc=desc):
                    if condition["frame_placement"] == "pre":
                        j1_prompt = render_template(
                            j1_pre_template,
                            FRAME_TEXT=variant["frame_text"],
                            CASE_A=item["case_A"],
                            CASE_B=item["case_B"],
                        )
                    else:
                        j1_prompt = render_template(
                            j1_baseline_template,
                            CASE_A=item["case_A"],
                            CASE_B=item["case_B"],
                        )

                    j1_messages = [{"role": "user", "content": j1_prompt}]
                    j1 = parse_or_repair_json(
                        model,
                        tokenizer,
                        j1_messages,
                        repair_prompt_text,
                        validate_judgment,
                        generation_cfg["max_new_tokens_j1"],
                        generation_cfg,
                    )

                    explanation = None
                    j2 = None
                    skipped_metrics = []

                    if condition["run_explanation"]:
                        if condition["frame_placement"] == "post":
                            expl_prompt = render_template(
                                explanation_post_template,
                                FRAME_TEXT=variant["frame_text"],
                            )
                        else:
                            expl_prompt = explanation_template

                        j1_context = (
                            json.dumps(j1["parsed"], ensure_ascii=False)
                            if j1["parsed"] is not None
                            else j1["effective_output"]
                        )
                        explanation_messages = [
                            {"role": "user", "content": j1_prompt},
                            {"role": "assistant", "content": j1_context},
                            {"role": "user", "content": expl_prompt},
                        ]
                        explanation = parse_explanation_stage(
                            model,
                            tokenizer,
                            explanation_messages,
                            repair_prompt_text,
                            generation_cfg["max_new_tokens_explanation"],
                            generation_cfg,
                        )
                    else:
                        skipped_metrics.extend(["explanation_stage", "explanation_metrics"])

                    if condition["run_j2"]:
                        j1_context = (
                            json.dumps(j1["parsed"], ensure_ascii=False)
                            if j1["parsed"] is not None
                            else j1["effective_output"]
                        )
                        explanation_context = (
                            json.dumps({"explanation": explanation["explanation_text"]}, ensure_ascii=False)
                            if explanation and explanation["explanation_text"] is not None
                            else (explanation["effective_output"] if explanation else "")
                        )
                        j2_messages = [
                            {"role": "user", "content": j1_prompt},
                            {"role": "assistant", "content": j1_context},
                        ]
                        if explanation is not None:
                            j2_messages.extend(
                                [
                                    {"role": "user", "content": expl_prompt},
                                    {"role": "assistant", "content": explanation_context},
                                ]
                            )
                        j2_messages.append({"role": "user", "content": j2_template})
                        j2 = parse_or_repair_json(
                            model,
                            tokenizer,
                            j2_messages,
                            repair_prompt_text,
                            validate_judgment,
                            generation_cfg["max_new_tokens_j2"],
                            generation_cfg,
                        )
                    else:
                        skipped_metrics.extend(["j2_stage", "revision_metrics"])

                    stage_rows.append(
                        {
                            "experiment_name": experiment_cfg["experiment"]["name"],
                            "benchmark": benchmark_key,
                            "split": benchmark_cfg["split"],
                            "benchmark_split": benchmark_cfg["split"],
                            "benchmark_file": benchmark_cfg["benchmark_file"],
                            "item_id": item["item_id"],
                            "benchmark_version": item.get("benchmark_version"),
                            "model_id": model_id,
                            "model": model_short,
                            "model_backend": model_backend,
                            "condition": condition_id,
                            "condition_name": condition["name"],
                            "frame_family": condition["frame_family"],
                            "frame_placement": condition["frame_placement"],
                            "frame_variant": variant["frame_variant_id"],
                            "frame_variant_id": variant["frame_variant_id"],
                            "frame_source": variant["frame_source"],
                            "seed": generation_cfg["seed"],
                            "decode_config": {
                                "temperature": generation_cfg["temperature"],
                                "top_p": generation_cfg["top_p"],
                                "do_sample": generation_cfg["do_sample"],
                                "seed": generation_cfg["seed"],
                                "max_new_tokens_j1": generation_cfg["max_new_tokens_j1"],
                                "max_new_tokens_explanation": generation_cfg["max_new_tokens_explanation"],
                                "max_new_tokens_j2": generation_cfg["max_new_tokens_j2"],
                            },
                            "temperature": generation_cfg["temperature"],
                            "top_p": generation_cfg["top_p"],
                            "do_sample": generation_cfg["do_sample"],
                            "max_new_tokens_j1": generation_cfg["max_new_tokens_j1"],
                            "max_new_tokens_explanation": generation_cfg["max_new_tokens_explanation"],
                            "max_new_tokens_j2": generation_cfg["max_new_tokens_j2"],
                            "family": item["family"],
                            "difficulty": item["difficulty"],
                            "domain": item["domain"],
                            "setting_type": item["setting_type"],
                            "dissociation_target": item.get("dissociation_target"),
                            "gold_heart_worse": item.get("gold_heart_worse"),
                            "gold_act_worse": item.get("gold_act_worse"),
                            "j1_heart_worse": j1["parsed"].get("heart_worse") if j1["parsed"] else None,
                            "j1_act_worse": j1["parsed"].get("act_worse") if j1["parsed"] else None,
                            "j1_raw_output": j1["raw_output"],
                            "j1_parse_success": j1["parse_success"],
                            "j1_repair_attempted": j1["repair_attempted"],
                            "j1_repair_success": j1["repair_success"],
                            "explanation_text": explanation["explanation_text"] if explanation else None,
                            "explanation_raw_output": explanation["raw_output"] if explanation else None,
                            "explanation_parse_success": explanation["parse_success"] if explanation else None,
                            "explanation_repair_attempted": explanation["repair_attempted"] if explanation else None,
                            "explanation_repair_success": explanation["repair_success"] if explanation else None,
                            "j2_heart_worse": j2["parsed"].get("heart_worse") if j2 and j2["parsed"] else None,
                            "j2_act_worse": j2["parsed"].get("act_worse") if j2 and j2["parsed"] else None,
                            "j2_raw_output": j2["raw_output"] if j2 else None,
                            "j2_parse_success": j2["parse_success"] if j2 else None,
                            "j2_repair_attempted": j2["repair_attempted"] if j2 else None,
                            "j2_repair_success": j2["repair_success"] if j2 else None,
                            "skipped_metrics": skipped_metrics,
                            "output_file": str(out_path),
                            "result_file": str(out_path),
                        }
                    )

                elapsed = time.time() - start
                save_jsonl(stage_rows, out_path)
                print(f"Saved {out_path.name} in {elapsed:.1f}s")
                manifest["results_files"].append(str(out_path))

        del model, tokenizer
        if model_backend == "huggingface" and torch.cuda.is_available():
            torch.cuda.empty_cache()
        if model_backend == "huggingface" and torch.backends.mps.is_available():
            torch.mps.empty_cache()

    combined = []
    for path in sorted(output_dir.glob("*.jsonl")):
        if path.name == "all_results.jsonl":
            continue
        combined.extend(load_jsonl(path))
    deduped = {}
    for row in combined:
        key = (
            row["model"],
            row["condition"],
            row["frame_variant_id"],
            row["item_id"],
        )
        deduped[key] = row

    all_results_path = output_dir / "all_results.jsonl"
    save_jsonl(list(deduped.values()), all_results_path)
    manifest["combined_results_file"] = str(all_results_path)
    manifest["results_files"] = sorted(set(manifest["results_files"]))
    with open(output_dir / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nSaved combined staged results to {all_results_path}")
    print(f"Saved run manifest to {output_dir / 'run_manifest.json'}")


if __name__ == "__main__":
    main()
