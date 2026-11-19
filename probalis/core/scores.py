"""Distributions de scores : Poisson et correction de Dixon-Coles."""
from __future__ import annotations

import numpy as np
from scipy.stats import poisson

MAX_GOALS = 10


def poisson_vector(rate: float, max_goals: int = MAX_GOALS) -> np.ndarray:
    """P(X = 0..max_goals) ; la dernière case reçoit aussi la queue (max_goals et plus)."""
    p = poisson.pmf(np.arange(max_goals + 1), rate)
    p[-1] += max(0.0, 1.0 - p.sum())
    return p


def dc_tau(x: np.ndarray, y: np.ndarray, lam: np.ndarray, mu: np.ndarray, rho: float) -> np.ndarray:
    """Facteur de correction de Dixon-Coles pour les petits scores (0-0, 1-0, 0-1, 1-1)."""
    tau = np.ones(np.broadcast(x, y, lam, mu).shape)
    tau = np.where((x == 0) & (y == 0), 1 - lam * mu * rho, tau)
    tau = np.where((x == 0) & (y == 1), 1 + lam * rho, tau)
    tau = np.where((x == 1) & (y == 0), 1 + mu * rho, tau)
    tau = np.where((x == 1) & (y == 1), 1 - rho, tau)
    return tau


def score_matrix(lam: float, mu: float, rho: float = 0.0, max_goals: int = MAX_GOALS) -> np.ndarray:
    """Matrice M[h, a] = P(score domicile h, score extérieur a), somme = 1."""
    m = np.outer(poisson_vector(lam, max_goals), poisson_vector(mu, max_goals))
    if rho:
        g = np.arange(max_goals + 1)
        m = m * dc_tau(g[:, None], g[None, :], lam, mu, rho)
        m = np.clip(m, 0.0, None)
    return m / m.sum()


def half_matrices(lam: float, mu: float, first_half_share: float, max_goals: int = 8):
    """Matrices de score de la 1re et de la 2e mi-temps (buts indépendants par mi-temps)."""
    f = first_half_share
    h1 = score_matrix(lam * f, mu * f, 0.0, max_goals)
    h2 = score_matrix(lam * (1 - f), mu * (1 - f), 0.0, max_goals)
    return h1, h2
