"""Cognitive test bank.

The tests are short, conversational and graded by difficulty. They map roughly
to validated paper-and-pencil domains used in MMSE / MoCA:

    - Orientation             (orientation in time/place)
    - Episodic memory         (immediate + delayed recall)
    - Semantic memory         (general knowledge / autobiographical)
    - Verbal fluency          (category fluency)
    - Naming                  (lexical retrieval)
    - Attention / calculation (simple math, serial subtractions)

For each test we keep:
    - difficulty (0..1)
    - the bank of items
    - a verifier that decides if the patient's response is "successful"

Verifiers use simple normalisation. A real deployment would use a clinician
panel — this is research-grade only.
"""

from __future__ import annotations

import random
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

from ..patient_simulator.cognitive_state import Stage


def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _contains_any(answer: str, accepted: list[str]) -> bool:
    a = _normalize(answer)
    return any(_normalize(x) in a for x in accepted)


@dataclass
class CognitiveTest:
    domain: str
    difficulty: float            # 0..1
    prompt_es: str
    prompt_en: str
    verify: Callable[[str], bool]
    metadata: dict = field(default_factory=dict)


@dataclass
class TestResult:
    test: CognitiveTest
    answer: str
    success: bool
    score: float       # graded credit, 0..1


# --------------------------------------------------------------------------
# Builders
# --------------------------------------------------------------------------
def _orientation_today() -> CognitiveTest:
    now = datetime.now()
    accepted_day = [now.strftime("%A").lower(), str(now.day)]
    # Spanish weekday
    es_days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    accepted_day.append(es_days[now.weekday()])

    def verify(ans: str) -> bool:
        return _contains_any(ans, accepted_day)

    return CognitiveTest(
        domain="orientation",
        difficulty=0.1,
        prompt_es="¿Qué día de la semana es hoy?",
        prompt_en="What day of the week is it today?",
        verify=verify,
        metadata={"answer_hint": accepted_day},
    )


def _orientation_year() -> CognitiveTest:
    year = datetime.now().year
    accepted = [str(year), str(year)[-2:]]

    def verify(ans: str) -> bool:
        return _contains_any(ans, accepted)

    return CognitiveTest(
        domain="orientation",
        difficulty=0.2,
        prompt_es="¿En qué año estamos?",
        prompt_en="What year are we in?",
        verify=verify,
        metadata={"answer_hint": accepted},
    )


def _semantic_general(prompt_es: str, prompt_en: str, accepted: list[str], diff: float) -> CognitiveTest:
    def verify(ans: str) -> bool:
        return _contains_any(ans, accepted)
    return CognitiveTest(
        domain="semantic",
        difficulty=diff,
        prompt_es=prompt_es,
        prompt_en=prompt_en,
        verify=verify,
        metadata={"answer_hint": accepted},
    )


def _fluency(category_es: str, category_en: str, min_items: int, diff: float) -> CognitiveTest:
    def verify(ans: str) -> bool:
        # Count distinct content words; success if >= min_items
        tokens = [t for t in re.split(r"[\s,.;]+", _normalize(ans)) if len(t) > 2]
        return len(set(tokens)) >= min_items
    return CognitiveTest(
        domain="fluency",
        difficulty=diff,
        prompt_es=f"Dígame, durante unos segundos, todos los {category_es} que se le ocurran.",
        prompt_en=f"In a few seconds, name as many {category_en} as you can.",
        verify=verify,
        metadata={"min_items": min_items, "category": category_es},
    )


def _attention_serial7() -> CognitiveTest:
    expected = [93, 86, 79, 72, 65]
    def verify(ans: str) -> bool:
        # Accept if any 3 of the expected numbers appear
        a = _normalize(ans)
        hits = sum(1 for n in expected if str(n) in a)
        return hits >= 3
    return CognitiveTest(
        domain="attention",
        difficulty=0.6,
        prompt_es="¿Puede restar 7 a 100 y seguir restando 7 al resultado?",
        prompt_en="Can you subtract 7 from 100 and keep subtracting 7?",
        verify=verify,
        metadata={"sequence": expected},
    )


def _naming() -> CognitiveTest:
    accepted = ["reloj", "watch", "clock", "wristwatch"]
    def verify(ans: str) -> bool:
        return _contains_any(ans, accepted)
    return CognitiveTest(
        domain="naming",
        difficulty=0.3,
        prompt_es="Si le muestro un objeto que va en la muñeca y marca la hora, ¿cómo se llama?",
        prompt_en="If I show you an object you wear on your wrist that tells time, what is it?",
        verify=verify,
        metadata={"answer_hint": accepted},
    )


def _episodic_word_recall(rng: random.Random) -> CognitiveTest:
    words_es = rng.sample(["manzana", "mesa", "moneda", "lapicero", "tren", "libro"], 3)
    words_en = rng.sample(["apple", "table", "coin", "pencil", "train", "book"], 3)
    def verify(ans: str) -> bool:
        a = _normalize(ans)
        hits = sum(1 for w in words_es + words_en if _normalize(w) in a)
        return hits >= 2
    return CognitiveTest(
        domain="episodic",
        difficulty=0.5,
        prompt_es=(f"Voy a decirle tres palabras y le pediré que las repita después: "
                   f"{', '.join(words_es)}. ¿Puede repetirlas?"),
        prompt_en=(f"I will say three words and ask you to repeat them: "
                   f"{', '.join(words_en)}. Can you repeat them?"),
        verify=verify,
        metadata={"words_es": words_es, "words_en": words_en},
    )


class CognitiveTestBank:
    """Adaptive bank of cognitive tests."""

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self._builders = [
            _orientation_today,
            _orientation_year,
            _naming,
            lambda: _fluency("animales", "animals", 5, 0.4),
            lambda: _fluency("frutas y verduras", "fruits and vegetables", 4, 0.35),
            lambda: _semantic_general(
                "¿Cuántos días tiene una semana?",
                "How many days are in a week?",
                ["7", "siete", "seven"], 0.15),
            lambda: _semantic_general(
                "¿En qué país nació Cervantes?",
                "In what country was Shakespeare born?",
                ["españa", "spain", "england", "inglaterra", "united kingdom"], 0.45),
            _attention_serial7,
            lambda: _episodic_word_recall(self.rng),
        ]

    def sample_for_stage(self, stage: Stage, n: int = 1) -> list[CognitiveTest]:
        """Pick tests whose difficulty matches the patient's stage."""
        target = {
            Stage.HEALTHY: 0.7,
            Stage.MCI: 0.55,
            Stage.MILD_AD: 0.4,
            Stage.MODERATE_AD: 0.25,
            Stage.SEVERE_AD: 0.1,
        }[stage]
        tests = [b() for b in self._builders]
        tests.sort(key=lambda t: abs(t.difficulty - target))
        return tests[:n]

    def random(self, n: int = 1) -> list[CognitiveTest]:
        builders = self.rng.sample(self._builders, k=min(n, len(self._builders)))
        return [b() for b in builders]

    @staticmethod
    def evaluate(test: CognitiveTest, answer: str) -> TestResult:
        ok = test.verify(answer)
        return TestResult(test=test, answer=answer, success=ok, score=1.0 if ok else 0.0)
