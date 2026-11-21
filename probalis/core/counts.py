"""Corners et cartons : lois de comptage et marchés.

Chaque équipe obtient un nombre de corners (ou reçoit un nombre de cartons) qui suit une loi binomiale
négative : comme Poisson, mais plus dispersée (certains matchs en ont beaucoup plus que la moyenne).
« size » règle cette dispersion (grand = proche de Poisson) ; elle est apprise sur les saisons passées
(football/tune.py). Les deux équipes sont supposées indépendantes, la dispersion du total absorbe le reste.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import nbinom, poisson

from .markets import Market
from .value import Outcome

S = Outcome.simple

CORNER_LINES = (7.5, 8.5, 9.5, 10.5, 11.5)
CORNER_TEAM_LINES = (3.5, 4.5, 5.5)
CARD_LINES = (2.5, 3.5, 4.5, 5.5)
CARD_TEAM_LINES = (1.5, 2.5)


def count_pmf(mean: float, size: float | None, n_max: int) -> np.ndarray:
    """P(X = 0..n_max) ; la dernière case reçoit la queue."""
    k = np.arange(n_max + 1)
    if not size or size <= 0 or size > 1e4:
        p = poisson.pmf(k, mean)
    else:
        p = nbinom.pmf(k, size, size / (size + mean))
    p[-1] += max(0.0, 1.0 - p.sum())
    return p


def count_matrix(mean_h: float, mean_a: float, size: float | None, n_max: int) -> np.ndarray:
    m = np.outer(count_pmf(mean_h, size, n_max), count_pmf(mean_a, size, n_max))
    return m / m.sum()


def _p(m: np.ndarray, mask: np.ndarray) -> float:
    return float(m[mask].sum())


def corner_markets(mean_h: float, mean_a: float, size: float | None) -> list[Market]:
    m = count_matrix(mean_h, mean_a, size, 30)
    H, A = np.indices(m.shape)
    T = H + A
    out = [Market("co", "corners", {"over": S(_p(m, T > ln)), "under": S(_p(m, T < ln))}, ln)
           for ln in CORNER_LINES]
    out.append(Market("co1x2", "corners", {"1": S(_p(m, H > A)), "X": S(_p(m, H == A)), "2": S(_p(m, H < A))}))
    for side, G in (("1", H), ("2", A)):
        out += [Market(f"cot{side}", "corners", {"over": S(_p(m, G > ln)), "under": S(_p(m, G < ln))}, ln)
                for ln in CORNER_TEAM_LINES]
    for mk in out:
        mk.meta["mean"] = (round(mean_h, 2), round(mean_a, 2))
    return out


def card_markets(mean_h: float, mean_a: float, size: float | None) -> list[Market]:
    m = count_matrix(mean_h, mean_a, size, 16)
    H, A = np.indices(m.shape)
    T = H + A
    out = [Market("ca", "corners", {"over": S(_p(m, T > ln)), "under": S(_p(m, T < ln))}, ln)
           for ln in CARD_LINES]
    out.append(Market("ca1x2", "corners", {"1": S(_p(m, H > A)), "X": S(_p(m, H == A)), "2": S(_p(m, H < A))}))
    for side, G in (("1", H), ("2", A)):
        out += [Market(f"cat{side}", "corners", {"over": S(_p(m, G > ln)), "under": S(_p(m, G < ln))}, ln)
                for ln in CARD_TEAM_LINES]
    return out


COUNT_KEYS = {"co": "corners", "co1x2": "corners", "cot1": "corners", "cot2": "corners",
              "ca": "cards", "ca1x2": "cards", "cat1": "cards", "cat2": "cards"}


def settle_count(key: str, line, sel: str, h: float, a: float) -> str:
    """Règlement d'un marché de corners ou de cartons à partir des chiffres du match."""
    if key in ("co", "ca"):
        v = h + a
    elif key in ("cot1", "cat1"):
        v = h
    elif key in ("cot2", "cat2"):
        v = a
    else:  # co1x2, ca1x2
        r = "1" if h > a else ("X" if h == a else "2")
        return "won" if sel == r else "lost"
    if sel == "over":
        return "won" if v > line else "lost"
    return "won" if v < line else "lost"
