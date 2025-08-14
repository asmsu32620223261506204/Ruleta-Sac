# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from pathlib import Path
import csv
import numpy as np
from stable_baselines3 import SAC

from roulette_env_sb3 import RouletteEnv, RouletteConfig

def evaluate(model_path: Path, bankroll: float, episodes: int, bet_fraction: float,
             max_steps: int, target_bankroll: float, seed: int, out_csv: Path):
    cfg = RouletteConfig(
        initial_bankroll=bankroll,
        bet_fraction=bet_fraction,
        max_steps=max_steps,
        target_bankroll=target_bankroll,
        random_seed=seed,
        use_wheel_layout=True,
    )

    env = RouletteEnv(cfg)
    model = SAC.load(str(model_path))

    returns, lens, finals = [], [], []

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["episode", "initial_bankroll", "final_bankroll", "profit", "steps"])
        for ep in range(1, episodes+1):
            obs, _ = env.reset()
            ini = float(cfg.initial_bankroll)
            done = False
            ep_ret = 0.0
            steps = 0
            last_info = {"bankroll": ini}  # fallback por si el episodio termina en 0 pasos
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                obs, r, term, trunc, info = env.step(action)
                last_info = info
                ep_ret += float(r)
                steps += 1
                done = bool(term or trunc)
            fin = float(last_info["bankroll"])
            profit = fin - ini
            returns.append(ep_ret)
            lens.append(steps)
            finals.append(fin)
            w.writerow([ep, f"{ini:.2f}", f"{fin:.2f}", f"{profit:.2f}", steps])

    print(f"[OK] Evaluación -> {out_csv}")
    print(f"Episodios: {episodes}")
    print(f"Return medio: {np.mean(returns):.2f} ± {np.std(returns):.2f}")
    print(f"Bankroll final medio: {np.mean(finals):.2f}")
    print(f"Profit medio: {np.mean(np.array(finals) - bankroll):.2f}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", type=str, default="models/sac_roulette.zip")
    p.add_argument("--episodes", type=int, default=20)
    p.add_argument("--bankroll", type=float, default=1_000_000.0)
    p.add_argument("--bet_fraction", type=float, default=0.10)
    p.add_argument("--max_steps", type=int, default=2_000)
    p.add_argument("--target_bankroll", type=float, default=2_000_000.0)
    p.add_argument("--seed", type=int, default=123)
    p.add_argument("--out_csv", type=str, default="eval_large_bankroll.csv")
    args = p.parse_args()

    evaluate(
        model_path=Path(args.model),
        bankroll=args.bankroll,
        episodes=args.episodes,
        bet_fraction=args.bet_fraction,
        max_steps=args.max_steps,
        target_bankroll=args.target_bankroll,
        seed=args.seed,
        out_csv=Path(args.out_csv),
    )
