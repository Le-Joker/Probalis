"""Règles des paris du jour et des coupons (probalis/site/picks.py)."""
from probalis.football.leagues import LEAGUES
from probalis.site import picks


def _match(mid, p_home, p_over15=0.75, p_btts=0.5, league="E0", conf="high"):
    def sel(**ps):
        return {k: {"p": v, "fair": round(1 / v, 3)} for k, v in ps.items()}
    p_away = round((1 - p_home) * 0.55, 4)
    p_draw = round(1 - p_home - p_away, 4)
    return {"id": mid, "league": league, "kickoff": "2026-11-21T15:00:00+00:00", "confidence": conf,
            "markets": [
                {"key": "1x2", "sel": sel(**{"1": p_home, "X": p_draw, "2": p_away})},
                {"key": "dc", "sel": sel(**{"1X": p_home + p_draw, "X2": p_draw + p_away, "12": p_home + p_away})},
                {"key": "ou", "line": 1.5, "sel": sel(over=p_over15, under=1 - p_over15)},
                {"key": "btts", "sel": sel(yes=p_btts, no=1 - p_btts)},
            ]}


def test_settle_classic_markets():
    assert picks.settle("1x2", None, "1", 2, 1) == "won"
    assert picks.settle("1x2", None, "2", 2, 1) == "lost"
    assert picks.settle("dc", None, "1X", 1, 1) == "won"
    assert picks.settle("dc", None, "12", 0, 0) == "lost"
    assert picks.settle("ou", 2.5, "over", 2, 1) == "won"
    assert picks.settle("ou", 1.5, "under", 1, 1) == "lost"
    assert picks.settle("btts", None, "yes", 1, 0) == "lost"
    assert picks.settle("btts", None, "no", 3, 0) == "won"
    assert picks.settle("tt2", 0.5, "over", 0, 1) == "won"
    assert picks.settle("tt1", 1.5, "over", 1, 3) == "lost"


def test_coupon_result():
    assert picks.coupon_result(["won", "won"]) == "won"
    assert picks.coupon_result(["won", "lost", None]) == "lost"
    assert picks.coupon_result(["won", None]) is None
    assert picks.coupon_result(["won", "void"]) == "won"
    assert picks.coupon_result(["void", "void"]) == "void"


def test_tier_picks_rules():
    ms = [_match(f"m{i}", 0.30 + 0.04 * i) for i in range(8)]
    for tier, (lo, hi) in picks.TIERS.items():
        out = picks.tier_picks(ms, tier)
        assert len(out) <= picks.N_PICKS
        assert len({c["mid"] for c in out}) == len(out), "un seul pari par match"
        fams = [picks.FAMILY[c["key"]] for c in out]
        assert all(fams.count(f) <= 2 for f in fams), "pas plus de deux paris du même type"
        assert all(lo <= c["p"] <= hi for c in out)


def test_excluded_matches():
    women = next(lg.code for lg in LEAGUES if lg.category == "women")
    ms = [_match("w", 0.6, league=women), _match("low", 0.6, conf="low"), _match("ok", 0.6)]
    mids = {c["mid"] for t in picks.TIERS for c in picks.tier_picks(ms, t)}
    assert mids == {"ok"}


def test_book_odds_margin():
    assert abs(picks.book_odds(2.1) - 2.0) < 1e-9
    legs = [{"p": 0.5, "fair": 2.0}, {"p": 0.5, "fair": 2.0}]
    st = picks.coupon_stats(legs)
    assert st["p"] == 0.25 and st["fair"] == 4.0
    assert st["book"] < st["fair"]


def test_day_coupons_hit_targets():
    ms = [_match(f"m{i}", 0.35 + 0.05 * i, p_over15=0.70 + 0.02 * i) for i in range(10)]
    cps = picks.day_coupons(ms)
    assert cps, "au moins un coupon avec 10 matchs"
    for cp in cps:
        t = cp["target"]
        assert 0.9 * t <= cp["book"] <= 1.35 * t
        assert len({c["mid"] for c in cp["legs"]}) == len(cp["legs"])
