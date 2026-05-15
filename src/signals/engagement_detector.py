"""High-level engagement detector for a full session.

Aggregates latency, interest-tracker, and linguistic signals into a
SessionEngagement summary that can be shown to caregivers or used as
a feature for longitudinal tracking.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .interest_tracker import InterestTracker
from .latency_model import EngagementSignal


@dataclass
class SessionEngagement:
    n_turns: int = 0
    avg_latency_s: float = 0.0
    avg_strategy_fit: float = 0.0
    activity_success_rate: float = 0.0
    silence_streak_max: int = 0
    trending_topics: list[str] = field(default_factory=list)
    alarms: list[str] = field(default_factory=list)
    topic_scores: dict[str, float] = field(default_factory=dict)

    def summary_text(self) -> str:
        lines = [
            f"Turnos: {self.n_turns}",
            f"Latencia media: {self.avg_latency_s:.1f}s  "
            f"(ajuste estrategia: {self.avg_strategy_fit:.2f})",
            f"Tasa de éxito en actividades: {self.activity_success_rate:.0%}",
        ]
        if self.trending_topics:
            lines.append(f"Temas de interés: {', '.join(self.trending_topics)}")
        if self.alarms:
            lines.append(f"⚠ Alarmas: {', '.join(self.alarms)}")
        return "\n".join(lines)


class EngagementDetector:
    """Accumulate per-turn signals into a session-level SessionEngagement."""

    def __init__(self) -> None:
        self._signals: list[EngagementSignal] = []
        self._tracker: Optional[InterestTracker] = None

    def attach_tracker(self, tracker: InterestTracker) -> None:
        self._tracker = tracker

    def record(self, signal: EngagementSignal) -> None:
        self._signals.append(signal)

    def evaluate(self, alarms: Optional[list[str]] = None) -> SessionEngagement:
        n = len(self._signals)
        if n == 0:
            return SessionEngagement()

        avg_lat = sum(s.latency_s for s in self._signals) / n
        avg_fit = sum(s.strategy_fit for s in self._signals) / n
        max_streak = max((s.silence_streak for s in self._signals), default=0)

        tracker_summary = self._tracker.engagement_summary() if self._tracker else {}

        return SessionEngagement(
            n_turns=n,
            avg_latency_s=round(avg_lat, 1),
            avg_strategy_fit=round(avg_fit, 3),
            activity_success_rate=tracker_summary.get("success_rate", 0.0),
            silence_streak_max=max_streak,
            trending_topics=tracker_summary.get("trending", []),
            alarms=alarms or [],
            topic_scores=tracker_summary.get("scores", {}),
        )
