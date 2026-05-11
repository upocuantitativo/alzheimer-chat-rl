"""Cognitive state model for the simulated patient.

Mapping to standard clinical scales:
    - MMSE (Mini-Mental State Examination), 0–30
    - CDR (Clinical Dementia Rating), 0 / 0.5 / 1 / 2 / 3
    - GDS (Global Deterioration Scale), 1–7

We keep MMSE as the primary axis because it is the most widely reported in
the public datasets (ADReSS, Ivanova, TAUKADIAL).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum


class Stage(str, Enum):
    HEALTHY = "healthy"           # MMSE 27–30, CDR 0
    MCI = "mci"                   # MMSE 24–28, CDR 0.5  (mild cognitive impairment)
    MILD_AD = "mild_ad"           # MMSE 20–26, CDR 1
    MODERATE_AD = "moderate_ad"   # MMSE 10–20, CDR 2
    SEVERE_AD = "severe_ad"       # MMSE <10,   CDR 3

    @classmethod
    def from_mmse(cls, mmse: int) -> "Stage":
        if mmse >= 27:
            return cls.HEALTHY
        if mmse >= 24:
            return cls.MCI
        if mmse >= 20:
            return cls.MILD_AD
        if mmse >= 10:
            return cls.MODERATE_AD
        return cls.SEVERE_AD


@dataclass
class CognitiveState:
    """Continuous + discrete state of the simulated patient.

    Continuous variables drift turn-by-turn:
        - fatigue:  0..1  (rises with effort, falls with rest)
        - anxiety:  0..1  (rises with confrontation, falls with validation)
        - mood:    -1..1  (negative→positive)

    Discrete:
        - mmse, stage   (slow trajectory, can change between sessions)
        - language      ("es" or "en")
    """

    mmse: int = 22
    fatigue: float = 0.1
    anxiety: float = 0.2
    mood: float = 0.0
    language: str = "es"

    history_length: int = 0
    cognitive_successes: int = 0
    cognitive_failures: int = 0

    @property
    def stage(self) -> Stage:
        return Stage.from_mmse(self.mmse)

    # -------- transitions --------
    def step_fatigue(self, delta: float) -> None:
        self.fatigue = max(0.0, min(1.0, self.fatigue + delta))

    def step_anxiety(self, delta: float) -> None:
        self.anxiety = max(0.0, min(1.0, self.anxiety + delta))

    def step_mood(self, delta: float) -> None:
        self.mood = max(-1.0, min(1.0, self.mood + delta))

    # -------- sampling --------
    @classmethod
    def sample(cls, rng: random.Random | None = None, language: str = "es") -> "CognitiveState":
        rng = rng or random.Random()
        # Skew toward MCI / mild AD which is the most clinically relevant range
        mmse = int(rng.choices(
            population=[28, 25, 22, 18, 14, 8],
            weights=[1, 3, 4, 3, 2, 1],
            k=1,
        )[0])
        return cls(
            mmse=mmse,
            fatigue=rng.uniform(0.0, 0.3),
            anxiety=rng.uniform(0.0, 0.4),
            mood=rng.uniform(-0.2, 0.3),
            language=language,
        )

    def as_dict(self) -> dict:
        return {
            "mmse": self.mmse,
            "stage": self.stage.value,
            "fatigue": round(self.fatigue, 3),
            "anxiety": round(self.anxiety, 3),
            "mood": round(self.mood, 3),
            "language": self.language,
            "history_length": self.history_length,
            "cognitive_successes": self.cognitive_successes,
            "cognitive_failures": self.cognitive_failures,
        }
