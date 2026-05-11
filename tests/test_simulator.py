"""Basic smoke tests for the simulator and the RL env."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest

from src.chatbot import ScriptedAgent
from src.chatbot.actions import AgentAction
from src.chatbot.tests import CognitiveTestBank
from src.patient_simulator import PatientSimulator, CognitiveState
from src.patient_simulator.cognitive_state import Stage
from src.rl import AlzheimerChatEnv
from src.signals import extract_features, ProgressionDetector


def test_patient_state_sample_in_range():
    s = CognitiveState.sample()
    assert 0 <= s.mmse <= 30
    assert 0 <= s.fatigue <= 1
    assert 0 <= s.anxiety <= 1
    assert -1 <= s.mood <= 1


def test_stage_from_mmse():
    assert CognitiveState(mmse=30).stage == Stage.HEALTHY
    assert CognitiveState(mmse=25).stage == Stage.MCI
    assert CognitiveState(mmse=22).stage == Stage.MILD_AD
    assert CognitiveState(mmse=15).stage == Stage.MODERATE_AD
    assert CognitiveState(mmse=5).stage == Stage.SEVERE_AD


def test_simulator_runs_rules_only():
    sim = PatientSimulator(seed=1, mode="rules_only", language="es")
    turn = sim.reply("¿Le gusta la música?")
    assert turn.text
    assert "mmse" in turn.state


def test_env_runs_full_episode():
    env = AlzheimerChatEnv(language="es", max_turns=8, seed=42, patient_mode="rules_only")
    obs, info = env.reset(seed=42)
    assert obs.shape == (12,)
    agent = ScriptedAgent(seed=42)
    done = False
    while not done:
        a = int(agent.act(env.sim))
        obs, r, term, trunc, info = env.step(a)
        done = term or trunc
    assert len(env.transcript) >= 1


def test_features_and_progression():
    utts = [
        "Pues a ver, no recuerdo bien... esa cosa, ya sabes.",
        "Era pequeña, pequeña. No sé.",
        "Eh... no me viene.",
        "Mi madre, sí, cocinaba paella.",
    ]
    feats = extract_features(utts, language="es")
    assert feats.n_tokens > 0
    prog = ProgressionDetector().evaluate(utts, language="es")
    assert -1 <= prog.score <= 1


def test_cognitive_bank_for_stage():
    bank = CognitiveTestBank(seed=1)
    for stage in [Stage.HEALTHY, Stage.MILD_AD, Stage.SEVERE_AD]:
        tests = bank.sample_for_stage(stage, n=2)
        assert len(tests) == 2
        for t in tests:
            assert 0 <= t.difficulty <= 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
