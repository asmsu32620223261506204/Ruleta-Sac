# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from pathlib import Path
import csv
import numpy as np

from stable_baselines3 import SAC
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from roulette_env_sb3 import RouletteEnv, RouletteConfig

def make_env(cfg: RouletteConfig):
    def _thunk():
        return Monitor(RouletteEnv(cfg))
    return _thunk

def train(args):
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / "sac_roulette.zip"
    log_csv = out_dir / "training_episodes.csv"

    cfg = RouletteConfig(
        initial_bankroll=100.0,
        bet_fraction=args.bet_fraction,
        max_steps=args.max_steps,
        target_bankroll=args.target_bankroll,
        random_seed=args.seed,
        use_wheel_layout=True,
    )

    env = DummyVecEnv([make_env(cfg)])

    model = SAC(
        "MlpPolicy",
        env,
        verbose=1,
        gamma=0.999,
        learning_rate=3e-4,
        buffer_size=200_000,
        batch_size=256,
        tau=0.02,
        train_freq=64,
        gradient_steps=64,
        ent_coef="auto",
        seed=args.seed,
        device="auto",
    )

    model.learn(total_timesteps=args.timesteps, log_interval=10)
    model.save(str(model_path))
    print(f"[OK] Modelo guardado en: {model_path}")

    # Evaluación-resumen
    n_eval_eps = args.eval_episodes
    returns, lengths, final_bankrolls = [], [], []

    env_eval = RouletteEnv(cfg)
    for ep in range(n_eval_eps):
        obs, _ = env_eval.reset()
        done = False
        ep_ret = 0.0
        steps = 0
        last_info = {"bankroll": float(cfg.initial_bankroll)}  # fallback
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, r, term, trunc, info = env_eval.step(action)
            last_info = info
            ep_ret += float(r)
            steps += 1
            done = bool(term or trunc)
        returns.append(ep_ret)
        lengths.append(steps)
        final_bankrolls.append(float(last_info["bankroll"]))

    with log_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["episode", "return", "length", "final_bankroll"])
        for i, (r, l, b) in enumerate(zip(returns, lengths, final_bankrolls), 1):
            w.writerow([i, f"{r:.4f}", l, f"{b:.2f}"])
    print(f"[OK] CSV de evaluación: {log_csv}")
    print(f"Return medio: {np.mean(returns):.2f} ± {np.std(returns):.2f}")
    print(f"Bankroll final medio: {np.mean(final_bankrolls):.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=500_000)
    parser.add_argument("--bet_fraction", type=float, default=0.10)
    parser.add_argument("--max_steps", type=int, default=2_000)
    parser.add_argument("--target_bankroll", type=float, default=200.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--eval_episodes", type=int, default=50)
    parser.add_argument("--out_dir", type=str, default="models")
    args = parser.parse_args()
    train(args)
