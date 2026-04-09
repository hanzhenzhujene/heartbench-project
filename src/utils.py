"""Utility functions for HeartBench pipeline."""

import json
import os
import yaml
from pathlib import Path
from typing import Optional, Union

PROJECT_ROOT = Path(__file__).parent.parent


def load_yaml(path: Union[str, Path]) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_prompt(path: Union[str, Path]) -> str:
    with open(path, "r") as f:
        return f.read().strip()


def render_prompt(template: str, case_a: str, case_b: str) -> str:
    return template.replace("{{CASE_A}}", case_a).replace("{{CASE_B}}", case_b)


def load_benchmark(path: Union[str, Path]) -> list[dict]:
    items = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def save_benchmark(items: list[dict], path: Union[str, Path]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def save_jsonl(records: list[dict], path: Union[str, Path]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_jsonl(path: Union[str, Path]) -> list[dict]:
    records = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def parse_json_output(text: str) -> Optional[dict]:
    """Try to parse JSON from model output, handling common issues."""
    text = text.strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting JSON from surrounding text
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    # Try fixing common issues: single quotes
    try:
        fixed = text.replace("'", '"')
        start = fixed.find("{")
        end = fixed.rfind("}")
        if start != -1 and end != -1:
            return json.loads(fixed[start:end + 1])
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def validate_parsed_output(parsed: dict) -> bool:
    """Check that parsed output has valid keys and values."""
    if not isinstance(parsed, dict):
        return False
    required_keys = {"heart_worse", "morally_worse", "reason_focus"}
    if not required_keys.issubset(parsed.keys()):
        return False
    if parsed.get("heart_worse") not in ("A", "B"):
        return False
    if parsed.get("morally_worse") not in ("A", "B"):
        return False
    valid_focus = {"outward_act", "motive", "consequence", "rule", "unclear"}
    if parsed.get("reason_focus") not in valid_focus:
        return False
    return True


def get_config(name: str) -> dict:
    return load_yaml(PROJECT_ROOT / "research" / "configs" / f"{name}.yaml")


def ensure_dir(path: Union[str, Path]) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
