
# Roulette Wheel Game (European) — Pygame

Juego de **ruleta europea** con rueda visual, bola animada y apuestas básicas.

## Características
- Rueda europea en el orden real de números (0–36) y colores correctos.
- Animación de rueda y bola con desaceleración.
- Panel lateral con **bankroll**, **apuesta por ficha** y **boleta de apuestas**.
- Apuestas soportadas: **RED, BLACK, EVEN, ODD, LOW, HIGH, STRAIGHT (número exacto)**.
- Liquidación automática con pagos 1:1 (apuestas pares) y 35:1 (número exacto).

> **Nota:** Esto es educativo; la ruleta tiene valor esperado negativo.

## Requisitos
```bash
pip install pygame
```

## Cómo ejecutar
```bash
python main.py
```

## Controles
- `SPACE`  → Girar
- `C`      → Limpiar boleta
- `↑/↓`    → Cambiar valor de ficha
- `1..6`   → Agregar apuesta con la ficha actual
  - 1 RED, 2 BLACK, 3 EVEN, 4 ODD, 5 LOW, 6 HIGH
- `S`      → Modo STRAIGHT (número exacto)
- `←/→`    → Cambiar número cuando STRAIGHT esté activo
- `ENTER`  → Agregar apuesta STRAIGHT con la ficha actual

## Próximos pasos (opcionales)
- Agregar docenas/columnas/semidocenas, vecinos del cero, etc.
- Sonidos y partículas para más “feeling”.
- Historial y estadística de últimos 20 resultados.
- Exportar resultados a CSV para análisis.
