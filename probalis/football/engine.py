"""Moteur d'analyse Probalis : plusieurs indices pesés ensemble, puis vérifiés sur le passé.

Pour chaque match, comme un analyste qui recoupe ses sources :
1. force de fond (attaque et défense sur 3 saisons, modèle de Dixon-Coles sur les buts) ;
2. buts « mérités » (tirs et tirs cadrés), moins soumis à la chance que les buts ;
3. forme récente (même modèle avec une mémoire de quelques mois) ;
4. avantage du terrain du championnat ;
5. cotes des bookmakers quand elles existent (marge retirée), mélangées au lieu d'être recopiées ;
6. quantité de données (confiance).

Les poids viennent de football/engine_params.json, appris et testés par football/tune.py sur des saisons
que le moteur n'a pas vues. Sans ce fichier, le moteur redonne exactement l'ancien calcul (buts seuls,
cotes recopiées), ce qui sert de filet de sécurité.

Sortie : les buts attendus (λ, μ) → la même matrice de scores et les mêmes 93 marchés qu'avant, plus les
corners et cartons quand les données existent, et la liste des raisons (« facteurs ») de l'analyse.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, fields
from datetime import date
from pathlib import Path

from ..core.counts import card_markets, corner_markets
from ..core.implied import implied_rates
from ..core.value import devig_by
from . import signals
from .data import MatchRow
from .model import TeamModel, fit
from .predict import Prediction, confidence, predict_from_rates

PARAMS_PATH = Path(__file__).resolve().parent / "engine_params.json"


@dataclass
class EngineParams:
    version: str = "v1"
    w_xg: float = 0.0          # part des buts mérités (tirs) dans la force des équipes
    w_form: float = 0.0        # part de la forme récente
    form_target: str = "goals"  # la forme se mesure sur les buts ("goals") ou les buts mérités ("xg")
    xi_form: float = 0.008     # mémoire de la forme : demi-vie d'environ 3 mois
    t: float = 1.0             # écart entre les deux équipes (1 = tel quel)
    s: float = 1.0             # nombre total de buts (1 = tel quel)
    w_mkt: float = 1.0         # part des cotes quand elles existent (1 = cotes seules, comme avant)
    devig: str = "proportional"  # façon de retirer la marge du bookmaker
    corners_size: float | None = None  # dispersion des corners (None : pas de marchés de corners)
    cards_size: float | None = None    # dispersion des cartons (None : pas de marchés de cartons)
    corners_shrink: float = 1.0        # part de l'écart propre aux équipes (0 = moyenne du championnat)
    cards_shrink: float = 1.0
    reliability: dict = field(default_factory=dict)  # verdicts comparables : annoncé et réussi (tune.py)
    meta: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "EngineParams":
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in names})

    def to_dict(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self)}


_PARAMS: EngineParams | None = None


def load_params(path: Path = PARAMS_PATH) -> EngineParams:
    global _PARAMS
    if _PARAMS is None or path != PARAMS_PATH:
        try:
            p = EngineParams.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError):
            p = EngineParams()
        if path != PARAMS_PATH:
            return p
        _PARAMS = p
    return _PARAMS


# --- Modèles d'un championnat ----------------------------------------------------------------------------

@dataclass
class LeagueModels:
    goals: TeamModel
    xg: TeamModel | None = None
    form: TeamModel | None = None
    corners: TeamModel | None = None
    cards: TeamModel | None = None
    season_teams: list[str] = field(default_factory=list)


def _try_fit(hist: list[MatchRow], ref: date, include_ref_day: bool, **kw) -> TeamModel | None:
    try:
        return fit(hist, ref, include_ref_day=include_ref_day, **kw)
    except ValueError:
        return None


def fit_league(hist: list[MatchRow], ref_date: date, params: EngineParams | None = None,
               include_ref_day: bool = False, counts: bool = True,
               season_teams: list[str] | None = None) -> LeagueModels:
    """Tous les modèles d'un championnat à la date ref_date (que des matchs d'avant, sauf include_ref_day)."""
    p = params or load_params()
    goals = fit(hist, ref_date, include_ref_day=include_ref_day)
    shots = signals.has_shots([m for m in hist if (ref_date - m.date).days <= 365])
    xg_t = signals.xg_target(hist) if shots else None
    xg = _try_fit(hist, ref_date, include_ref_day, target=xg_t) if (p.w_xg > 0 and xg_t) else None
    form = None
    if p.w_form > 0:
        tgt = xg_t if (p.form_target == "xg" and xg_t) else None
        form = _try_fit(hist, ref_date, include_ref_day, xi=p.xi_form, target=tgt)
    corners = cards = None
    if counts:
        recent = [m for m in hist if (ref_date - m.date).days <= 365]
        if p.corners_size is not None and signals.has_stat(recent, signals.corners):
            corners = _try_fit(hist, ref_date, include_ref_day, target=signals.corners)
        if p.cards_size is not None and signals.has_stat(recent, signals.cards):
            cards = _try_fit(hist, ref_date, include_ref_day, target=signals.cards)
    return LeagueModels(goals, xg, form, corners, cards, list(season_teams or []))


# --- Buts attendus ---------------------------------------------------------------------------------------

def _log_rates(m: TeamModel | None, home: str, away: str) -> tuple[float, float] | None:
    if m is None or not (m.knows(home) and m.knows(away)):
        return None
    lam, mu = m.rates(home, away)
    return math.log(lam), math.log(mu)


def transform(lam: float, mu: float, t: float, s: float) -> tuple[float, float]:
    """Étire l'écart entre les équipes (t) et le total de buts (s), sans changer le reste."""
    a = (math.log(lam) + math.log(mu)) / 2 + math.log(s)
    d = (math.log(lam) - math.log(mu)) / 2 * t
    return math.exp(a + d), math.exp(a - d)


def ensemble_rates(lm: LeagueModels, home: str, away: str, p: EngineParams) -> tuple[float, float, dict]:
    """Buts attendus du moteur seul (sans les cotes) et la part de chaque indice (en log)."""
    base = _log_rates(lm.goals, home, away)
    if base is None:
        raise KeyError((home, away))
    terms = {}
    lx = _log_rates(lm.xg, home, away)
    if lx and p.w_xg:
        terms["shots"] = (p.w_xg * (lx[0] - base[0]), p.w_xg * (lx[1] - base[1]))
    lf = _log_rates(lm.form, home, away)
    if lf and p.w_form:
        terms["form"] = (p.w_form * (lf[0] - base[0]), p.w_form * (lf[1] - base[1]))
    ll = base[0] + sum(t[0] for t in terms.values())
    lmu = base[1] + sum(t[1] for t in terms.values())
    lam, mu = transform(math.exp(ll), math.exp(lmu), p.t, p.s)
    return lam, mu, terms


def market_rates(o1x2: list[float], o_ou25: list[float] | None, rho: float, p: EngineParams,
                 start: tuple[float, float]) -> tuple[float, float]:
    p1x2 = devig_by(p.devig, o1x2)
    p_over = devig_by(p.devig, o_ou25)[0] if o_ou25 else None
    return implied_rates(p1x2, rho, p_over, start=start)


def mix(model: tuple[float, float], market: tuple[float, float], w_mkt: float) -> tuple[float, float]:
    return (math.exp(w_mkt * math.log(market[0]) + (1 - w_mkt) * math.log(model[0])),
            math.exp(w_mkt * math.log(market[1]) + (1 - w_mkt) * math.log(model[1])))


# --- Analyse d'un match ----------------------------------------------------------------------------------

@dataclass
class Analysis:
    pred: Prediction            # analyse publiée (avec les cotes si elles existent)
    model_pred: Prediction      # moteur seul
    source: str                 # "market" (cotes mélangées) ou "model"
    confidence: str
    factors: list[dict]
    counts: dict = field(default_factory=dict)  # {"corners": (h, a), "cards": (h, a)}


def _rank(model: TeamModel, team: str, attack: bool, pool: list[str]) -> tuple[int, int]:
    teams = [t for t in pool if model.knows(t)] or list(model.teams)
    if team not in teams:
        teams.append(team)
    idx = model._idx  # noqa: SLF001
    vals = sorted(teams, key=lambda t: -model.attack[idx[t]] if attack else model.defence[idx[t]])
    return vals.index(team) + 1, len(teams)


def factors(lm: LeagueModels, home: str, away: str, lam: float, mu: float, terms: dict,
            mkt_terms: tuple[float, float] | None, conf: str) -> list[dict]:
    """Raisons de l'analyse, chiffrées en buts : ce que chaque indice ajoute (ou retire) aux buts attendus."""
    m = lm.goals
    i, j = m._idx[home], m._idx[away]  # noqa: SLF001
    out = []

    def delta(rate: float, term: float) -> float:
        return rate * (1 - math.exp(-term))

    pool = lm.season_teams
    for side, team, idx, rate_for, rate_against in (("h", home, i, lam, mu), ("a", away, j, mu, lam)):
        r, n = _rank(m, team, True, pool)
        out.append({"k": "att", "side": side, "d": round(delta(rate_for, float(m.attack[idx])), 3),
                    "rank": r, "n": n, "v": round(math.exp(m.intercept + float(m.attack[idx])), 2)})
        r, n = _rank(m, team, False, pool)
        out.append({"k": "def", "side": side, "d": round(-delta(rate_against, float(m.defence[idx])), 3),
                    "rank": r, "n": n, "v": round(math.exp(m.intercept + float(m.defence[idx])), 2)})
    out.append({"k": "home", "side": "h", "d": round(delta(lam, m.home_adv), 3)})
    for key in ("shots", "form"):
        if key in terms:
            th, ta = terms[key]
            out.append({"k": key, "side": "h", "d": round(delta(lam, th), 3)})
            out.append({"k": key, "side": "a", "d": round(delta(mu, ta), 3)})
    if mkt_terms:
        out.append({"k": "market", "side": "h", "d": round(delta(lam, mkt_terms[0]), 3)})
        out.append({"k": "market", "side": "a", "d": round(delta(mu, mkt_terms[1]), 3)})
    out = [f for f in out if abs(f["d"]) >= 0.02 or f["k"] in ("att", "def")]
    out.sort(key=lambda f: -abs(f["d"]))
    top = out[:5]
    if conf != "high":
        top.append({"k": "data", "side": "both", "d": 0.0, "conf": conf})
    return top


def analyse(lm: LeagueModels, home: str, away: str, o1x2: list[float] | None = None,
            o_ou25: list[float] | None = None, params: EngineParams | None = None) -> Analysis:
    p = params or load_params()
    lam_e, mu_e, terms = ensemble_rates(lm, home, away, p)
    model_pred = predict_from_rates(lm.goals, home, away, lam_e, mu_e)
    conf = confidence(lm.goals, home, away)
    pred, source, mkt_terms = model_pred, "model", None
    if o1x2:
        lam_m, mu_m = market_rates(o1x2, o_ou25, lm.goals.rho, p, start=(lam_e, mu_e))
        lam, mu = mix((lam_e, mu_e), (lam_m, mu_m), p.w_mkt)
        pred = predict_from_rates(lm.goals, home, away, lam, mu)
        source, conf = "market", "high"
        mkt_terms = (math.log(lam / lam_e), math.log(mu / mu_e))
    counts = add_counts(pred, lm.corners, lm.cards, home, away, p)
    return Analysis(pred, model_pred, source, conf,
                    factors(lm, home, away, pred.lam, pred.mu, terms, mkt_terms, conf), counts)


def shrink(rate: tuple[float, float], base: tuple[float, float], k: float) -> tuple[float, float]:
    """Rapproche les chiffres d'un match de la moyenne du championnat (k = 0 : la moyenne ; 1 : tel quel).
    Les corners et cartons dépendent beaucoup du hasard et de l'arbitre : l'écart propre aux équipes doit
    être pris avec prudence (k appris sur les saisons passées)."""
    return (math.exp(math.log(base[0]) + k * (math.log(rate[0]) - math.log(base[0]))),
            math.exp(math.log(base[1]) + k * (math.log(rate[1]) - math.log(base[1]))))


def count_rates(m: TeamModel, home: str, away: str) -> tuple[tuple[float, float], tuple[float, float]]:
    """(chiffres attendus du match, moyenne du championnat à domicile et à l'extérieur)."""
    return m.rates(home, away), (math.exp(m.intercept + m.home_adv), math.exp(m.intercept))


def add_counts(pred: Prediction, corners: TeamModel | None, cards: TeamModel | None, home: str, away: str,
               p: EngineParams, rates: dict | None = None) -> dict:
    """Ajoute les marchés de corners et de cartons à la prédiction (si on a les données des deux équipes).

    rates : chiffres déjà connus {"corners": ((h, a), (base_h, base_a)), "cards": …} (coupes d'Europe)."""
    raw = dict(rates or {})
    if "corners" not in raw and corners is not None and corners.knows(home) and corners.knows(away):
        raw["corners"] = count_rates(corners, home, away)
    if "cards" not in raw and cards is not None and cards.knows(home) and cards.knows(away):
        raw["cards"] = count_rates(cards, home, away)
    out = {}
    if "corners" in raw and p.corners_size is not None:
        out["corners"] = shrink(*raw["corners"], p.corners_shrink)
        pred.markets += corner_markets(*out["corners"], p.corners_size)
    if "cards" in raw and p.cards_size is not None:
        out["cards"] = shrink(*raw["cards"], p.cards_shrink)
        pred.markets += card_markets(*out["cards"], p.cards_size)
    return {k: (round(v[0], 3), round(v[1], 3)) for k, v in out.items()}
