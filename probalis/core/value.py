"""Mathématiques des cotes : marge du bookmaker, cote juste, valeur (espérance)."""
from __future__ import annotations

from dataclasses import dataclass
from math import prod


@dataclass(frozen=True)
class Outcome:
    """Issue d'un pari. Gère les paris simples et les lignes asiatiques (remboursement, demi-gain, demi-perte)."""

    win: float
    half_win: float = 0.0
    push: float = 0.0
    half_loss: float = 0.0
    loss: float = 0.0

    @classmethod
    def simple(cls, p: float) -> "Outcome":
        p = min(max(float(p), 0.0), 1.0)
        return cls(win=p, loss=1.0 - p)

    @property
    def prob(self) -> float:
        """Probabilité d'être payé, entièrement ou à moitié."""
        return self.win + self.half_win

    @property
    def fair_odds(self) -> float | None:
        """Cote à laquelle le pari a une espérance nulle."""
        gain = self.win + self.half_win / 2
        risk = self.loss + self.half_loss / 2
        if gain <= 1e-12:
            return None
        return 1.0 + risk / gain

    def ev(self, odds: float) -> float:
        """Espérance de gain pour 1 misé à la cote donnée (0,10 = +10 %)."""
        g = odds - 1.0
        return self.win * g + self.half_win * g / 2 - self.half_loss / 2 - self.loss


def margin(odds: list[float]) -> float:
    """Marge du bookmaker sur un marché complet (0,05 = 5 %)."""
    return sum(1.0 / o for o in odds) - 1.0


def devig(odds: list[float]) -> list[float]:
    """Probabilités « justes » du bookmaker, marge retirée proportionnellement."""
    inv = [1.0 / o for o in odds]
    s = sum(inv)
    return [i / s for i in inv]


def devig_power(odds: list[float]) -> list[float]:
    """Marge retirée par la méthode « puissance » : p_i = (1/cote_i)^k, k choisi pour que la somme fasse 1.
    Retire plus de marge sur les grosses cotes (les outsiders sont en général trop peu payés)."""
    inv = [1.0 / o for o in odds]
    lo, hi = 1.0, 3.0
    if sum(inv) < 1.0:
        lo, hi = 0.3, 1.0
    for _ in range(60):
        k = (lo + hi) / 2
        if sum(i ** k for i in inv) > 1.0:
            lo = k
        else:
            hi = k
    k = (lo + hi) / 2
    ps = [i ** k for i in inv]
    s = sum(ps)
    return [p / s for p in ps]


def devig_shin(odds: list[float]) -> list[float]:
    """Marge retirée par la méthode de Shin (part de parieurs « initiés » z estimée à partir des cotes)."""
    inv = [1.0 / o for o in odds]
    s = sum(inv)
    if s <= 1.0:
        return [i / s for i in inv]

    def probs(z: float) -> list[float]:
        return [((z * z + 4 * (1 - z) * i * i / s) ** 0.5 - z) / (2 * (1 - z)) for i in inv]

    lo, hi = 0.0, 0.4
    for _ in range(60):
        z = (lo + hi) / 2
        if sum(probs(z)) > 1.0:
            lo = z
        else:
            hi = z
    ps = probs((lo + hi) / 2)
    t = sum(ps)
    return [p / t for p in ps]


DEVIG = {"proportional": devig, "power": devig_power, "shin": devig_shin}


def devig_by(method: str, odds: list[float]) -> list[float]:
    return DEVIG.get(method, devig)(odds)


def blend(p_model: float, p_market: float, weight_model: float) -> float:
    """Mélange de la probabilité du modèle et de celle du marché."""
    return weight_model * p_model + (1.0 - weight_model) * p_market


@dataclass(frozen=True)
class Accumulator:
    prob: float
    odds: float

    @property
    def ev(self) -> float:
        return self.prob * self.odds - 1.0


def accumulator(probs: list[float], odds: list[float]) -> Accumulator:
    """Combiné de sélections indépendantes (matchs différents)."""
    return Accumulator(prob=prod(probs), odds=prod(odds))
