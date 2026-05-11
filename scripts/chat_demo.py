"""Interactive demo.

Modes:
    --mode interactive  : you play the agent, simulator plays the patient
    --mode scripted     : ScriptedAgent vs simulator, you watch
    --mode ppo          : trained PPO vs simulator (--model required)

Usage:
    python scripts/chat_demo.py --mode interactive
    python scripts/chat_demo.py --mode scripted --turns 10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.chatbot import ScriptedAgent
from src.chatbot.actions import AgentAction, TEMPLATES
from src.chatbot.tests import CognitiveTestBank
from src.patient_simulator import PatientSimulator
from src.rl import AlzheimerChatEnv
from src.rl.renderer import render_action
from src.signals import ProgressionDetector, extract_features


def banner(title: str) -> None:
    bar = "─" * (len(title) + 2)
    print(f"\n┌{bar}┐\n│ {title} │\n└{bar}┘")


def print_state(sim: PatientSimulator) -> None:
    s = sim.state
    p = sim.profile
    print(f"  · MMSE={s.mmse}  fase={s.stage.value}  fatiga={s.fatigue:.2f}  "
          f"ansiedad={s.anxiety:.2f}  ánimo={s.mood:+.2f}")
    print(f"  · descubierto: likes={sorted(p.revealed_likes)} dislikes={sorted(p.revealed_dislikes)}")


def run_scripted(args) -> int:
    env = AlzheimerChatEnv(language=args.language, max_turns=args.turns,
                            seed=args.seed, patient_mode=args.patient_mode)
    agent = ScriptedAgent(seed=args.seed)
    obs, info = env.reset(seed=args.seed)
    banner(f"Paciente: {env.sim.profile.name}, {env.sim.profile.age} años — "
           f"fase={env.sim.state.stage.value}")

    total_r = 0.0
    done = False
    while not done:
        a = agent.act(env.sim)
        obs, r, term, trunc, info = env.step(int(a))
        total_r += r
        print(f"\n[{info['action']}]")
        print(f"  agente   : {info['agent']}")
        print(f"  paciente : {info['patient']}")
        if info["test_success"] is not None:
            print(f"  ↳ test {'OK' if info['test_success'] else 'fallido'}")
        print(f"  r = {r:+.2f}")
        done = term or trunc

    banner("Resumen final")
    print_state(env.sim)
    patient_utts = [t["patient"] for t in env.transcript]
    feats = extract_features(patient_utts, language=args.language)
    prog = ProgressionDetector().evaluate(patient_utts, language=args.language)
    print(f"  recompensa total : {total_r:+.2f}  (en {len(env.transcript)} turnos)")
    print(f"  TTR={feats.ttr}  MATTR={feats.mattr_20}  "
          f"len_media={feats.mean_utt_length}")
    print(f"  progresión       : score={prog.score:+.3f}  confianza={prog.confidence:.2f}")
    for note in prog.notes:
        print(f"    · {note}")
    return 0


def run_ppo(args) -> int:
    if not args.model:
        print("❌ --model requerido para ppo")
        return 1
    from stable_baselines3 import PPO
    model = PPO.load(args.model)
    env = AlzheimerChatEnv(language=args.language, max_turns=args.turns,
                            seed=args.seed, patient_mode=args.patient_mode)
    obs, info = env.reset(seed=args.seed)
    banner(f"PPO vs Paciente: {env.sim.profile.name}")

    total_r = 0.0
    done = False
    while not done:
        a, _ = model.predict(obs, deterministic=True)
        obs, r, term, trunc, info = env.step(int(a))
        total_r += r
        print(f"\n[{info['action']}] agente: {info['agent']}")
        print(f"  paciente: {info['patient']}  (r={r:+.2f})")
        done = term or trunc
    banner("Fin")
    print(f"  recompensa total: {total_r:+.2f}")
    print_state(env.sim)
    return 0


def run_interactive(args) -> int:
    sim = PatientSimulator(seed=args.seed, mode=args.patient_mode, language=args.language)
    bank = CognitiveTestBank(seed=args.seed)

    banner(f"Paciente: {sim.profile.name}, {sim.profile.age} años")
    print("Acciones disponibles (escribe el número, o un texto libre para hablar):")
    for a in AgentAction:
        print(f"  {a.value}. {a.name}")
    print("  q. salir\n")

    import random
    rng = random.Random(args.seed)
    last_test = None

    for turn in range(args.turns):
        print_state(sim)
        choice = input(f"\n[turno {turn+1}] → ").strip()
        if not choice:
            continue
        if choice.lower() in {"q", "quit", "salir"}:
            break

        test = None
        if choice.isdigit() and int(choice) in [a.value for a in AgentAction]:
            action = AgentAction(int(choice))
            utt, test = render_action(sim, action, bank, rng, last_test=last_test)
            print(f"  agente : {utt}")
        else:
            utt = choice
            print(f"  agente : {utt}")

        patient_turn = sim.reply(utt)
        print(f"  paciente: {patient_turn.text}")
        if patient_turn.triggered_like:
            print(f"    ✓ descubierta filia: {patient_turn.triggered_like}")
        if patient_turn.triggered_dislike:
            print(f"    ⚠ tocada fobia    : {patient_turn.triggered_dislike}")
        if test is not None:
            result = CognitiveTestBank.evaluate(test, patient_turn.text)
            sim.record_test_outcome(result.success)
            print(f"    ↳ test [{test.domain}] {'OK' if result.success else 'fallido'}")
            last_test = test

    banner("Resumen final")
    print_state(sim)
    patient_utts = [t for s, t in sim.history if s == "patient"]
    feats = extract_features(patient_utts, language=args.language)
    prog = ProgressionDetector().evaluate(patient_utts, language=args.language)
    print(f"  TTR={feats.ttr}  MATTR={feats.mattr_20}  filler={feats.filler_ratio}")
    print(f"  progresión score = {prog.score:+.3f} (conf={prog.confidence:.2f})")
    for note in prog.notes:
        print(f"    · {note}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["interactive", "scripted", "ppo"],
                    default="scripted")
    ap.add_argument("--model", default=None)
    ap.add_argument("--language", default="es", choices=["es", "en"])
    ap.add_argument("--turns", type=int, default=10)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--patient-mode", default="llm_hybrid",
                    choices=["rules_only", "llm_hybrid", "llm_only"])
    args = ap.parse_args()

    if args.mode == "interactive":
        return run_interactive(args)
    if args.mode == "ppo":
        return run_ppo(args)
    return run_scripted(args)


if __name__ == "__main__":
    raise SystemExit(main())
