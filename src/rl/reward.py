"""Multi-objective reward function.

The agent is rewarded for behaviour aligned with the clinical guides on
communication with AD patients:

    + interest discovery        (uncovering filias)
    + cognitive engagement      (proposing apt tests and patient succeeding)
    + emotional alignment       (validating, reducing anxiety, mood up)
    − fatigue induction         (long sessions with hard tests fatigue patient)
    − anxiety induction         (touching fobias without containment)
    − inappropriateness         (hard tests in severe stages, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass

from ..chatbot.actions import AgentAction
from ..patient_simulator import PatientSimulator
from ..patient_simulator.cognitive_state import Stage


@dataclass
class RewardConfig:
    discovery_bonus: float = 1.0
    test_success_bonus: float = 0.8
    test_fail_penalty: float = 0.3
    mood_weight: float = 0.5
    fatigue_weight: float = 0.6
    anxiety_weight: float = 0.7
    inappropriate_penalty: float = 0.8
    short_session_penalty: float = 0.5  # if you close too early
    max_turns: int = 12


def compute_reward(
    sim_before: dict,
    sim_after: PatientSimulator,
    action: AgentAction,
    triggered_like: bool,
    triggered_dislike: bool,
    test_success: bool | None,
    cfg: RewardConfig,
    closed: bool,
    n_turns: int,
) -> tuple[float, dict]:
    """Return (reward, components_dict) for logging."""
    s_before = sim_before
    s_after = sim_after.state.as_dict()

    components: dict[str, float] = {}

    # Discovery bonus — first time we reveal a like
    if triggered_like:
        components["discovery"] = cfg.discovery_bonus
    elif triggered_dislike and action != AgentAction.SHORT_REASSURE:
        components["fobia_hit"] = -cfg.inappropriate_penalty

    # Cognitive test outcomes
    if test_success is True:
        components["test_success"] = cfg.test_success_bonus
    elif test_success is False:
        components["test_fail"] = -cfg.test_fail_penalty

    # Emotional state shifts
    components["mood_shift"] = cfg.mood_weight * (s_after["mood"] - s_before["mood"])
    components["fatigue_shift"] = -cfg.fatigue_weight * (s_after["fatigue"] - s_before["fatigue"])
    components["anxiety_shift"] = -cfg.anxiety_weight * (s_after["anxiety"] - s_before["anxiety"])

    # Inappropriateness: hard test on severe patient, etc.
    stage = sim_after.state.stage
    if action == AgentAction.COGNITIVE_TEST_HARD and stage in (Stage.MODERATE_AD, Stage.SEVERE_AD):
        components["inappropriate"] = -cfg.inappropriate_penalty
    if action == AgentAction.COGNITIVE_TEST_HARD and s_before["fatigue"] > 0.7:
        components["inappropriate"] = components.get("inappropriate", 0) - cfg.inappropriate_penalty / 2

    # Early closure penalty
    if closed and n_turns < 4:
        components["early_close"] = -cfg.short_session_penalty

    # Small per-turn time cost to encourage useful turns
    components["step_cost"] = -0.02

    total = sum(components.values())
    return total, components
