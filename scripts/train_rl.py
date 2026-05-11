"""Train a PPO policy on AlzheimerChatEnv.

Usage:
    python scripts/train_rl.py --timesteps 50000 --out models/ppo_v1.zip
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timesteps", type=int, default=50_000)
    ap.add_argument("--out", default=str(ROOT / "models" / "ppo_v1.zip"))
    ap.add_argument("--language", default="es", choices=["es", "en"])
    ap.add_argument("--max-turns", type=int, default=12)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-envs", type=int, default=4)
    args = ap.parse_args()

    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.env_util import make_vec_env
    except ImportError:
        print("❌ stable-baselines3 no instalado. `pip install stable-baselines3 torch`")
        return 1

    from src.rl import AlzheimerChatEnv

    def make_env():
        return AlzheimerChatEnv(
            language=args.language,
            max_turns=args.max_turns,
            seed=None,
            patient_mode="rules_only",
        )

    vec_env = make_vec_env(make_env, n_envs=args.n_envs, seed=args.seed)
    model = PPO(
        "MlpPolicy",
        vec_env,
        verbose=1,
        n_steps=512,
        batch_size=64,
        learning_rate=3e-4,
        gamma=0.95,
        gae_lambda=0.9,
        ent_coef=0.01,
        seed=args.seed,
        tensorboard_log=str(ROOT / "tb_logs"),
    )

    print(f"Entrenando PPO durante {args.timesteps} steps en {args.n_envs} envs…")
    model.learn(total_timesteps=args.timesteps, progress_bar=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(out_path))
    print(f"✓ Modelo guardado en {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
