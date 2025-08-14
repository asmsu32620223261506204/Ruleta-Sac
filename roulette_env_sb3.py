# -*- coding: utf-8 -*-
# Entorno Gymnasium de Ruleta Europea para SB3 (SAC)
from __future__ import annotations
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from dataclasses import dataclass

# Layout europeo (orden real de la rueda)
WHEEL_ORDER = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30,
               8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7,
               28, 12, 35, 3, 26]
RED_NUMBERS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK_NUMBERS = set(range(1,37)) - RED_NUMBERS
ZERO = 0

OPTION_NAMES = ["RED","BLACK","EVEN","ODD","LOW","HIGH","N7","N17","N23","N32"]

@dataclass
class RouletteConfig:
    initial_bankroll: float = 100.0
    bet_fraction: float = 0.10         # fracción del bankroll apostada por paso
    max_steps: int = 2000
    bankrupt_threshold: float = 0.0
    target_bankroll: float = 200.0
    random_seed: int | None = None
    use_wheel_layout: bool = True      # uniforme por bolsillo (rueda europea)

class RouletteEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, config: RouletteConfig | None = None):
        super().__init__()
        self.cfg = config or RouletteConfig()
        self.rng = np.random.default_rng(self.cfg.random_seed)

        # Acción continua → 10 logits (softmax a pesos de apuesta)
        self.action_space = spaces.Box(low=-8.0, high=8.0, shape=(10,), dtype=np.float32)

        # Observación: bankroll_norm + one-hots del último resultado
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(8,), dtype=np.float32)

        # Atributos con tipos concretos (no Optional)
        self.bankroll: float = float(self.cfg.initial_bankroll)
        self.steps: int = 0
        self.last_n: int = -1  # -1 = no hay último resultado todavía

    # --------- helpers ----------
    def _spin(self) -> int:
        if not self.cfg.use_wheel_layout:
            return int(self.rng.integers(0, 37))
        idx = int(self.rng.integers(0, len(WHEEL_ORDER)))
        return WHEEL_ORDER[idx]

    def _color(self, n: int) -> str:
        if n == ZERO: return "zero"
        return "red" if n in RED_NUMBERS else "black"

    def _parity(self, n: int) -> str:
        if n == ZERO: return "none"
        return "even" if (n % 2) == 0 else "odd"

    def _range(self, n: int) -> str:
        if n == ZERO: return "none"
        return "low" if (1 <= n <= 18) else "high"

    def _obs(self) -> np.ndarray:
        denom = max(self.cfg.initial_bankroll, 1e-9)
        bnorm = float(np.clip(self.bankroll / denom, 0.0, 1.0))
        zero = red = black = even = odd = low = high = 0
        if self.last_n >= 0:
            c = self._color(self.last_n)
            p = self._parity(self.last_n)
            r = self._range(self.last_n)
            if c == "zero": zero = 1
            elif c == "red": red = 1
            elif c == "black": black = 1
            if p == "even": even = 1
            elif p == "odd": odd = 1
            if r == "low": low = 1
            elif r == "high": high = 1
        return np.array([bnorm, zero, red, black, even, odd, low, high], dtype=np.float32)

    # --------- API Gym ----------
    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self.bankroll = float(self.cfg.initial_bankroll)
        self.steps = 0
        self.last_n = -1
        return self._obs(), {}

    def step(self, action: np.ndarray):
        self.steps += 1

        logits = np.array(action, dtype=np.float64).clip(-10, 10)
        exps = np.exp(logits - logits.max())
        weights = exps / exps.sum()

        stake = float(self.cfg.bet_fraction) * float(self.bankroll)
        bets = weights * stake

        n = self._spin()
        self.last_n = n

        # Payouts: even-money 1:1; straight (7,17,23,32) 35:1
        win = 0.0
        if n != ZERO:
            if n in RED_NUMBERS:   win += float(bets[0]) * 2.0  # RED
            if n in BLACK_NUMBERS: win += float(bets[1]) * 2.0  # BLACK
            if (n % 2) == 0:       win += float(bets[2]) * 2.0  # EVEN
            else:                  win += float(bets[3]) * 2.0  # ODD
            if 1 <= n <= 18:       win += float(bets[4]) * 2.0  # LOW
            elif 19 <= n <= 36:    win += float(bets[5]) * 2.0  # HIGH
        if n == 7:   win += float(bets[6]) * 36.0
        if n == 17:  win += float(bets[7]) * 36.0
        if n == 23:  win += float(bets[8]) * 36.0
        if n == 32:  win += float(bets[9]) * 36.0

        reward = float(win - stake)
        self.bankroll = float(self.bankroll + reward)

        terminated = (
            self.bankroll <= float(self.cfg.bankrupt_threshold)
            or self.bankroll >= float(self.cfg.target_bankroll)
            or self.steps >= int(self.cfg.max_steps)
        )
        truncated = False

        info = {
            "number": int(n),
            "bankroll": float(self.bankroll),
            "stake": float(stake),
            "win": float(win),
            "reward": float(reward),
            "weights": weights.astype(np.float32),
        }
        return self._obs(), float(reward), bool(terminated), bool(truncated), info
