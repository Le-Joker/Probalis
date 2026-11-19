"""Prédiction d'un match : buts attendus, matrices de score, tous les marchés."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core.markets import Market, football_markets
from ..core.scores import half_matrices, score_matrix
from .model import TeamModel


@dataclass
class Prediction:
    home: str
    away: str
    lam: float
    mu: float
    ft: np.ndarray
    markets: list[Market]

    def market(self, key: str, line: float | None = None) -> Market:
        for m in self.markets:
            if m.key == key and (line is None or m.line == line):
                return m
        raise KeyError((key, line))

    def p(self, key: str, sel: str, line: float | None = None) -> float:
        return self.market(key, line).selections[sel].prob


def predict(model: TeamModel, home: str, away: str) -> Prediction:
    lam, mu = model.rates(home, away)
    return predict_from_rates(model, home, away, lam, mu)


def predict_from_rates(model: TeamModel, home: str, away: str, lam: float, mu: float) -> Prediction:
    ft = score_matrix(lam, mu, model.rho)
    h1, h2 = half_matrices(lam, mu, model.first_half_share)
    return Prediction(home, away, lam, mu, ft, football_markets(ft, h1, h2))


def confidence(model: TeamModel, home: str, away: str) -> str:
    """Indice de confiance selon la quantité de données récentes sur les deux équipes."""
    wmin = min(model.weight_by_team.get(home, 0.0), model.weight_by_team.get(away, 0.0))
    if wmin >= 35:
        return "high"
    if wmin >= 15:
        return "medium"
    return "low"
