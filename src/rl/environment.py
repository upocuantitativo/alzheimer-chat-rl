"""Gymnasium-style environment wrapping the PatientSimulator.

Observation (vector, len=12):
    [ mmse_norm, fatigue, anxiety, mood,
      discovery_rate, n_revealed_likes_norm, n_revealed_dislikes_norm,
      stage_one_hot (5) ]

Action: Discrete(9) — see chatbot.actions.AgentAction

Episode ends on:
    - AgentAction.CLOSE_TURN
    - max_turns reached
    - fatigue ≥ 0.95 (patient overwhelmed)
"""

from __future__ import annotations

import random
from typing import Any, Optional

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
    _HAS_GYM = True
except ImportError:  # pragma: no cover
    _HAS_GYM = False
    gym = object  # type: ignore

from ..chatbot.actions import ACTION_SPACE, AgentAction
from ..chatbot.tests import CognitiveTestBank
from ..patient_simulator import PatientSimulator, CognitiveState
from ..patient_simulator.cognitive_state import Stage
from .renderer import render_action
from .reward import RewardConfig, compute_reward


STAGE_ORDER = [Stage.HEALTHY, Stage.MCI, Stage.MILD_AD, Stage.MODERATE_AD, Stage.SEVERE_AD]


def _stage_one_hot(stage: Stage) -> list[float]:
    v = [0.0] * len(STAGE_ORDER)
    v[STAGE_ORDER.index(stage)] = 1.0
    return v


class AlzheimerChatEnv(gym.Env if _HAS_GYM else object):
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        *,
        language: str = "es",
        max_turns: int = 12,
        seed: Optional[int] = None,
        patient_mode: str = "rules_only",  # RL training should be fast: pure rules
        reward_config: Optional[RewardConfig] = None,
    ):
        super().__init__() if _HAS_GYM else None
        self.language = language
        self.max_turns = max_turns
        self.patient_mode = patient_mode
        self.reward_config = reward_config or RewardConfig(max_turns=max_turns)
        self._seed = seed
        self.rng = random.Random(seed)
        self.test_bank = CognitiveTestBank(seed=seed)

        if _HAS_GYM:
            self.action_space = spaces.Discrete(len(ACTION_SPACE))
            self.observation_space = spaces.Box(
                low=-1.0, high=1.0, shape=(12,), dtype=np.float32
            )

        self.sim: Optional[PatientSimulator] = None
        self.last_test = None
        self.n_turns = 0
        self.transcript: list[dict] = []

    # ------------------------------------------------------------------
    # Gym API
    # ------------------------------------------------------------------
    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None):
        if seed is not None:
            self._seed = seed
            self.rng = random.Random(seed)
            self.test_bank = CognitiveTestBank(seed=seed)
        self.sim = PatientSimulator(
            seed=self.rng.randint(0, 1_000_000),
            mode=self.patient_mode,
            language=self.language,
        )
        self.last_test = None
        self.n_turns = 0
        self.transcript = []
        obs = self._observe()
        info = {
            "patient_profile": self.sim.profile.as_dict(hide_private=True),
            "patient_state": self.sim.state.as_dict(),
        }
        return obs, info

    def step(self, action: int):
        assert self.sim is not None, "Call reset() first"
        a = AgentAction(int(action))
        state_before = self.sim.state.as_dict()

        # Render agent utterance, possibly with a cognitive test
        utterance, test = render_action(self.sim, a, self.test_bank, self.rng,
                                        last_test=self.last_test)

        # Patient responds
        turn = self.sim.reply(utterance)

        # Verify cognitive test if one was issued
        test_success: Optional[bool] = None
        if test is not None:
            result = CognitiveTestBank.evaluate(test, turn.text)
            test_success = result.success
            self.sim.record_test_outcome(result.success)
            self.last_test = test

        # Discovery flags (first-time only)
        triggered_like = (
            turn.triggered_like is not None
            and turn.triggered_like in self.sim.profile.revealed_likes
            and len(self.sim.profile.revealed_likes) > len(state_before.get("_likes_prev", set()))
        )
        # Simpler: trust patient turn signal
        triggered_like = turn.triggered_like is not None
        triggered_dislike = turn.triggered_dislike is not None

        closed = a == AgentAction.CLOSE_TURN
        self.n_turns += 1

        reward, components = compute_reward(
            sim_before=state_before,
            sim_after=self.sim,
            action=a,
            triggered_like=triggered_like,
            triggered_dislike=triggered_dislike,
            test_success=test_success,
            cfg=self.reward_config,
            closed=closed,
            n_turns=self.n_turns,
        )

        truncated = self.n_turns >= self.max_turns
        terminated = closed or self.sim.state.fatigue >= 0.95

        info = dict(
            action=a.name,
            agent=utterance,
            patient=turn.text,
            patient_state=self.sim.state.as_dict(),
            reward_components=components,
            test_success=test_success,
            triggered_like=turn.triggered_like,
            triggered_dislike=turn.triggered_dislike,
        )
        self.transcript.append(info)

        return self._observe(), float(reward), terminated, truncated, info

    def render(self) -> None:
        if not self.transcript:
            return
        last = self.transcript[-1]
        print(f"[{last['action']}] agent: {last['agent']}")
        print(f"             paciente: {last['patient']}")
        print(f"             r={sum(last['reward_components'].values()):+.2f}")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _observe(self) -> np.ndarray:
        s = self.sim.state
        p = self.sim.profile
        n_likes = len(p.revealed_likes)
        n_dislikes = len(p.revealed_dislikes)
        total_likes = max(1, len(p.likes))
        total_dislikes = max(1, len(p.dislikes))

        vec = [
            s.mmse / 30.0,
            s.fatigue,
            s.anxiety,
            (s.mood + 1.0) / 2.0,
            p.discovery_rate,
            n_likes / total_likes,
            n_dislikes / total_dislikes,
            *_stage_one_hot(s.stage),
        ]
        return np.asarray(vec, dtype=np.float32)
