"""Modèle relié (coupes d'Europe, féminin) : il doit retrouver l'écart de niveau entre deux pays."""
from datetime import date, timedelta

import numpy as np

from probalis.football.linked import country_key
from probalis.football.model import Game, fit_linked


def _simulate(seed=1):
    rng = np.random.default_rng(seed)
    # Pays A nettement plus fort que le pays B ; 8 équipes chacun, écarts propres modestes
    teams = {f"A{i}": ("A", 0.35 + rng.normal(0, 0.15), -0.25 + rng.normal(0, 0.1)) for i in range(8)}
    teams |= {f"B{i}": ("B", -0.35 + rng.normal(0, 0.15), 0.25 + rng.normal(0, 0.1)) for i in range(8)}
    c, home = 0.2, 0.25
    ref = date(2026, 6, 1)
    games = []

    def play(h, a, kind, d):
        lam = np.exp(c + home + teams[h][1] + teams[a][2])
        mu = np.exp(c + teams[a][1] + teams[h][2])
        games.append(Game(d, h, a, int(rng.poisson(lam)), int(rng.poisson(mu)), kind))

    for k in range(4):  # championnats : chacun joue contre chacun, 4 fois
        for country in "AB":
            names = [t for t in teams if t.startswith(country)]
            for h in names:
                for a in names:
                    if h != a:
                        play(h, a, "dom", ref - timedelta(days=30 + 90 * k + int(rng.integers(0, 80))))
    for _ in range(120):  # matchs européens entre les deux pays
        h, a = rng.choice([f"A{i}" for i in range(8)]), rng.choice([f"B{i}" for i in range(8)])
        if rng.random() < 0.5:
            h, a = a, h
        play(str(h), str(a), "cup", ref - timedelta(days=int(rng.integers(10, 400))))
    return teams, games, ref


def test_linked_model_recovers_country_gap():
    teams, games, ref = _simulate()
    model = fit_linked(games, {t: g for t, (g, _, _) in teams.items()}, ref)
    gap_true = np.mean([t[1] - t[2] for t in teams.values() if t[0] == "A"]) - \
        np.mean([t[1] - t[2] for t in teams.values() if t[0] == "B"])
    q = {t: model.attack[i] - model.defence[i] for i, t in enumerate(model.teams)}
    gap_fit = np.mean([q[t] for t in q if t.startswith("A")]) - np.mean([q[t] for t in q if t.startswith("B")])
    assert abs(gap_fit - gap_true) < 0.35
    assert gap_fit > 0.8  # le pays A est bien vu comme plus fort


def test_linked_view_predicts_cup_match():
    from probalis.football.predict import predict
    teams, games, ref = _simulate(2)
    model = fit_linked(games, {t: g for t, (g, _, _) in teams.items()}, ref)
    pred = predict(model.view("cup"), "A0", "B0")
    p1, px, p2 = (pred.p("1x2", s) for s in ("1", "X", "2"))
    assert abs(p1 + px + p2 - 1) < 1e-6 and p1 > p2
    neutral = predict(model.view("cup", neutral=True), "A0", "B0")
    assert neutral.p("1x2", "1") < p1  # sans avantage du terrain, le favori a moins de chances


def test_country_names_are_normalised():
    assert country_key("The Netherlands") == "netherlands"
    assert country_key("Türkiye") == "turkey"
    assert country_key("Monaco") == "france"
