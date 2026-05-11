"""Materialise an AgentAction into an utterance.

Pure templates + interest profile substitution. The LLM is intentionally
NOT used here — we want the RL training to depend on the action label,
not on stochastic verbal surface, to keep training reproducible.
"""

from __future__ import annotations

import random
from typing import Optional

from ..chatbot.actions import AgentAction, TEMPLATES
from ..chatbot.tests import CognitiveTest, CognitiveTestBank
from ..patient_simulator import PatientSimulator


def render_action(
    sim: PatientSimulator,
    action: AgentAction,
    bank: CognitiveTestBank,
    rng: random.Random,
    *,
    last_test: Optional[CognitiveTest] = None,
) -> tuple[str, Optional[CognitiveTest]]:
    """Return (utterance, optional_test_object).

    The test object is returned when the action is a cognitive test, so the
    environment can later verify the patient's response against it.
    """
    L = sim.language
    tpl = TEMPLATES[action]
    pool = tpl.es if L == "es" else tpl.en

    if action == AgentAction.PROBE_LIKE:
        revealed = sorted(sim.profile.revealed_likes)
        if not revealed:
            # No likes yet → fall back to open question
            fallback = TEMPLATES[AgentAction.OPEN_QUESTION]
            return rng.choice(fallback.es if L == "es" else fallback.en), None
        topic = rng.choice(revealed)
        return rng.choice(pool).format(topic=topic), None

    if action in (AgentAction.COGNITIVE_TEST_EASY, AgentAction.COGNITIVE_TEST_HARD):
        target_stage = sim.state.stage
        tests = bank.sample_for_stage(target_stage, n=3)
        if action == AgentAction.COGNITIVE_TEST_EASY:
            test = min(tests, key=lambda t: t.difficulty)
        else:
            test = max(tests, key=lambda t: t.difficulty)
        prompt = test.prompt_es if L == "es" else test.prompt_en
        utterance = rng.choice(pool).format(prompt=prompt)
        return utterance, test

    return rng.choice(pool), None
