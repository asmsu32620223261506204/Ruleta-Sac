# Roulette SAC — Can AI Beat the House?

I trained a **Soft Actor-Critic (SAC)** agent to play **European roulette**.
Spoiler: mathematics wins — in a game with a negative expectation (~**−2.7%**) there is **no** sustainable winning strategy.

> This repo provides a Gymnasium roulette environment, SAC training with Stable-Baselines3, evaluation scripts for small/large bankrolls and a simple pygame demo.

---

## 🧠 Idea in 30 Seconds

- **Environment:** European roulette (single zero), continuous action → softmax over bet distribution.
- **Available bets (10):** `RED, BLACK, EVEN, ODD, LOW (1–18), HIGH (19–36), N7, N17, N23, N32`.
- **Reward per step:** `win - stake` (stake = 10% of bankroll by default).
- **Goal of RL:** learn how to distribute bets to "grow" the bankroll within each episode.

> ⚠️ Roulette has a **house edge** of \(-1/37 ≈ -2.70\%\).
> Every bet (and combination of bets) shares that negative expectation.

---

## 🛠️ Installation

Using **conda**:

```bash
conda create -n pygame python=3.11 -c conda-forge -y
conda activate pygame
pip install -r requirements.txt
```

In VS Code pick the interpreter from this environment (Python: Select Interpreter).

---

## 🚀 Training (bankroll = $100)

```bash
python train_sac.py --timesteps 500000 --eval_episodes 50
```

- Model saved at `models/sac_roulette.zip`
- Short evaluation metrics: `models/training_episodes.csv`
  - columns: episode, return, steps, final_bankroll

Useful parameters:

| parameter          | description                                   | default |
|--------------------|-----------------------------------------------|---------|
| `--bet_fraction`   | fraction of bankroll wagered each step        | 0.10    |
| `--max_steps`      | maximum steps per episode                     | 2000    |
| `--target_bankroll`| goal to finish early                          | 200.0   |

---

## 🧪 Evaluation (large bankroll)

Example with $1,000,000:

```bash
python evaluate_policy.py \
  --model models/sac_roulette.zip \
  --bankroll 1000000 \
  --episodes 50 \
  --out_csv eval_large_bankroll.csv
```

Output (`CSV`): `episode, initial_bankroll, final_bankroll, profit, steps`

Typical observations:

- A few episodes double the bankroll thanks to lucky streaks.
- Most episodes go broke or near zero before `max_steps`.
- Average final capital is negative, consistent with the game's edge.

---

## 📈 Quick Visualization

With the evaluation CSV:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("eval_large_bankroll.csv")
plt.figure(figsize=(10,5))
plt.plot(df["episode"], df["final_bankroll"], marker="o", alpha=0.7)
plt.axhline(y=df["initial_bankroll"][0], linestyle="--", label="Initial bankroll")
plt.xlabel("Episode")
plt.ylabel("Final capital ($)")
plt.title("Final capital per episode — SAC Roulette Evaluation")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("capital_vs_episodes.png", dpi=300, bbox_inches="tight")
```

Place the generated image in `result_examples/`.

---

## 🎲 Visual Demo (optional)

`main.py` implements the roulette wheel in **pygame** with animated wheel and ball. Handy for presentations or manual play.

```bash
python main.py
```

---

## 📂 Key Files

| file                 | description                                          |
|----------------------|------------------------------------------------------|
| `roulette_env_sb3.py`| Gymnasium environment for European roulette          |
| `train_sac.py`       | Trains SAC with $100 initial bankroll                |
| `evaluate_policy.py` | Evaluates the model with large bankrolls and exports CSV |
| `main.py`            | Pygame visual game (demo)                            |
| `requirements.txt`   | Dependencies                                         |

---

## 🧰 Troubleshooting

- **Pylance "unresolved import"**: ensure the correct interpreter is selected in VS Code.
- **PyTorch CPU/GPU**: install `pytorch-cuda` if you have an NVIDIA GPU (`conda install pytorch-cuda=12.1 -c nvidia -c pytorch`).
- **ModuleNotFoundError**: run `pip install -r requirements.txt` inside the activated environment.

---

## ⚖️ License

[MIT](LICENSE) — free use with attribution.