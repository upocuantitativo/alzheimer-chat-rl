"""Heuristic progression detector.

Compares a current session's linguistic features against a baseline
(either a previous session for the same patient or population norms).
Returns a 'progression score' in [-1, +1]:
    +1  =  strong evidence of decline
     0  =  stable
    -1  =  improvement / cognitive reserve effect

This is NOT a diagnostic. It is a research signal to be reviewed by a
clinician, with confidence intervals and per-feature contributions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .linguistic_features import LinguisticFeatures, extract_features


# Population-level rough norms (informed by published ADReSS/Ivanova statistics).
# These are deliberate, conservative defaults — tune them against real data
# once DementiaBank access is granted.
NORMS_HEALTHY = dict(
    ttr=0.55, mattr_20=0.72, mean_utt_length=12.0,
    filler_ratio=0.04, repetition_ratio=0.02, anomia_ratio=0.005,
    truncation_ratio=0.02, idea_density_proxy=0.55,
)

NORMS_MILD_AD = dict(
    ttr=0.42, mattr_20=0.60, mean_utt_length=7.0,
    filler_ratio=0.12, repetition_ratio=0.10, anomia_ratio=0.05,
    truncation_ratio=0.15, idea_density_proxy=0.42,
)

# Sign of each feature when it indicates DECLINE.
FEATURE_DIRECTION = dict(
    ttr=-1, mattr_20=-1, mean_utt_length=-1, idea_density_proxy=-1,
    filler_ratio=+1, repetition_ratio=+1, anomia_ratio=+1, truncation_ratio=+1,
)


@dataclass
class ProgressionReport:
    score: float                       # -1..+1, positive = decline signal
    confidence: float                  # 0..1, low when utterances are few
    per_feature: dict[str, float] = field(default_factory=dict)
    current: dict = field(default_factory=dict)
    baseline: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "score": round(self.score, 3),
            "confidence": round(self.confidence, 3),
            "per_feature": {k: round(v, 3) for k, v in self.per_feature.items()},
            "current": self.current,
            "baseline": self.baseline,
            "notes": self.notes,
        }


class ProgressionDetector:
    def __init__(self, baseline: LinguisticFeatures | dict | None = None):
        if baseline is None:
            self.baseline = NORMS_HEALTHY.copy()
        elif isinstance(baseline, LinguisticFeatures):
            self.baseline = baseline.as_dict()
        else:
            self.baseline = dict(baseline)

    def evaluate(
        self,
        utterances: list[str],
        language: str = "es",
    ) -> ProgressionReport:
        feats = extract_features(utterances, language=language)
        current = feats.as_dict()

        per_feature: dict[str, float] = {}
        notes: list[str] = []

        for fname, direction in FEATURE_DIRECTION.items():
            cur = float(current.get(fname, 0.0))
            base = float(self.baseline.get(fname, 0.0))
            denom = max(0.01, abs(base) + 0.05)
            # Normalized signed deviation
            delta = direction * (cur - base) / denom
            per_feature[fname] = max(-1.5, min(1.5, delta))

        # Mean across features → squash into [-1, 1]
        avg = sum(per_feature.values()) / len(per_feature)
        score = max(-1.0, min(1.0, avg / 2.0))

        # Confidence rises with utterance count; saturates around 40 utt.
        n = current.get("n_utterances", 0) or 0
        confidence = min(1.0, n / 40.0)

        if confidence < 0.25:
            notes.append("Pocas elocuciones — el score es indicativo y no diagnóstico.")
        if per_feature.get("anomia_ratio", 0) > 0.5:
            notes.append("Marcadores de anomia elevados.")
        if per_feature.get("repetition_ratio", 0) > 0.5:
            notes.append("Repeticiones por encima del baseline.")
        if per_feature.get("ttr", 0) > 0.5:
            notes.append("Diversidad léxica reducida (TTR/MATTR).")

        return ProgressionReport(
            score=score,
            confidence=confidence,
            per_feature=per_feature,
            current=current,
            baseline=self.baseline,
            notes=notes,
        )
