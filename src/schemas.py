"""Schemas and validation for HeartBench-240."""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, List
import json

FAMILIES = [
    "same_act_different_motive",
    "same_restraint_different_posture",
    "same_correction_different_heart",
    "good_act_corrupt_motive",
    "flawed_act_benevolent_motive",
    "mixed_motive_hard",
]

FAMILY_LABELS = {
    "same_act_different_motive": "1. Same act, different motive",
    "same_restraint_different_posture": "2. Same restraint, different posture",
    "same_correction_different_heart": "3. Same correction, different heart",
    "good_act_corrupt_motive": "4. Good act, corrupt motive",
    "flawed_act_benevolent_motive": "5. Flawed act, benevolent motive",
    "mixed_motive_hard": "6. Mixed-motive hard cases",
}

SOURCE_TYPES = ["adapted", "original", "moral_stories"]
SETTING_TYPES = ["public", "private"]
DIFFICULTIES = ["easy", "medium", "hard"]
AB_VALUES = ["A", "B"]
PRIMARY_CUES = [
    "motive", "inward_posture", "manipulation", "vanity",
    "contempt", "compassion", "responsibility", "mixed",
]
REASON_FOCUS_VALUES = ["outward_act", "motive", "consequence", "rule", "unclear"]

ITEMS_PER_FAMILY = 40
TOTAL_ITEMS = 240


@dataclass
class BenchmarkItem:
    item_id: str
    family: str
    source_type: str
    setting_type: str
    domain: str
    difficulty: str
    case_A: str
    case_B: str
    gold_heart_worse: str
    gold_morally_worse: str
    gold_primary_cue: str
    notes: str = ""

    def validate(self) -> list[str]:
        errors = []
        if self.family not in FAMILIES:
            errors.append(f"Invalid family: {self.family}")
        if self.source_type not in SOURCE_TYPES:
            errors.append(f"Invalid source_type: {self.source_type}")
        if self.setting_type not in SETTING_TYPES:
            errors.append(f"Invalid setting_type: {self.setting_type}")
        if self.difficulty not in DIFFICULTIES:
            errors.append(f"Invalid difficulty: {self.difficulty}")
        if self.gold_heart_worse not in AB_VALUES:
            errors.append(f"Invalid gold_heart_worse: {self.gold_heart_worse}")
        if self.gold_morally_worse not in AB_VALUES:
            errors.append(f"Invalid gold_morally_worse: {self.gold_morally_worse}")
        if self.gold_primary_cue not in PRIMARY_CUES:
            errors.append(f"Invalid gold_primary_cue: {self.gold_primary_cue}")
        if not self.case_A.strip():
            errors.append("case_A is empty")
        if not self.case_B.strip():
            errors.append("case_B is empty")
        return errors

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BenchmarkItem":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def swapped(self) -> "BenchmarkItem":
        """Return a copy with A/B swapped."""
        swap_map = {"A": "B", "B": "A"}
        return BenchmarkItem(
            item_id=self.item_id + "_swap",
            family=self.family,
            source_type=self.source_type,
            setting_type=self.setting_type,
            domain=self.domain,
            difficulty=self.difficulty,
            case_A=self.case_B,
            case_B=self.case_A,
            gold_heart_worse=swap_map[self.gold_heart_worse],
            gold_morally_worse=swap_map[self.gold_morally_worse],
            gold_primary_cue=self.gold_primary_cue,
            notes=self.notes + " [A/B swapped]",
        )


@dataclass
class ModelOutput:
    item_id: str
    model: str
    condition: str
    raw_output: str
    heart_worse: Optional[str] = None
    morally_worse: Optional[str] = None
    reason_focus: Optional[str] = None
    parse_success: bool = False
    repair_attempted: bool = False
    repair_success: bool = False

    def to_dict(self) -> dict:
        return asdict(self)
