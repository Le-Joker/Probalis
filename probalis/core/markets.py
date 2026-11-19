"""Calcul de tous les marchés football à partir des matrices de score.

Moteur A du catalogue (docs/01-catalogue-marches.md) : tout se lit dans la matrice
du match entier (Dixon-Coles) et dans les matrices des deux mi-temps.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .value import Outcome

S = Outcome.simple

OU_LINES = (0.5, 1.5, 2.5, 3.5, 4.5, 5.5)
ASIAN_TOTAL_LINES = (1.75, 2.0, 2.25, 2.75, 3.0, 3.25)
TEAM_TOTAL_LINES = (0.5, 1.5, 2.5, 3.5)
AH_LINES = tuple(x / 4 for x in range(-10, 11))  # -2.5 .. +2.5 par quart
EH_LINES = (-2.0, -1.0, 1.0, 2.0)
MULTIGOALS = ((1, 2), (1, 3), (2, 3), (2, 4), (3, 4), (3, 5), (4, 6), (1, 5), (2, 5))
COMBO_OU_LINES = (1.5, 2.5, 3.5)
HALF_OU_LINES = (0.5, 1.5, 2.5)


@dataclass
class Market:
    key: str
    group: str
    selections: dict[str, Outcome]
    line: float | None = None
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        sel = {}
        for k, o in self.selections.items():
            d = {"p": round(o.prob, 5)}
            fo = o.fair_odds
            d["fair"] = round(fo, 3) if fo else None
            if o.push or o.half_win or o.half_loss:
                d.update(w=round(o.win, 5), hw=round(o.half_win, 5), pu=round(o.push, 5),
                         hl=round(o.half_loss, 5), l=round(o.loss, 5))
            sel[k] = d
        out = {"key": self.key, "group": self.group, "sel": sel}
        if self.line is not None:
            out["line"] = self.line
        return out


def _p(m: np.ndarray, mask: np.ndarray) -> float:
    return float(m[mask].sum())


def _line_outcome(m: np.ndarray, margin_fn, line: float) -> Outcome:
    """Règlement d'une ligne (entière, demi ou quart) ; margin_fn(l) > 0 signifie gagné."""
    q = line * 4
    if abs(q - round(q)) < 1e-9 and int(round(q)) % 2 != 0:
        r = np.sign(margin_fn(line - 0.25)) + np.sign(margin_fn(line + 0.25))
        return Outcome(win=_p(m, r == 2), half_win=_p(m, r == 1), push=_p(m, r == 0),
                       half_loss=_p(m, r == -1), loss=_p(m, r == -2))
    s = np.sign(margin_fn(line))
    return Outcome(win=_p(m, s > 0), push=_p(m, s == 0), loss=_p(m, s < 0))


def _result_masks(D: np.ndarray) -> dict[str, np.ndarray]:
    return {"1": D > 0, "X": D == 0, "2": D < 0}


def full_time_markets(ft: np.ndarray) -> list[Market]:
    H, A = np.indices(ft.shape)
    T, D = H + A, H - A
    P = lambda mask: _p(ft, mask)  # noqa: E731
    res = _result_masks(D)
    dc = {"1X": D >= 0, "12": D != 0, "X2": D <= 0}
    btts = {"yes": (H > 0) & (A > 0), "no": (H == 0) | (A == 0)}
    out: list[Market] = []
    add = lambda key, group, sel, line=None: out.append(Market(key, group, sel, line))  # noqa: E731

    # Principaux
    add("1x2", "main", {k: S(P(v)) for k, v in res.items()})
    add("dc", "main", {k: S(P(v)) for k, v in dc.items()})
    add("dnb", "main", {"1": _line_outcome(ft, lambda l: D + l, 0.0),
                        "2": _line_outcome(ft, lambda l: -D + l, 0.0)})
    add("btts", "main", {k: S(P(v)) for k, v in btts.items()})

    # Buts
    for line in OU_LINES:
        add("ou", "goals", {"over": S(P(T > line)), "under": S(P(T < line))}, line)
    for line in ASIAN_TOTAL_LINES:
        add("aou", "goals", {"over": _line_outcome(ft, lambda l: T - l, line),
                             "under": _line_outcome(ft, lambda l: l - T, line)}, line)
    exact = {str(k): S(P(T == k)) for k in range(6)}
    exact["6+"] = S(P(T >= 6))
    add("exact", "goals", exact)
    add("multigoals", "goals", {f"{a}-{b}": S(P((T >= a) & (T <= b))) for a, b in MULTIGOALS})
    add("oe", "goals", {"odd": S(P(T % 2 == 1)), "even": S(P(T % 2 == 0))})

    # Équipes
    for side, G in (("1", H), ("2", A)):
        for line in TEAM_TOTAL_LINES:
            add(f"tt{side}", "teams", {"over": S(P(G > line)), "under": S(P(G < line))}, line)
        add(f"oe{side}", "teams", {"odd": S(P(G % 2 == 1)), "even": S(P(G % 2 == 0))})
    add("clean1", "teams", {"yes": S(P(A == 0)), "no": S(P(A > 0))})
    add("clean2", "teams", {"yes": S(P(H == 0)), "no": S(P(H > 0))})
    add("wtn", "teams", {"1": S(P((A == 0) & (H > 0))), "2": S(P((H == 0) & (A > 0)))})
    add("score4", "teams", {"none": S(P(T == 0)), "1": S(P((H > 0) & (A == 0))),
                            "2": S(P((H == 0) & (A > 0))), "both": S(P((H > 0) & (A > 0)))})
    add("margin", "teams", {"1+1": S(P(D == 1)), "1+2": S(P(D == 2)), "1+3": S(P(D >= 3)),
                            "X": S(P(D == 0)),
                            "2+1": S(P(D == -1)), "2+2": S(P(D == -2)), "2+3": S(P(D <= -3))})

    # Handicaps
    for h in AH_LINES:
        add("ah", "handicaps", {"1": _line_outcome(ft, lambda l: D + l, h),
                                "2": _line_outcome(ft, lambda l: -D + l, -h)}, h)
    for h in EH_LINES:
        add("eh", "handicaps", {k: S(P(v)) for k, v in _result_masks(D + h).items()}, h)

    # Score exact
    scores = {f"{h}-{a}": S(float(ft[h, a])) for h in range(6) for a in range(6)}
    scores["other"] = S(P((H > 5) | (A > 5)))
    add("score", "scores", scores)

    # Combinés du même match
    for line in COMBO_OU_LINES:
        ou = {"over": T > line, "under": T < line}
        add("1x2_ou", "combos", {f"{r}&{o}": S(P(rm & om)) for r, rm in res.items() for o, om in ou.items()}, line)
    add("1x2_btts", "combos", {f"{r}&{b}": S(P(rm & bm)) for r, rm in res.items() for b, bm in btts.items()})
    add("dc_btts", "combos", {f"{r}&{b}": S(P(rm & bm)) for r, rm in dc.items() for b, bm in btts.items()})
    ou25 = {"over": T > 2.5, "under": T < 2.5}
    add("dc_ou", "combos", {f"{r}&{o}": S(P(rm & om)) for r, rm in dc.items() for o, om in ou25.items()}, 2.5)
    add("ou_btts", "combos", {f"{o}&{b}": S(P(om & bm)) for o, om in ou25.items() for b, bm in btts.items()}, 2.5)
    add("res_or_ou", "combos", {f"{r}|{o}": S(P(rm | om)) for r, rm in res.items() for o, om in ou25.items()}, 2.5)
    return out


def _single_half_markets(m: np.ndarray, suffix: str) -> list[Market]:
    H, A = np.indices(m.shape)
    T, D = H + A, H - A
    P = lambda mask: _p(m, mask)  # noqa: E731
    out = [
        Market(f"1x2_{suffix}", "halves", {k: S(P(v)) for k, v in _result_masks(D).items()}),
        Market(f"dc_{suffix}", "halves", {"1X": S(P(D >= 0)), "12": S(P(D != 0)), "X2": S(P(D <= 0))}),
        Market(f"btts_{suffix}", "halves", {"yes": S(P((H > 0) & (A > 0))), "no": S(P((H == 0) | (A == 0)))}),
    ]
    for line in HALF_OU_LINES:
        out.append(Market(f"ou_{suffix}", "halves", {"over": S(P(T > line)), "under": S(P(T < line))}, line))
    scores = {f"{h}-{a}": S(float(m[h, a])) for h in range(4) for a in range(4)}
    scores["other"] = S(P((H > 3) | (A > 3)))
    out.append(Market(f"score_{suffix}", "halves", scores))
    return out


def half_markets(h1: np.ndarray, h2: np.ndarray, ft_1x2: dict[str, float]) -> list[Market]:
    out = _single_half_markets(h1, "1h") + _single_half_markets(h2, "2h")

    J = h1[:, :, None, None] * h2[None, None, :, :]
    a1h, a1a, a2h, a2a = np.indices(J.shape)
    t1, t2 = a1h + a1a, a2h + a2a
    P = lambda mask: _p(J, mask)  # noqa: E731

    ht = _result_masks(a1h - a1a)
    ft = _result_masks((a1h + a2h) - (a1a + a2a))
    # Mi-temps / fin de match, recalé sur le 1X2 du modèle Dixon-Coles pour rester cohérent.
    raw = {(h, f): P(ht[h] & ft[f]) for h in ht for f in ft}
    scale = {f: ft_1x2[f] / max(sum(raw[(h, f)] for h in ht), 1e-12) for f in ft}
    out.append(Market("htft", "halves", {f"{h}/{f}": S(raw[(h, f)] * scale[f]) for h in ht for f in ft}))

    out.append(Market("most_goals_half", "halves", {"1h": S(P(t1 > t2)), "2h": S(P(t2 > t1)), "equal": S(P(t1 == t2))}))
    for side, (g1, c1, g2, c2) in (("1", (a1h, a1a, a2h, a2a)), ("2", (a1a, a1h, a2a, a2h))):
        both = (g1 > c1) & (g2 > c2)
        either = (g1 > c1) | (g2 > c2)
        scores_both = (g1 > 0) & (g2 > 0)
        out.append(Market(f"win_both{side}", "halves", {"yes": S(P(both)), "no": S(P(~both))}))
        out.append(Market(f"win_either{side}", "halves", {"yes": S(P(either)), "no": S(P(~either))}))
        out.append(Market(f"score_both_halves{side}", "halves", {"yes": S(P(scores_both)), "no": S(P(~scores_both))}))
    for line in (0.5, 1.5):
        both_over = (t1 > line) & (t2 > line)
        out.append(Market("both_halves_over", "halves", {"yes": S(P(both_over)), "no": S(P(~both_over))}, line))
    both_under = (t1 < 1.5) & (t2 < 1.5)
    out.append(Market("both_halves_under", "halves", {"yes": S(P(both_under)), "no": S(P(~both_under))}, 1.5))
    return out


def football_markets(ft: np.ndarray, h1: np.ndarray, h2: np.ndarray) -> list[Market]:
    markets = full_time_markets(ft)
    ft_1x2 = {k: o.prob for k, o in markets[0].selections.items()}
    return markets + half_markets(h1, h2, ft_1x2)
