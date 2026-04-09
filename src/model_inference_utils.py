#!/usr/bin/env python3
"""Shared model-loading and generation helpers for canonical pipelines."""

from __future__ import annotations

import os
import json
import urllib.error
import urllib.request

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def get_inference_device(prefer_mps: bool = False):
    """Prefer local accelerators when available."""
    if torch.cuda.is_available():
        return torch.device("cuda"), torch.float16
    if prefer_mps and torch.backends.mps.is_available():
        return torch.device("mps"), torch.float16
    # Qwen2.5 currently triggers MPS matmul shape failures in this environment,
    # so prefer the stable CPU path unless CUDA is available.
    return torch.device("cpu"), torch.float32


def is_ollama_model_id(model_id: str) -> bool:
    """Treat `name:tag` model identifiers as Ollama-local models."""
    return ":" in model_id and "/" not in model_id


def load_model_and_tokenizer(model_id: str, prefer_mps: bool = False):
    """Load a model/tokenizer pair from the local Hugging Face cache."""
    print(f"Loading model: {model_id}")
    if is_ollama_model_id(model_id):
        print("Using backend: ollama")
        return {"backend": "ollama", "model_id": model_id}, None

    device, dtype = get_inference_device(prefer_mps=prefer_mps)
    print(f"Using device: {device}, dtype: {dtype}")
    common_kwargs = {
        "trust_remote_code": True,
    }
    model_kwargs = {**common_kwargs}
    if device.type != "cpu":
        model_kwargs["torch_dtype"] = dtype
    try:
        old_hf_offline = os.environ.get("HF_HUB_OFFLINE")
        old_transformers_offline = os.environ.get("TRANSFORMERS_OFFLINE")
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            local_files_only=True,
            **common_kwargs,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            local_files_only=True,
            **model_kwargs,
        )
        print("Loaded model from local Hugging Face cache.")
    except OSError:
        print("Local cache incomplete; falling back to Hugging Face download.")
        if old_hf_offline is None:
            os.environ.pop("HF_HUB_OFFLINE", None)
        else:
            os.environ["HF_HUB_OFFLINE"] = old_hf_offline
        if old_transformers_offline is None:
            os.environ.pop("TRANSFORMERS_OFFLINE", None)
        else:
            os.environ["TRANSFORMERS_OFFLINE"] = old_transformers_offline
        tokenizer = AutoTokenizer.from_pretrained(model_id, **common_kwargs)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            **model_kwargs,
        )
    else:
        if old_hf_offline is None:
            os.environ.pop("HF_HUB_OFFLINE", None)
        else:
            os.environ["HF_HUB_OFFLINE"] = old_hf_offline
        if old_transformers_offline is None:
            os.environ.pop("TRANSFORMERS_OFFLINE", None)
        else:
            os.environ["TRANSFORMERS_OFFLINE"] = old_transformers_offline
    model.to(device)
    model.eval()
    return model, tokenizer


def generate_ollama_chat_response(
    model_id: str,
    messages: list[dict],
    max_new_tokens: int = 128,
    temperature: float | None = None,
    top_p: float | None = None,
    seed: int | None = None,
) -> str:
    """Generate a deterministic chat response from a local Ollama server."""
    options = {
        "num_predict": max_new_tokens,
        "temperature": 0 if temperature is None else temperature,
        "top_p": 1 if top_p is None else top_p,
    }
    if seed is not None:
        options["seed"] = seed
    payload = {
        "model": model_id,
        "messages": messages,
        "stream": False,
        "options": options,
    }
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama request failed for {model_id}: {exc}") from exc

    return data["message"]["content"].strip()


def generate_chat_response(
    model,
    tokenizer,
    messages: list[dict],
    max_new_tokens: int = 128,
    temperature: float | None = None,
    top_p: float | None = None,
    do_sample: bool = False,
    seed: int | None = None,
) -> str:
    """Generate a deterministic chat response from an explicit message list."""
    if isinstance(model, dict) and model.get("backend") == "ollama":
        return generate_ollama_chat_response(
            model["model_id"],
            messages,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            seed=seed,
        )

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
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
        )

    response = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
    return response.strip()


def generate_response(
    model,
    tokenizer,
    prompt: str,
    max_new_tokens: int = 128,
) -> str:
    """Generate a deterministic chat response."""
    return generate_chat_response(
        model,
        tokenizer,
        [{"role": "user", "content": prompt}],
        max_new_tokens=max_new_tokens,
    )


def attempt_repair(
    model,
    tokenizer,
    original_prompt: str,
    bad_output: str,
    repair_prompt_text: str,
    max_new_tokens: int = 128,
) -> str:
    """Attempt to repair malformed JSON output via a follow-up turn."""
    return generate_chat_response(
        model,
        tokenizer,
        [
        {"role": "user", "content": original_prompt},
        {"role": "assistant", "content": bad_output},
        {"role": "user", "content": repair_prompt_text},
        ],
        max_new_tokens=max_new_tokens,
    )
