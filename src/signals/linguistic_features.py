"""Linguistic features tied to AD-related speech changes.

These are the features most consistently reported in DementiaBank/ADReSS
studies as discriminative between healthy controls, MCI and AD:

    - Type-Token Ratio (TTR)              ↓ in AD
    - Moving-Average TTR (MATTR, w=20)    more stable estimator
    - Mean utterance length (words)       ↓ in moderate–severe AD
    - Filler ratio                        ↑ with stage
    - Repetition ratio                    ↑ with stage
    - Anomia / hypernym ratio             ↑ with stage
    - Idea density (proxy: noun+verb / total)  ↓ with stage
    - Sentence completeness                ↓ with stage (truncation)
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass

FILLER_WORDS = {
    "es": {"eh", "este", "esto", "bueno", "pues", "o sea", "vale", "mmm"},
    "en": {"um", "uh", "well", "you know", "i mean", "hmm"},
}

ANOMIA_MARKERS = {
    "es": {"esa cosa", "lo de siempre", "como se llame", "esa que tu sabes",
           "lo que se usa", "esa que tú sabes"},
    "en": {"that thing", "the usual", "whatchamacallit", "you know which",
           "the one you use"},
}

WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ']+")


@dataclass
class LinguisticFeatures:
    n_utterances: int
    n_tokens: int
    n_types: int
    ttr: float
    mattr_20: float
    mean_utt_length: float
    filler_ratio: float
    repetition_ratio: float
    anomia_ratio: float
    truncation_ratio: float
    idea_density_proxy: float

    def as_dict(self) -> dict:
        return asdict(self)


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in WORD_RE.findall(text)]


def _mattr(tokens: list[str], window: int = 20) -> float:
    if len(tokens) < window:
        return _ttr(tokens)
    ratios = []
    for i in range(0, len(tokens) - window + 1):
        seg = tokens[i : i + window]
        ratios.append(len(set(seg)) / window)
    return sum(ratios) / max(1, len(ratios))


def _ttr(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def _filler_ratio(tokens: list[str], lang: str) -> float:
    if not tokens:
        return 0.0
    fillers = FILLER_WORDS.get(lang, FILLER_WORDS["en"])
    n = sum(1 for t in tokens if t in fillers)
    return n / len(tokens)


def _repetition_ratio(text: str) -> float:
    """Fraction of bigrams that repeat consecutively within the utterance."""
    tokens = _tokens(text)
    if len(tokens) < 4:
        return 0.0
    bigrams = list(zip(tokens, tokens[1:]))
    repeats = sum(1 for i in range(1, len(bigrams)) if bigrams[i] == bigrams[i - 1])
    return repeats / max(1, len(bigrams))


def _anomia_ratio(text: str, lang: str) -> float:
    markers = ANOMIA_MARKERS.get(lang, ANOMIA_MARKERS["en"])
    t = text.lower()
    hits = sum(t.count(m) for m in markers)
    n_words = len(_tokens(text)) or 1
    return hits / n_words


def _truncation_ratio(utterances: list[str]) -> float:
    if not utterances:
        return 0.0
    truncated = sum(1 for u in utterances if u.rstrip().endswith("..."))
    return truncated / len(utterances)


def _idea_density_proxy(tokens: list[str]) -> float:
    """Crude proxy: ratio of non-stopword tokens to total. Real idea density
    requires POS-tagging; this approximation is fast and language-agnostic."""
    stop = {
        "es": {"el", "la", "los", "las", "un", "una", "y", "o", "de", "del", "a",
               "que", "en", "es", "se", "lo", "le", "su", "por", "para", "con",
               "no", "sí", "ya", "me", "te", "te", "mi", "tu", "yo"},
        "en": {"the", "a", "an", "and", "or", "of", "in", "is", "it", "to",
               "for", "with", "no", "yes", "me", "you", "my", "your", "i",
               "we", "us", "they", "them"},
    }
    if not tokens:
        return 0.0
    s = stop["es"] | stop["en"]
    content = sum(1 for t in tokens if t not in s)
    return content / len(tokens)


def extract_features(utterances: list[str], language: str = "es") -> LinguisticFeatures:
    """Compute linguistic features over a list of patient utterances."""
    joined = " ".join(utterances)
    tokens = _tokens(joined)
    n_tokens = len(tokens)
    n_types = len(set(tokens))
    n_utt = len(utterances)

    mean_len = n_tokens / max(1, n_utt)

    return LinguisticFeatures(
        n_utterances=n_utt,
        n_tokens=n_tokens,
        n_types=n_types,
        ttr=round(_ttr(tokens), 4),
        mattr_20=round(_mattr(tokens, 20), 4),
        mean_utt_length=round(mean_len, 3),
        filler_ratio=round(_filler_ratio(tokens, language), 4),
        repetition_ratio=round(_repetition_ratio(joined), 4),
        anomia_ratio=round(_anomia_ratio(joined, language), 4),
        truncation_ratio=round(_truncation_ratio(utterances), 4),
        idea_density_proxy=round(_idea_density_proxy(tokens), 4),
    )
