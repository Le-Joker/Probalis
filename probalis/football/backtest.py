"""Test de fiabilité : on rejoue une saison passée semaine par semaine.

Pour chaque semaine, le modèle n'apprend que sur les matchs d'avant, puis prédit les matchs
de la semaine. On compare ensuite aux résultats réels et aux cotes de clôture des bookmakers
(les cotes juste avant le coup d'envoi, très difficiles à battre).

Usage : python -m probalis.football.backtest --season 2526 --leagues E0 SP1
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import timedelta

import numpy as np

from ..core.implied import implied_rates
from ..core.scores import score_matrix
from ..core.value import devig
from .data import MatchRow, load_history
from .leagues import BY_CODE, LEAGUES
from .model import DEFAULT_RIDGE, DEFAULT_XI, fit
from .predict import predict

CLOSE_1X2 = (("PSCH", "PSCD", "PSCA"), ("AvgCH", "AvgCD", "AvgCA"), ("B365CH", "B365CD", "B365CA"))
CLOSE_OU = (("PC>2.5", "PC<2.5"), ("AvgC>2.5", "AvgC<2.5"), ("B365C>2.5", "B365C<2.5"))


def _odds(m: MatchRow, choices) -> list[float] | None:
    for cols in choices:
        vals = [m.odds.get(c) for c in cols]
        if all(vals):
            return vals
    return None


def _prev_season(season: str) -> str:
    a = int(season[:2]) - 1
    return f"{a % 100:02d}{(a + 1) % 100:02d}"


@dataclass
class Score:
    n: int = 0
    ll_model: float = 0.0
    ll_market: float = 0.0
    ll_blend: dict = field(default_factory=lambda: defaultdict(float))
    brier_model: float = 0.0
    brier_market: float = 0.0

    def add(self, p_model: np.ndarray, p_market: np.ndarray, k: int) -> None:
        e = np.zeros(len(p_model))
        e[k] = 1
        self.n += 1
        self.ll_model += -np.log(max(p_model[k], 1e-12))
        self.ll_market += -np.log(max(p_market[k], 1e-12))
        for wgt in (0.25, 0.5, 0.75):
            pb = wgt * p_model + (1 - wgt) * p_market
            self.ll_blend[wgt] += -np.log(max(pb[k], 1e-12))
        self.brier_model += float(np.sum((p_model - e) ** 2))
        self.brier_market += float(np.sum((p_market - e) ** 2))

    def summary(self) -> dict:
        n = max(self.n, 1)
        return {"n": self.n, "logloss_model": self.ll_model / n, "logloss_market": self.ll_market / n,
                "logloss_blend": {k: v / n for k, v in self.ll_blend.items()},
                "brier_model": self.brier_model / n, "brier_market": self.brier_market / n}


@dataclass
class Bets:
    n: int = 0
    staked: float = 0.0
    profit: float = 0.0

    def add(self, won: bool, odds: float) -> None:
        self.n += 1
        self.staked += 1
        self.profit += (odds - 1) if won else -1

    @property
    def roi(self) -> float:
        return self.profit / self.staked if self.staked else 0.0


MAX_CLOSE_1X2 = ("MaxCH", "MaxCD", "MaxCA")
MAX_CLOSE_OU = ("MaxC>2.5", "MaxC<2.5")
AVG_CLOSE_1X2 = ("AvgCH", "AvgCD", "AvgCA")
AVG_CLOSE_OU = ("AvgC>2.5", "AvgC<2.5")


def run(codes: list[str], season: str, xi: float = DEFAULT_XI, ridge: float = DEFAULT_RIDGE,
        value_threshold: float = 0.05, weight_model: float = 0.5, verbose: bool = True,
        shop_threshold: float = 0.02) -> dict:
    s1x2, sou = Score(), Score()
    sou_implied = Score()
    bets = Bets()
    shop = Bets()
    seasons = [season, _prev_season(season), _prev_season(_prev_season(season)), _prev_season(_prev_season(_prev_season(season)))]
    for code in codes:
        hist = load_history(code, seasons)
        test = [m for m in hist if _in_season(m, season)]
        if not test:
            continue
        test.sort(key=lambda m: m.date)
        start = test[0].date + timedelta(days=21)  # on laisse 3 semaines au modèle pour voir les promus
        week = start
        while week <= test[-1].date:
            batch = [m for m in test if week <= m.date < week + timedelta(days=7)]
            if batch:
                model = fit(hist, week, xi=xi, ridge=ridge)
                for m in batch:
                    if not (model.knows(m.home) and model.knows(m.away)):
                        continue
                    pr = predict(model, m.home, m.away)
                    o12 = _odds(m, CLOSE_1X2)
                    if o12:
                        pm = np.array([pr.p("1x2", s) for s in ("1", "X", "2")])
                        pk = np.array(devig(o12))
                        k = 0 if m.fthg > m.ftag else (1 if m.fthg == m.ftag else 2)
                        s1x2.add(pm, pk, k)
                        for i in range(3):
                            pb = weight_model * pm[i] + (1 - weight_model) * pk[i]
                            if pb * o12[i] - 1 >= value_threshold:
                                bets.add(i == k, o12[i])
                    # Plus/moins 2,5 déduit des seules cotes 1X2 (buts attendus implicites)
                    oou_avg = _odds(m, (AVG_CLOSE_OU,))
                    o12_avg = _odds(m, (AVG_CLOSE_1X2,))
                    if o12_avg and oou_avg:
                        lam, mu = implied_rates(devig(o12_avg), model.rho)
                        p_over = _over25(lam, mu, model.rho)
                        k = 0 if m.fthg + m.ftag > 2.5 else 1
                        sou_implied.add(np.array([p_over, 1 - p_over]), np.array(devig(oou_avg)), k)
                    # « Meilleure cote » : parier quand la cote max dépasse la cote juste du consensus
                    for avg_cols, max_cols, outcome_idx in ((AVG_CLOSE_1X2, MAX_CLOSE_1X2, None), (AVG_CLOSE_OU, MAX_CLOSE_OU, "ou")):
                        avg, mx = _odds(m, (avg_cols,)), _odds(m, (max_cols,))
                        if not (avg and mx):
                            continue
                        if outcome_idx == "ou":
                            k = 0 if m.fthg + m.ftag > 2.5 else 1
                        else:
                            k = 0 if m.fthg > m.ftag else (1 if m.fthg == m.ftag else 2)
                        for i, p in enumerate(devig(avg)):
                            if p * mx[i] - 1 >= shop_threshold:
                                shop.add(i == k, mx[i])
                    oou = _odds(m, CLOSE_OU)
                    if oou:
                        pm = np.array([pr.p("ou", "over", 2.5), pr.p("ou", "under", 2.5)])
                        pk = np.array(devig(oou))
                        k = 0 if m.fthg + m.ftag > 2.5 else 1
                        sou.add(pm, pk, k)
                        for i in range(2):
                            pb = weight_model * pm[i] + (1 - weight_model) * pk[i]
                            if pb * oou[i] - 1 >= value_threshold:
                                bets.add(i == k, oou[i])
            week += timedelta(days=7)
        if verbose:
            print(f"  {code} ({BY_CODE[code].name_fr}) : {len(test)} matchs dans la saison")
    return {"1x2": s1x2.summary(), "ou25": sou.summary(), "ou25_implied": sou_implied.summary(),
            "value_bets": {"n": bets.n, "roi": bets.roi, "profit": bets.profit},
            "best_price": {"n": shop.n, "roi": shop.roi, "profit": shop.profit}}


def _over25(lam: float, mu: float, rho: float) -> float:
    ft = score_matrix(lam, mu, rho)
    H, A = np.indices(ft.shape)
    return float(ft[(H + A) > 2.5].sum())


def _in_season(m: MatchRow, season: str) -> bool:
    y = 2000 + int(season[:2])
    return (m.date.year == y and m.date.month >= 7) or (m.date.year == y + 1 and m.date.month < 7)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", default="2526")
    ap.add_argument("--leagues", nargs="*", default=[lg.code for lg in LEAGUES if lg.category == "domestic"])
    ap.add_argument("--xi", type=float, default=DEFAULT_XI)
    ap.add_argument("--ridge", type=float, default=DEFAULT_RIDGE)
    args = ap.parse_args()
    res = run(args.leagues, args.season, args.xi, args.ridge)
    for mk in ("1x2", "ou25"):
        r = res[mk]
        print(f"[{mk}] {r['n']} matchs | log-loss modèle {r['logloss_model']:.4f} | marché {r['logloss_market']:.4f} | "
              f"mélanges {', '.join(f'{k:.2f}:{v:.4f}' for k, v in r['logloss_blend'].items())}")
    r = res["ou25_implied"]
    print(f"[ou25 déduit du 1X2] {r['n']} matchs | log-loss {r['logloss_model']:.4f} | marché {r['logloss_market']:.4f}")
    vb = res["value_bets"]
    print(f"[value bets modèle, cote de clôture] {vb['n']} paris | ROI {vb['roi'] * 100:+.1f} %")
    bp = res["best_price"]
    print(f"[meilleure cote > cote juste du consensus] {bp['n']} paris | ROI {bp['roi'] * 100:+.1f} %")


if __name__ == "__main__":
    main()
