# Ruleta SAC — ¿Puede la IA "ganar" la ruleta?

Entrené un agente de **Reinforcement Learning (SAC)** para jugar a la **ruleta europea**.
Spoiler: confirmó lo que dicen las matemáticas — en un juego con esperanza negativa
(~**−2.7%**) **no hay** estrategia ganadora sostenida.

> Este repo incluye: simulación Gymnasium de ruleta, entrenamiento con Stable-Baselines3,
> evaluación con bancas pequeñas/grandes y una demo visual en pygame.

---

## 🧠 Idea en 30 segundos

- **Entorno:** ruleta europea (un cero), acciones continuas → softmax a distribución de apuestas.
- **Apuestas disponibles (10):** `RED, BLACK, EVEN, ODD, LOW (1–18), HIGH (19–36), N7, N17, N23, N32`.
- **Recompensa por paso:** `ganancia - stake` (stake = 10% de la banca por defecto).
- **Objetivo del RL:** aprender a distribuir las apuestas para "hacer crecer" la banca dentro del episodio.

> ⚠️ La ruleta tiene **edge** del casino \(-1/37 ≈ -2.70\%\).
> Todas las apuestas (y combinaciones) comparten esa esperanza negativa.

---

## 🛠️ Instalación

Con **conda**:

```bash
conda create -n pygame python=3.11 -c conda-forge -y
conda activate pygame
pip install -r requirements.txt
```

En VS Code selecciona el intérprete del entorno (Python: Select Interpreter).

---

## 🚀 Entrenamiento (bankroll = $100)

```bash
python train_sac.py --timesteps 500000 --eval_episodes 50
```

- Modelo guardado: `models/sac_roulette.zip`
- Métricas de evaluación corta: `models/training_episodes.csv`
  - columnas: episodio, retorno, pasos, banca final

Parámetros útiles:

| parámetro        | descripción                                 | por defecto |
|------------------|---------------------------------------------|-------------|
| `--bet_fraction` | fracción de la banca apostada por paso      | 0.10        |
| `--max_steps`    | pasos máximos por episodio                  | 2000        |
| `--target_bankroll` | meta para terminar antes                  | 200.0       |

---

## 🧪 Evaluación (bankroll grande)

Ejemplo con $1.000.000:

```bash
python evaluate_policy.py \
  --model models/sac_roulette.zip \
  --bankroll 1000000 \
  --episodes 50 \
  --out_csv eval_large_bankroll.csv
```

Salida (`CSV`): `episode, initial_bankroll, final_bankroll, profit, steps`

Observaciones típicas:

- Pocos episodios duplican la banca (rachas favorables).
- La mayoría termina en quiebra o casi 0 antes de `max_steps`.
- Promedio final negativo, coherente con el edge del juego.

---

## 📈 Visualización rápida

Con el CSV de evaluación:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("eval_large_bankroll.csv")
plt.figure(figsize=(10,5))
plt.plot(df["episode"], df["final_bankroll"], marker="o", alpha=0.7)
plt.axhline(y=df["initial_bankroll"][0], linestyle="--", label="Banca inicial")
plt.xlabel("Episodio")
plt.ylabel("Capital final ($)")
plt.title("Capital final por episodio — Evaluación SAC en Ruleta")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("capital_vs_episodios.png", dpi=300, bbox_inches="tight")
```

Coloca la imagen generada en `result_examples/`.

---

## 🎲 Demo visual (opcional)

`main.py` implementa la ruleta en **pygame** con rueda y bola animadas.  Útil para
presentaciones o probar manualmente.

```bash
python main.py
```

---

## 📂 Archivos principales

| archivo               | descripción                                        |
|-----------------------|----------------------------------------------------|
| `roulette_env_sb3.py` | Entorno Gymnasium de ruleta europea                |
| `train_sac.py`        | Entrena SAC con banca inicial $100                 |
| `evaluate_policy.py`  | Evalúa el modelo con bancas grandes y exporta CSV  |
| `main.py`             | Juego visual en pygame (demo)                      |
| `requirements.txt`    | Dependencias                                      |

---

## 🧰 Solución de problemas

- **Pylance "import no resuelto"**: Selecciona el intérprete correcto en VS Code.
- **PyTorch CPU/GPU**: Instala `pytorch-cuda` si tienes GPU NVIDIA (`conda install pytorch-cuda=12.1 -c nvidia -c pytorch`).
- **ModuleNotFoundError**: Ejecuta `pip install -r requirements.txt` dentro del entorno activado.

---

## ⚖️ Licencia

[MIT](LICENSE) — uso libre con atribución.

