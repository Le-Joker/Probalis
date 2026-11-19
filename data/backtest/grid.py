"""Réglage rapide du modèle : quelques combinaisons de paramètres sur la saison 2025/26."""
import json, sys, time
from probalis.football.backtest import run
from probalis.football.leagues import LEAGUES
codes = [lg.code for lg in LEAGUES]
results = []
for ridge, xi in ((2.0, 0.0019), (5.0, 0.0019), (2.0, 0.003), (0.5, 0.0019)):
    t = time.time()
    r = run(codes, "2526", xi=xi, ridge=ridge, verbose=False)
    r["params"] = {"ridge": ridge, "xi": xi}
    results.append(r)
    a, b = r["1x2"], r["ou25"]
    print(f"ridge={ridge} xi={xi} | 1X2 n={a['n']} modele={a['logloss_model']:.4f} marche={a['logloss_market']:.4f} "
          f"melange25={a['logloss_blend'][0.25]:.4f} melange50={a['logloss_blend'][0.5]:.4f} | O/U modele={b['logloss_model']:.4f} "
          f"marche={b['logloss_market']:.4f} melange25={b['logloss_blend'][0.25]:.4f} | value n={r['value_bets']['n']} "
          f"roi={r['value_bets']['roi']*100:+.1f}% | {time.time()-t:.0f}s", flush=True)
json.dump(results, open("data/backtest/resultats-2526.json", "w"), indent=1, default=str)
