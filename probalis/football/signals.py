"""Indices tirés des statistiques de match (football-data.co.uk) : buts « mérités », corners, cartons.

- Buts mérités : les tirs cadrés (et un peu les tirs non cadrés) annoncent mieux la suite que les buts seuls,
  qui dépendent beaucoup de la chance. On les ramène à l'échelle des buts du championnat.
- Corners et cartons : comptés par équipe, pour les modèles du même nom.

Chaque fonction renvoie une « cible » pour model.fit : (domicile, extérieur) par match, ou None si le match
n'a pas le chiffre (il est alors ignoré, ou remplacé par les buts pour les buts mérités).
"""
from __future__ import annotations

from typing import Callable

from .data import MatchRow

OFF_TARGET_WEIGHT = 0.12  # un tir non cadré « vaut » environ 12 % d'un tir cadré (ordre de grandeur des xG publics)

Target = Callable[[MatchRow], "tuple[float, float] | None"]


def _shots(m: MatchRow) -> tuple[float, float] | None:
    s = m.stats
    if not all(k in s for k in ("HS", "AS", "HST", "AST")):
        return None
    h = s["HST"] + OFF_TARGET_WEIGHT * max(s["HS"] - s["HST"], 0.0)
    a = s["AST"] + OFF_TARGET_WEIGHT * max(s["AS"] - s["AST"], 0.0)
    return h, a


def has_shots(rows: list[MatchRow], min_share: float = 0.5) -> bool:
    played = [m for m in rows if m.played]
    return bool(played) and sum(_shots(m) is not None for m in played) >= min_share * len(played)


def xg_target(rows: list[MatchRow]) -> Target:
    """Buts mérités : tirs pondérés × (buts / tirs pondérés du championnat). Sans tirs : les buts réels."""
    g = s = 0.0
    for m in rows:
        sh = _shots(m) if m.played else None
        if sh:
            g += m.fthg + m.ftag
            s += sh[0] + sh[1]
    k = g / s if s else 0.0

    def target(m: MatchRow) -> tuple[float, float] | None:
        sh = _shots(m) if k else None
        if sh is None:
            return (float(m.fthg), float(m.ftag)) if m.played else None
        return k * sh[0], k * sh[1]

    return target


def corners(m: MatchRow) -> tuple[float, float] | None:
    s = m.stats
    return (s["HC"], s["AC"]) if "HC" in s and "AC" in s else None


def cards(m: MatchRow) -> tuple[float, float] | None:
    """Cartons d'une équipe : jaunes + rouges."""
    s = m.stats
    if "HY" not in s or "AY" not in s:
        return None
    return s["HY"] + s.get("HR", 0.0), s["AY"] + s.get("AR", 0.0)


def has_stat(rows: list[MatchRow], fn: Target, min_share: float = 0.5) -> bool:
    played = [m for m in rows if m.played]
    return bool(played) and sum(fn(m) is not None for m in played) >= min_share * len(played)
