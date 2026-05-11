"""A scripted (heuristic) agent.

Useful for:
    - Sanity-checking the RL environment.
    - Comparing the trained policy against a strong baseline.
    - Producing readable synthetic conversations before the RL agent is trained.

Policy rules (simple but informed by clinical guides):
    1. If patient anxiety high → SHORT_REASSURE or CHANGE_TOPIC.
    2. If fatigue high → CLOSE_TURN.
    3. If we have a revealed_like → PROBE_LIKE on it.
    4. If we know little about the patient (discovery_rate < 0.2) → OPEN_QUESTION or REMINISCE.
    5. Periodically (every ~3 turns) propose a cognitive test calibrated to the stage.
"""

from __future__ import annotations

import random
from typing import Optional

from ..patient_simulator import PatientSimulator
from ..patient_simulator.cognitive_state import Stage
from .actions import AgentAction


class ScriptedAgent:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.turns_since_test = 0

    def reset(self) -> None:
        self.turns_since_test = 0

    def act(self, sim: PatientSimulator) -> AgentAction:
        s = sim.state
        p = sim.profile

        if s.fatigue > 0.85:
            return AgentAction.CLOSE_TURN

        if s.anxiety > 0.6:
            return self.rng.choice([AgentAction.SHORT_REASSURE, AgentAction.CHANGE_TOPIC])

        # Test every ~3 turns, calibrated to stage
        self.turns_since_test += 1
        if self.turns_since_test >= 3 and s.fatigue < 0.6:
            self.turns_since_test = 0
            if s.stage in (Stage.HEALTHY, Stage.MCI):
                return AgentAction.COGNITIVE_TEST_HARD
            return AgentAction.COGNITIVE_TEST_EASY

        if p.revealed_likes and self.rng.random() < 0.55:
            return AgentAction.PROBE_LIKE

        if p.discovery_rate < 0.2:
            return self.rng.choice([AgentAction.OPEN_QUESTION, AgentAction.REMINISCE])

        return self.rng.choice([
            AgentAction.OPEN_QUESTION,
            AgentAction.REMINISCE,
            AgentAction.VALIDATE_EMOTION,
        ])
