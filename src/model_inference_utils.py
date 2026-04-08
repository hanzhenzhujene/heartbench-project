#!/usr/bin/env python3
"""Shared model-loading and generation helpers for canonical pipelines."""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def get_inference_device():
    """Prefer local accelerators when available."""
    if torch.cuda.is_available():
        return torch.device("cuda"), torch.float16
    # Qwen2.5 currently triggers MPS matmul shape failures in this environment,
    # so prefer the stable CPU path unless CUDA is available.
    return torch.device("cpu"), torch.float32


def load_model_and_tokenizer(model_id: str):
    """Load a model/tokenizer pair from the local Hugging Face cache."""
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
    """Generate a deterministic chat response."""
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
    """Attempt to repair malformed JSON output via a follow-up turn."""
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
