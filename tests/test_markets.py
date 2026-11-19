import numpy as np
import pytest

from probalis.core.markets import football_markets
from probalis.core.scores import half_matrices, score_matrix
from probalis.core.value import Outcome, accumulator, devig, margin


def _markets(lam=1.6, mu=1.1, rho=-0.08, share=0.45):
    ft = score_matrix(lam, mu, rho)
    h1, h2 = half_matrices(lam, mu, share)
    return ft, {(m.key, m.line): m for m in football_markets(ft, h1, h2)}


def test_score_matrix_sums_to_one():
    assert score_matrix(1.4, 1.2, -0.1).sum() == pytest.approx(1.0)


def test_mutually_exclusive_markets_sum_to_one():
    _, mk = _markets()
    for key in ("1x2", "dc_btts", "1x2_btts", "exact", "score", "margin", "score4", "htft", "most_goals_half",
                "score_1h", "1x2_2h"):
        m = mk[(key, None)]
        total = sum(o.prob for o in m.selections.values())
        expected = 2.0 if key == "dc_btts" else 1.0  # double chance : chaque issue est comptée deux fois
        assert total == pytest.approx(expected, abs=1e-6), key
    for line in (0.5, 2.5, 5.5):
        ou = mk[("ou", line)].selections
        assert ou["over"].prob + ou["under"].prob == pytest.approx(1.0)


def test_symmetric_match_is_symmetric():
    _, mk = _markets(lam=1.3, mu=1.3)
    s = mk[("1x2", None)].selections
    assert s["1"].prob == pytest.approx(s["2"].prob)
    ah = mk[("ah", 0.0)].selections
    assert ah["1"].fair_odds == pytest.approx(ah["2"].fair_odds)


def test_asian_quarter_line_is_average_of_neighbours():
    _, mk = _markets()
    q = mk[("ah", -0.75)].selections["1"]
    a = mk[("ah", -0.5)].selections["1"]
    b = mk[("ah", -1.0)].selections["1"]
    for odds in (1.7, 2.0, 2.4):
        assert q.ev(odds) == pytest.approx((a.ev(odds) + b.ev(odds)) / 2)


def test_dnb_equals_ah_zero():
    _, mk = _markets()
    assert mk[("dnb", None)].selections["1"].fair_odds == pytest.approx(mk[("ah", 0.0)].selections["1"].fair_odds)


def test_htft_is_consistent_with_full_time_1x2():
    _, mk = _markets()
    x12 = mk[("1x2", None)].selections
    htft = mk[("htft", None)].selections
    for f in ("1", "X", "2"):
        assert sum(htft[f"{h}/{f}"].prob for h in ("1", "X", "2")) == pytest.approx(x12[f].prob)


def test_combo_consistency():
    _, mk = _markets()
    combo = mk[("1x2_ou", 2.5)].selections
    over = mk[("ou", 2.5)].selections["over"].prob
    assert sum(combo[f"{r}&over"].prob for r in ("1", "X", "2")) == pytest.approx(over)


def test_outcome_fair_odds_gives_zero_ev():
    o = Outcome(win=0.4, half_win=0.1, push=0.2, half_loss=0.1, loss=0.2)
    assert o.ev(o.fair_odds) == pytest.approx(0.0)
    assert Outcome.simple(0.5).fair_odds == pytest.approx(2.0)


def test_margin_and_devig():
    odds = [2.0, 3.4, 3.8]
    assert margin(odds) == pytest.approx(1 / 2 + 1 / 3.4 + 1 / 3.8 - 1)
    assert sum(devig(odds)) == pytest.approx(1.0)


def test_accumulator_margin_compounds():
    # 5 sélections justes à 50 % avec 5 % de marge chacune : le bookmaker garde ~22 %
    acc = accumulator([0.5] * 5, [2.0 / 1.05] * 5)
    assert acc.ev == pytest.approx(1 / 1.05 ** 5 - 1)
    assert acc.ev == pytest.approx(-0.2165, abs=1e-3)


def test_implied_rates_recover_true_rates():
    from probalis.core.implied import _probs, implied_rates
    p, over = _probs(1.7, 1.0, -0.05)
    lam, mu = implied_rates(list(p), -0.05)
    assert lam == pytest.approx(1.7, abs=1e-3) and mu == pytest.approx(1.0, abs=1e-3)
    lam2, mu2 = implied_rates(list(p), -0.05, p_over25=over)
    assert lam2 == pytest.approx(1.7, abs=1e-3) and mu2 == pytest.approx(1.0, abs=1e-3)


def test_matrix_against_independent_poisson_totals():
    ft, mk = _markets(rho=0.0)
    # sans correction, total = Poisson(lam + mu)
    from scipy.stats import poisson
    assert mk[("ou", 2.5)].selections["under"].prob == pytest.approx(poisson.cdf(2, 2.7), abs=1e-6)
    assert np.isclose(ft.sum(), 1.0)


def test_market_anchored_prediction_reproduces_odds():
    from probalis.core.implied import implied_rates
    from probalis.core.markets import football_markets
    p1x2 = devig([1.95, 3.6, 4.1])
    p_over = devig([1.9, 1.95])[0]
    lam, mu = implied_rates(p1x2, -0.05, p_over)
    ft = score_matrix(lam, mu, -0.05)
    h1, h2 = half_matrices(lam, mu, 0.45)
    mk = {(m.key, m.line): m for m in football_markets(ft, h1, h2)}
    x = mk[("1x2", None)].selections
    # 3 cibles (1, 2, plus 2,5) pour 2 paramètres : proche mais pas forcément exact
    assert x["1"].prob == pytest.approx(p1x2[0], abs=0.02)
    assert x["2"].prob == pytest.approx(p1x2[2], abs=0.02)
    assert mk[("ou", 2.5)].selections["over"].prob == pytest.approx(p_over, abs=0.02)
