"""Session-level interest trend tracker and alarm system.

The tracker maintains a decayed score per topic category.
After each turn it updates scores based on engagement signals
(latency, success, mood, response length) and exposes:

    trending(n)     — top-n hot categories right now
    cold_topics()   — categories not used for many turns
    check_alarms()  — returns list of active alarm codes

Alarm codes
-----------
ALARM_ANXIETY_SPIKE     patient anxiety > 0.75 for 2+ consecutive turns
ALARM_FATIGUE_CRITICAL  patient fatigue > 0.85
ALARM_SILENCE_STREAK    3+ consecutive silent turns (strategy not working)
ALARM_PROGRESSION       activity success rate drops below 0.25 on previously
                        mastered category (early deterioration signal)
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional

from ..patient_simulator.cognitive_state import CognitiveState


@dataclass
class TurnRecord:
    category: str
    success: bool
    latency_s: float
    mood_delta: float
    response_length: int  # word count


class InterestTracker:
    def __init__(self, decay: float = 0.85):
        self.decay = decay
        self._scores: dict[str, float] = defaultdict(float)
        self._last_used_turn: dict[str, int] = {}
        self._turn: int = 0

        # For alarm logic
        self._high_anxiety_turns: int = 0
        self._silence_streak: int = 0
        self._history: deque[TurnRecord] = deque(maxlen=20)

        # Track success per category for progression alarm
        self._category_success: dict[str, deque] = defaultdict(lambda: deque(maxlen=8))

    def update(
        self,
        category: str,
        *,
        success: bool,
        latency_s: float,
        mood_delta: float,
        response_length: int,
        is_silent: bool,
        silence_threshold: float = 12.0,
    ) -> None:
        self._turn += 1
        self._last_used_turn[category] = self._turn

        # Build reward signal from engagement indicators
        signal = 0.0
        if success:
            signal += 1.0
        if not is_silent:
            fit = max(0.0, 1.0 - latency_s / silence_threshold)
            signal += fit * 0.4
        if response_length >= 10:
            signal += 0.2
        if mood_delta > 0:
            signal += mood_delta * 0.5
        if is_silent:
            signal -= 1.0

        # Decay all scores, then add this turn's signal
        for k in list(self._scores.keys()):
            self._scores[k] *= self.decay
        self._scores[category] += signal

        # Track per-category success for progression detection
        self._category_success[category].append(int(success))

        # Track silence streak
        if is_silent:
            self._silence_streak += 1
        else:
            self._silence_streak = 0

        self._history.append(TurnRecord(
            category=category,
            success=success,
            latency_s=latency_s,
            mood_delta=mood_delta,
            response_length=response_length,
        ))

    def update_anxiety(self, anxiety: float) -> None:
        if anxiety > 0.75:
            self._high_anxiety_turns += 1
        else:
            self._high_anxiety_turns = 0

    def trending(self, n: int = 3) -> list[str]:
        """Return top-n categories by current engagement score."""
        scored = [(cat, sc) for cat, sc in self._scores.items() if sc > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [cat for cat, _ in scored[:n]]

    def cold_topics(self, current_turn: int | None = None, cold_after: int = 5) -> list[str]:
        """Return categories not used in the last cold_after turns."""
        t = current_turn or self._turn
        return [cat for cat, last in self._last_used_turn.items()
                if t - last >= cold_after]

    def best_category(self, candidates: list[str]) -> Optional[str]:
        """Return the candidate category with the highest engagement score."""
        if not candidates:
            return None
        return max(candidates, key=lambda c: self._scores.get(c, 0.0))

    def check_alarms(self, state: CognitiveState) -> list[str]:
        alarms: list[str] = []

        if self._high_anxiety_turns >= 2:
            alarms.append("ALARM_ANXIETY_SPIKE")

        if state.fatigue > 0.85:
            alarms.append("ALARM_FATIGUE_CRITICAL")

        if self._silence_streak >= 3:
            alarms.append("ALARM_SILENCE_STREAK")

        # Progression alarm: recent success rate < 25% on a category used >= 4 times
        for cat, window in self._category_success.items():
            if len(window) >= 4:
                recent_rate = sum(window) / len(window)
                if recent_rate < 0.25:
                    alarms.append(f"ALARM_PROGRESSION:{cat}")

        return alarms

    def engagement_summary(self) -> dict:
        total = len(self._history)
        if total == 0:
            return {"turns": 0, "avg_latency": 0.0, "success_rate": 0.0,
                    "trending": [], "silence_streak": self._silence_streak}
        avg_lat = sum(r.latency_s for r in self._history) / total
        suc_rate = sum(1 for r in self._history if r.success) / total
        return {
            "turns": total,
            "avg_latency_s": round(avg_lat, 1),
            "success_rate": round(suc_rate, 2),
            "trending": self.trending(3),
            "silence_streak": self._silence_streak,
            "scores": {k: round(v, 2) for k, v in sorted(
                self._scores.items(), key=lambda x: -x[1])},
        }
