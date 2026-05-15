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
from src.chatbot.activities import ActivityBank
from src.chatbot.tests import CognitiveTestBank
from src.data.local_knowledge import get_local_knowledge
from src.patient_simulator import PatientSimulator
from src.rl import AlzheimerChatEnv
from src.rl.renderer import render_action
from src.signals import ProgressionDetector, extract_features
from src.signals.engagement_detector import EngagementDetector
from src.signals.interest_tracker import InterestTracker
from src.signals.latency_model import make_signal


def _load_rag(path: str | None):
    if path is None:
        return None
    from pathlib import Path as _Path
    idx_dir = _Path(path)
    if not (idx_dir / "chunks.json").exists():
        print(f"[RAG] Índice no encontrado en {idx_dir}. "
              "Ejecuta primero: python scripts/build_rag_index.py\n")
        return None
    from src.data.rag_index import RAGIndex
    print(f"[RAG] Cargando índice desde {idx_dir}…")
    return RAGIndex.load(idx_dir)


def _rag_hint(rag, query: str) -> None:
    chunks = rag.query(query, k=2)
    if not chunks:
        return
    print()
    for c in chunks:
        src = c.source.replace(".pdf", "")
        snippet = c.text[:160].rstrip()
        print(f"  [Guía {src}, p.{c.page}] {snippet}…")
    print()


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
        lat = info.get("latency_s", 0.0)
        silent = " [SILENCIO]" if info.get("is_silent") else ""
        print(f"\n[{info['action']}]  latencia={lat:.1f}s{silent}")
        print(f"  agente   : {info['agent']}")
        print(f"  paciente : {info['patient']}")
        if info["test_success"] is not None:
            print(f"  ↳ test {'OK' if info['test_success'] else 'fallido'}")
        if info.get("alarms"):
            print(f"  ⚠ {', '.join(info['alarms'])}")
        print(f"  r = {r:+.2f}  fit={info.get('strategy_fit', 0):.2f}")
        done = term or trunc

    banner("Resumen final")
    print_state(env.sim)
    patient_utts = [t["patient"] for t in env.transcript]
    feats = extract_features(patient_utts, language=args.language)
    prog = ProgressionDetector().evaluate(patient_utts, language=args.language)
    eng = env.interest_tracker.engagement_summary() if env.interest_tracker else {}
    print(f"  recompensa total : {total_r:+.2f}  (en {len(env.transcript)} turnos)")
    print(f"  TTR={feats.ttr}  MATTR={feats.mattr_20}  len_media={feats.mean_utt_length}")
    print(f"  progresión       : score={prog.score:+.3f}  confianza={prog.confidence:.2f}")
    for note in prog.notes:
        print(f"    · {note}")
    if eng:
        print(f"  latencia media   : {eng.get('avg_latency_s', 0):.1f}s  "
              f"éxito actividades={eng.get('success_rate', 0):.0%}")
        if eng.get("trending"):
            print(f"  temas trending   : {', '.join(eng['trending'])}")
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
    rag = _load_rag(getattr(args, "rag", None))
    city = getattr(args, "city", None)
    birth_year = getattr(args, "birth_year", 1945)

    sim = PatientSimulator(seed=args.seed, mode=args.patient_mode, language=args.language)
    bank = CognitiveTestBank(seed=args.seed)
    activity_bank = ActivityBank(seed=args.seed)
    tracker = InterestTracker()
    detector = EngagementDetector()
    detector.attach_tracker(tracker)

    local_knowledge = None
    if city:
        print(f"[LOCAL] Cargando conocimiento de {city}...")
        local_knowledge = get_local_knowledge(city, birth_year=birth_year)
        print(f"  → {local_knowledge.region}: {', '.join(local_knowledge.dishes[:3])}")
        print()

    banner(f"Paciente: {sim.profile.name}, {sim.profile.age} años")
    print("Acciones disponibles (escribe el número, o un texto libre para hablar):")
    for a in AgentAction:
        print(f"  {a.value:2d}. {a.name}")
    print("   q. salir\n")

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
        trending = tracker.trending(3)
        if choice.isdigit() and int(choice) in [a.value for a in AgentAction]:
            action = AgentAction(int(choice))
            utt, test = render_action(sim, action, bank, rng, last_test=last_test,
                                      activity_bank=activity_bank, trending_tags=trending)
            print(f"  agente : {utt}")
        else:
            utt = choice
            test = None
            print(f"  agente : {utt}")

        is_procedural = bool(test and test.metadata.get("is_procedural", False))
        patient_turn = sim.reply(utt, is_procedural=is_procedural,
                                 topic_category=test.domain if test else None)

        lat_str = f"  [latencia ~{patient_turn.latency_s:.0f}s"
        lat_str += " — SILENCIO]" if patient_turn.is_silent else "]"
        print(f"  paciente: {patient_turn.text}{lat_str}")
        if patient_turn.triggered_like:
            print(f"    ✓ descubierta filia: {patient_turn.triggered_like}")
        if patient_turn.triggered_dislike:
            print(f"    ⚠ tocada fobia    : {patient_turn.triggered_dislike}")
        if rag:
            _rag_hint(rag, patient_turn.text)
        if test is not None:
            result = CognitiveTestBank.evaluate(test, patient_turn.text)
            sim.record_test_outcome(result.success)
            ok_str = "OK" if result.success else "fallido"
            print(f"    ↳ [{test.domain}] {ok_str}")
            if test.metadata.get("completion"):
                print(f"    ↳ respuesta esperada: «{test.metadata['completion']}»")
            last_test = test
            # Update interest tracker
            mood_before = patient_turn.state.get("mood", 0.0)
            tracker.update(
                test.domain,
                success=result.success,
                latency_s=patient_turn.latency_s,
                mood_delta=0.0,
                response_length=len(patient_turn.text.split()),
                is_silent=patient_turn.is_silent,
            )

        tracker.update_anxiety(sim.state.anxiety)
        alarms = tracker.check_alarms(sim.state)
        if alarms:
            print(f"  ⚠ ALARMA: {', '.join(alarms)}")
        detector.record(make_signal(patient_turn.latency_s, tracker._silence_streak))

    banner("Resumen final")
    print_state(sim)
    patient_utts = [t for s, t in sim.history if s == "patient"]
    feats = extract_features(patient_utts, language=args.language)
    prog = ProgressionDetector().evaluate(patient_utts, language=args.language)
    eng = detector.evaluate(alarms=tracker.check_alarms(sim.state))
    print(f"  TTR={feats.ttr}  MATTR={feats.mattr_20}  filler={feats.filler_ratio}")
    print(f"  progresión score = {prog.score:+.3f} (conf={prog.confidence:.2f})")
    for note in prog.notes:
        print(f"    · {note}")
    print()
    print(eng.summary_text())
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
    ap.add_argument("--rag", metavar="INDEX_DIR", default=None,
                    help="Ruta al índice RAG (p.ej. data/rag_index). "
                    "Solo activo en modo interactive.")
    ap.add_argument("--city", default=None,
                    help="Ciudad de origen del paciente para conocimiento local "
                    "(p.ej. 'Sevilla', 'Madrid'). Solo en modo interactive.")
    ap.add_argument("--birth-year", type=int, default=1945, dest="birth_year",
                    help="Año de nacimiento del paciente (default 1945). "
                    "Usado junto con --city.")
    args = ap.parse_args()

    if args.mode == "interactive":
        return run_interactive(args)
    if args.mode == "ppo":
        return run_ppo(args)
    return run_scripted(args)


if __name__ == "__main__":
    raise SystemExit(main())
