"""Test de fiabilité des coupes d'Europe et du football féminin.

Pas de cotes gratuites pour ces compétitions : on compare le modèle à un repère simple, les fréquences
moyennes de victoire à domicile, de nul et de victoire à l'extérieur. On rejoue la période deux semaines
par deux semaines : le modèle n'apprend que sur les matchs d'avant.

Usage : python -m probalis.football.backtest_linked            (coupes d'Europe, saison 2025/26)
        python -m probalis.football.backtest_linked --women    (football féminin, saison en cours)
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta

import numpy as np

from ..core.scores import score_matrix
from .leagues import LEAGUES
from .linked import WOMEN_MAX_DAYS, LinkedData, men_cups_data, women_data
from .model import DEFAULT_MAX_DAYS, fit_linked


def _outcome(hg: int, ag: int) -> int:
    return 0 if hg > ag else (1 if hg == ag else 2)


def evaluate(data: LinkedData, kinds: tuple[str, ...], start: date, end: date, step_days: int = 14,
             max_days: int = DEFAULT_MAX_DAYS) -> dict:
    tests = sorted((g for g in data.games if g.kind in kinds and start <= g.date < end), key=lambda g: g.date)
    ll_m, ll_b, hit_m, hit_b, fav = [], [], [], [], []
    t = start
    while t < end:
        window = [g for g in tests if t <= g.date < t + timedelta(days=step_days)]
        if window:
            model = fit_linked(data.games, data.group_of, t, max_days=max_days,
                               first_half_share=data.first_half_share)
            past = [_outcome(g.hg, g.ag) for g in data.games if g.kind in kinds and g.date < t
                    and (t - g.date).days <= 365]
            base = np.bincount(past, minlength=3) / max(len(past), 1) if past else np.ones(3) / 3
            views = {}
            for g in window:
                if model.weight_by_team.get(g.home, 0) <= 0 or model.weight_by_team.get(g.away, 0) <= 0:
                    continue
                key = (g.kind, g.neutral)
                views.setdefault(key, model.view(*key))
                lam, mu = views[key].rates(g.home, g.away)
                m = score_matrix(lam, mu, model.rho)
                p = np.array([np.tril(m, -1).sum(), np.trace(m), np.triu(m, 1).sum()])
                p = p / p.sum()
                k = _outcome(g.hg, g.ag)
                ll_m.append(-np.log(max(p[k], 1e-12)))
                ll_b.append(-np.log(max(base[k], 1e-12)))
                hit_m.append(int(np.argmax(p) == k))
                hit_b.append(int(np.argmax(base) == k))
                if p.max() >= 0.6:
                    fav.append((p.max(), int(np.argmax(p) == k)))
        t += timedelta(days=step_days)
    n = len(ll_m)
    return {
        "n": n,
        "logloss_model": float(np.mean(ll_m)) if n else None,
        "logloss_base": float(np.mean(ll_b)) if n else None,
        "hit_model": float(np.mean(hit_m)) if n else None,
        "hit_base": float(np.mean(hit_b)) if n else None,
        "strong_favourites": len(fav),
        "strong_fav_expected": float(np.mean([p for p, _ in fav])) if fav else None,
        "strong_fav_won": float(np.mean([w for _, w in fav])) if fav else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--women", action="store_true")
    args = ap.parse_args()
    today = date.today()
    if args.women:
        lgs = [lg for lg in LEAGUES if lg.category == "women"]
        data = women_data(lgs, today)
        start = date(today.year if today.month >= 8 else today.year - 1, 8, 1)
        parts = {"championnats": ("dom",), "Ligue des champions": ("cup",)}
        res = {k: evaluate(data, v, start, today, max_days=WOMEN_MAX_DAYS) for k, v in parts.items()}
    else:
        lgs = [lg for lg in LEAGUES if lg.category == "europe"]
        data = men_cups_data(lgs, today)
        res = {"coupes d'Europe 2025/26": evaluate(data, ("cup",), date(2025, 7, 1), date(2026, 6, 1)),
               "coupes d'Europe 2026/27": evaluate(data, ("cup",), date(2026, 7, 1), today)}
    for name, r in res.items():
        if not r["n"]:
            print(f"[{name}] aucun match à tester")
            continue
        print(f"[{name}] {r['n']} matchs | log-loss modèle {r['logloss_model']:.4f} | repère {r['logloss_base']:.4f}"
              f" | bon pronostic {r['hit_model'] * 100:.1f} % (repère {r['hit_base'] * 100:.1f} %)")
        if r["strong_favourites"]:
            print(f"   favoris à 60 % ou plus : {r['strong_favourites']} matchs, chances annoncées "
                  f"{r['strong_fav_expected'] * 100:.1f} %, gagnés {r['strong_fav_won'] * 100:.1f} %")


if __name__ == "__main__":
    main()
