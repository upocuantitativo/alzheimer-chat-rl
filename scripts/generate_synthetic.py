"""Generate synthetic conversations between a (scripted or trained) agent and
the simulated patient. Outputs JSONL with one conversation per line.

Each record contains:
    - patient profile (private fields included for analysis; remove for sharing)
    - per-turn agent action, utterance, patient utterance, reward components
    - end-of-episode linguistic features and progression score

Usage:
    python scripts/generate_synthetic.py --n 500 --out data/synthetic/run_001.jsonl
    python scripts/generate_synthetic.py --n 100 --policy random
    python scripts/generate_synthetic.py --n 100 --policy ppo --model models/ppo_v1.zip
    python scripts/generate_synthetic.py --n 50  --patient-mode llm_hybrid    # uses Groq
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Ensure UTF-8 on Windows consoles.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.chatbot import ScriptedAgent     # noqa: E402
from src.chatbot.actions import AgentAction  # noqa: E402
from src.rl import AlzheimerChatEnv        # noqa: E402
from src.signals import ProgressionDetector, extract_features  # noqa: E402


def load_policy(name: str, model_path: str | None):
    """Return a callable policy(obs, env) -> action_index."""
    if name == "random":
        import random
        rng = random.Random()
        def policy(obs, env):
            return rng.randint(0, env.action_space.n - 1)
        return policy

    if name == "scripted":
        agent = ScriptedAgent()
        def policy(obs, env):
            return int(agent.act(env.sim))
        return policy

    if name == "ppo":
        if not model_path:
            raise ValueError("--model required for ppo policy")
        from stable_baselines3 import PPO
        model = PPO.load(model_path)
        def policy(obs, env):
            action, _ = model.predict(obs, deterministic=False)
            return int(action)
        return policy

    raise ValueError(f"unknown policy: {name}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100, help="Number of conversations")
    ap.add_argument("--out", required=True)
    ap.add_argument("--policy", choices=["random", "scripted", "ppo"], default="scripted")
    ap.add_argument("--model", default=None)
    ap.add_argument("--language", default="es", choices=["es", "en"])
    ap.add_argument("--patient-mode", default="rules_only",
                    choices=["rules_only", "llm_hybrid", "llm_only"])
    ap.add_argument("--max-turns", type=int, default=12)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    env = AlzheimerChatEnv(
        language=args.language,
        max_turns=args.max_turns,
        seed=args.seed,
        patient_mode=args.patient_mode,
    )
    policy = load_policy(args.policy, args.model)
    detector = ProgressionDetector()

    t0 = time.time()
    with open(out, "w", encoding="utf-8") as f:
        for ep in tqdm(range(args.n), desc=f"sintetizando ({args.policy})"):
            obs, info = env.reset(seed=args.seed + ep)
            total_reward = 0.0
            done = False
            while not done:
                a = policy(obs, env)
                obs, r, terminated, truncated, step_info = env.step(a)
                total_reward += r
                done = terminated or truncated

            patient_utts = [t["patient"] for t in env.transcript]
            feats = extract_features(patient_utts, language=args.language)
            prog = detector.evaluate(patient_utts, language=args.language)

            record = {
                "episode": ep,
                "language": args.language,
                "policy": args.policy,
                "n_turns": len(env.transcript),
                "total_reward": round(total_reward, 3),
                "patient_profile": env.sim.profile.as_dict(),
                "final_patient_state": env.sim.state.as_dict(),
                "transcript": env.transcript,
                "linguistic_features": feats.as_dict(),
                "progression": prog.as_dict(),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    dt = time.time() - t0
    print(f"\n✓ {args.n} conversaciones en {dt:.1f}s → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
