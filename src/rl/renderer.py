"""Materialise an AgentAction into an utterance.

Templates + interest/trend-aware activity selection. The LLM is NOT used
here — RL training must be reproducible.

New actions (REFRÁN, CANCIÓN, TRIVIA_CULTURAL, TRIVIA_DEPORTES) are backed
by the ActivityBank. Each returns a CognitiveTest wrapping the Activity so
that the environment can verify the patient's answer.
"""
from __future__ import annotations

import random
from typing import Optional

from ..chatbot.actions import AgentAction, TEMPLATES
from ..chatbot.activities import Activity, ActivityBank
from ..chatbot.tests import CognitiveTest, CognitiveTestBank
from ..patient_simulator import PatientSimulator
from ..patient_simulator.cognitive_state import Stage

# Map new AgentActions to activity categories
_ACTION_TO_CATEGORY = {
    AgentAction.REFRÁN: "refrán",
    AgentAction.CANCIÓN: "canción",
    AgentAction.TRIVIA_CULTURAL: "trivia_cultural",
    AgentAction.TRIVIA_DEPORTES: "trivia_deportes",
}

# Difficulty cap per cognitive stage for cultural activities
_MAX_DIFFICULTY = {
    Stage.HEALTHY:     1.0,
    Stage.MCI:         0.8,
    Stage.MILD_AD:     0.6,
    Stage.MODERATE_AD: 0.4,
    Stage.SEVERE_AD:   0.25,
}


def _activity_to_test(activity: Activity) -> CognitiveTest:
    """Wrap an Activity as a CognitiveTest for the existing environment pipeline."""
    from ..chatbot.tests import CognitiveTest as CT

    def verify(answer: str) -> bool:
        from ..chatbot.activities import _norm
        norm_ans = _norm(answer)
        return any(_norm(acc) in norm_ans or norm_ans in _norm(acc)
                   for acc in activity.accepted_es)

    return CT(
        domain=activity.category,
        difficulty=activity.difficulty,
        prompt_es=activity.stimulus_es,
        prompt_en=activity.stimulus_es,   # Spanish activities only for now
        verify=verify,
        metadata={
            "completion": activity.completion_es,
            "is_procedural": activity.is_procedural,
            "interest_tags": activity.interest_tags,
        },
    )


def render_action(
    sim: PatientSimulator,
    action: AgentAction,
    bank: CognitiveTestBank,
    rng: random.Random,
    *,
    last_test: Optional[CognitiveTest] = None,
    activity_bank: Optional[ActivityBank] = None,
    trending_tags: Optional[list[str]] = None,
    local_items: Optional[list[str]] = None,
) -> tuple[str, Optional[CognitiveTest]]:
    """Return (utterance, optional_test_object).

    The test object is returned for cognitive tests and cultural activities
    so the environment can verify the patient's answer.
    """
    L = sim.language
    tpl = TEMPLATES[action]
    pool = tpl.es if L == "es" else tpl.en

    # ----------------------------------------------------------------
    # Original actions
    # ----------------------------------------------------------------
    if action == AgentAction.PROBE_LIKE:
        revealed = sorted(sim.profile.revealed_likes)
        if not revealed:
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

    # ----------------------------------------------------------------
    # New cultural / motivational actions
    # ----------------------------------------------------------------
    if action in _ACTION_TO_CATEGORY:
        category = _ACTION_TO_CATEGORY[action]
        ab = activity_bank or ActivityBank(seed=rng.randint(0, 999999))

        max_diff = _MAX_DIFFICULTY.get(sim.state.stage, 1.0)
        interest_tags = list(sim.profile.revealed_likes) + list(sim.profile.likes)

        activity = ab.sample(
            category,
            max_difficulty=max_diff,
            interest_tags=interest_tags,
            trending_tags=trending_tags or [],
            prefer_procedural=(action in (AgentAction.REFRÁN, AgentAction.CANCIÓN)),
        )

        if activity is None:
            # Fallback to open question if bank empty
            fallback = TEMPLATES[AgentAction.OPEN_QUESTION]
            return rng.choice(fallback.es if L == "es" else fallback.en), None

        utterance = rng.choice(pool).format(stimulus=activity.stimulus_es)
        return utterance, _activity_to_test(activity)

    # ----------------------------------------------------------------
    # Simple template actions (no substitution needed)
    # ----------------------------------------------------------------
    return rng.choice(pool), None
