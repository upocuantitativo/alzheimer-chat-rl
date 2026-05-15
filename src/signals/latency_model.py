"""Simulated response-latency model and engagement signal.

In a real deployment, latency would be measured in wall-clock time.
Here we simulate it from the patient's cognitive state, topic fit, and
activity type. High latency (or silence) signals that the current
strategy, topic, or session timing is not working.

Key thresholds
--------------
SILENCE_THRESHOLD_S  — if latency >= this, the patient is "silent"
                        (empty or near-empty response). Default 12 s.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..patient_simulator.cognitive_state import Stage

SILENCE_THRESHOLD_S = 12.0

_BASE_LATENCY: dict[Stage, float] = {
    Stage.HEALTHY:     2.0,
    Stage.MCI:         3.5,
    Stage.MILD_AD:     6.0,
    Stage.MODERATE_AD: 10.0,
    Stage.SEVERE_AD:   20.0,
}


@dataclass
class EngagementSignal:
    latency_s: float
    is_silent: bool
    strategy_fit: float     # 0..1 — inverse normalized latency; higher = better fit
    silence_streak: int     # consecutive turns with silence


def compute_latency(
    stage: Stage,
    fatigue: float,
    *,
    topic_is_liked: bool = False,
    topic_is_disliked: bool = False,
    is_procedural: bool = False,
    turns_since_topic: int = 0,
    noise: float = 0.0,
) -> float:
    """Return simulated response latency in seconds."""
    base = _BASE_LATENCY[stage]

    fatigue_factor = 1.0 + fatigue * 1.5
    if topic_is_liked:
        topic_factor = 0.5
    elif topic_is_disliked:
        topic_factor = 1.8
    else:
        topic_factor = 1.0

    procedural_factor = 0.6 if is_procedural else 1.0

    # Slight penalty for topics not visited recently
    recency_factor = 1.0 + min(turns_since_topic * 0.05, 0.4)

    latency = base * fatigue_factor * topic_factor * procedural_factor * recency_factor
    latency += noise
    return max(0.3, latency)


def make_signal(latency_s: float, silence_streak: int) -> EngagementSignal:
    is_silent = latency_s >= SILENCE_THRESHOLD_S
    # strategy_fit: 1.0 when latency = 0, 0.0 when latency = SILENCE_THRESHOLD_S
    fit = max(0.0, 1.0 - latency_s / SILENCE_THRESHOLD_S)
    return EngagementSignal(
        latency_s=latency_s,
        is_silent=is_silent,
        strategy_fit=round(fit, 3),
        silence_streak=silence_streak,
    )
