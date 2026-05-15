"""Gymnasium-style environment wrapping the PatientSimulator.

Observation (vector, len=16):
    [ mmse_norm, fatigue, anxiety, mood,
      discovery_rate, n_revealed_likes_norm, n_revealed_dislikes_norm,
      stage_one_hot (5),
      strategy_fit, engagement_trend, activity_success_rate, silence_streak_norm ]

Action: Discrete(13) — see chatbot.actions.AgentAction

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
from ..chatbot.activities import ActivityBank
from ..chatbot.tests import CognitiveTestBank
from ..patient_simulator import PatientSimulator, CognitiveState
from ..patient_simulator.cognitive_state import Stage
from ..signals.interest_tracker import InterestTracker
from .renderer import render_action
from .reward import RewardConfig, compute_reward

_CULTURAL_ACTIONS = {
    AgentAction.REFRÁN,
    AgentAction.CANCIÓN,
    AgentAction.TRIVIA_CULTURAL,
    AgentAction.TRIVIA_DEPORTES,
}


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
                low=-1.0, high=1.0, shape=(16,), dtype=np.float32
            )

        self.sim: Optional[PatientSimulator] = None
        self.last_test = None
        self.n_turns = 0
        self.transcript: list[dict] = []
        self.activity_bank: Optional[ActivityBank] = None
        self.interest_tracker: Optional[InterestTracker] = None
        self._last_strategy_fit: float = 0.5
        self._last_is_silent: bool = False

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
        self.activity_bank = ActivityBank(seed=self._seed)
        self.interest_tracker = InterestTracker()
        self._last_strategy_fit = 0.5
        self._last_is_silent = False
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

        # Determine if this is a cultural activity and its procedural flag
        is_cultural = a in _CULTURAL_ACTIONS
        trending = self.interest_tracker.trending(3) if self.interest_tracker else []

        # Render agent utterance, possibly with a cognitive test
        utterance, test = render_action(
            self.sim, a, self.test_bank, self.rng,
            last_test=self.last_test,
            activity_bank=self.activity_bank,
            trending_tags=trending,
        )

        is_procedural = bool(test and test.metadata.get("is_procedural", False))

        # Patient responds
        turn = self.sim.reply(
            utterance,
            is_procedural=is_procedural,
            topic_category=test.domain if test else None,
        )

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

        # Update latency / engagement tracking
        strategy_fit = 1.0 - min(turn.latency_s / 12.0, 1.0)
        self._last_strategy_fit = strategy_fit
        self._last_is_silent = turn.is_silent

        # Update interest tracker
        if self.interest_tracker and test:
            mood_before = state_before.get("mood", 0.0)
            mood_after = self.sim.state.mood
            response_len = len(turn.text.split())
            self.interest_tracker.update(
                test.domain,
                success=bool(test_success),
                latency_s=turn.latency_s,
                mood_delta=mood_after - mood_before,
                response_length=response_len,
                is_silent=turn.is_silent,
            )
            self.interest_tracker.update_anxiety(self.sim.state.anxiety)

        alarms = (self.interest_tracker.check_alarms(self.sim.state)
                  if self.interest_tracker else [])

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
            strategy_fit=strategy_fit,
            is_silent=turn.is_silent,
            is_cultural_activity=is_cultural,
            is_procedural=is_procedural,
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
            latency_s=turn.latency_s,
            is_silent=turn.is_silent,
            strategy_fit=round(strategy_fit, 3),
            alarms=alarms,
            engagement=self.interest_tracker.engagement_summary() if self.interest_tracker else {},
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

        # Engagement signals (new, 4 features)
        it = self.interest_tracker
        engagement_trend = 0.5
        act_success_rate = 0.5
        silence_streak_norm = 0.0
        if it and it._history:
            total = len(it._history)
            act_success_rate = sum(1 for r in it._history if r.success) / total
            engagement_trend = max(0.0, min(1.0, (act_success_rate + (1 - s.fatigue)) / 2))
            silence_streak_norm = min(1.0, it._silence_streak / 5.0)

        vec = [
            s.mmse / 30.0,
            s.fatigue,
            s.anxiety,
            (s.mood + 1.0) / 2.0,
            p.discovery_rate,
            n_likes / total_likes,
            n_dislikes / total_dislikes,
            *_stage_one_hot(s.stage),
            # new features
            self._last_strategy_fit,
            engagement_trend,
            act_success_rate,
            silence_streak_norm,
        ]
        return np.asarray(vec, dtype=np.float32)
