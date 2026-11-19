"""Buts attendus « implicites » : les (λ, μ) qui reproduisent les cotes du marché.

Les cotes de clôture des grands bookmakers sont très précises sur les marchés principaux.
On retrouve les buts attendus qui collent à ces cotes, puis on en déduit tous les autres
marchés (score exact, mi-temps, combinés…) que le marché évalue souvent moins bien.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares

from .scores import score_matrix


def _probs(lam: float, mu: float, rho: float) -> tuple[np.ndarray, float]:
    m = score_matrix(lam, mu, rho)
    H, A = np.indices(m.shape)
    p1x2 = np.array([m[H > A].sum(), m[H == A].sum(), m[H < A].sum()])
    over = float(m[(H + A) > 2.5].sum())
    return p1x2, over


def implied_rates(p1x2: list[float], rho: float = 0.0, p_over25: float | None = None,
                  start: tuple[float, float] = (1.4, 1.1)) -> tuple[float, float]:
    """λ, μ tels que le modèle reproduise le 1X2 (et le plus/moins 2,5 s'il est fourni) du marché."""
    target = np.asarray(p1x2, dtype=float)

    def resid(x: np.ndarray) -> np.ndarray:
        lam, mu = np.exp(x)
        p, over = _probs(lam, mu, rho)
        r = [p[0] - target[0], p[2] - target[2]]
        if p_over25 is not None:
            r.append(over - p_over25)
        return np.array(r)

    sol = least_squares(resid, np.log(np.maximum(start, 0.05)), bounds=(np.log(0.05), np.log(6.0)))
    lam, mu = np.exp(sol.x)
    return float(lam), float(mu)
