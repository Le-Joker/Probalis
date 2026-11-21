"""Simulation des « paris du jour » sur une saison passée (affichée dans l'onglet Historique).

Mêmes règles et même moteur que le site (football/engine.py, site/picks.py) : chaque semaine, le moteur
n'apprend que sur les matchs d'avant ; il mélange son analyse aux cotes moyennes des bookmakers d'avant-match
(comme sur le site quand ces cotes existent) ; on choisit chaque jour les 5 paris de chaque niveau et les
coupons du jour, puis on les règle avec le score final. Le résultat est enregistré dans
probalis/site/simulation.json.

Usage : python -m probalis.football.simulation --season 2526
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

from ..site import picks
from .backtest import _in_season, _odds, _prev_season
from .data import load_history
from .engine import analyse, fit_league, load_params
from .leagues import BY_CODE, LEAGUES

OUT = Path(__file__).resolve().parents[1] / "site" / "simulation.json"
PRE_1X2 = (("AvgH", "AvgD", "AvgA"), ("B365H", "B365D", "B365A"))
PRE_OU = (("Avg>2.5", "Avg<2.5"), ("B365>2.5", "B365<2.5"))


def _matches(codes: list[str], season: str, calibrate: bool, verbose: bool) -> tuple[list[dict], dict]:
    """Chaque match de la saison sous la même forme que sur le site, plus son score final."""
    seasons = [season, _prev_season(season), _prev_season(_prev_season(season)),
               _prev_season(_prev_season(_prev_season(season)))]
    out, scores = [], {}
    params = load_params()
    for code in codes:
        hist = load_history(code, seasons)
        test = sorted((m for m in hist if _in_season(m, season)), key=lambda m: m.date)
        if not test:
            continue
        week = test[0].date + timedelta(days=21)  # 3 semaines pour que le modèle voie les promus
        n = 0
        while week <= test[-1].date:
            batch = [m for m in test if week <= m.date < week + timedelta(days=7)]
            if batch:
                lm = fit_league(hist, week, params, counts=False)
                model = lm.goals
                for m in batch:
                    if not (model.knows(m.home) and model.knows(m.away)) or m.fthg is None:
                        continue
                    o12 = _odds(m, PRE_1X2) if calibrate else None
                    oou = _odds(m, PRE_OU) if o12 else None
                    an = analyse(lm, m.home, m.away, o12, oou, params)
                    pred, conf = an.pred, an.confidence
                    mid = f"{code}-{m.date.isoformat()}-{m.home}-{m.away}"
                    out.append({"id": mid, "league": code, "kickoff": f"{m.date.isoformat()}T15:00:00+00:00",
                                "confidence": conf, "markets": [mk.to_dict() for mk in pred.markets]})
                    scores[mid] = (m.fthg, m.ftag)
                    n += 1
            week += timedelta(days=7)
        if verbose:
            print(f"  {code} ({BY_CODE[code].name_fr}) : {n} matchs simulés", flush=True)
    return out, scores


def _acc() -> dict:
    return {"n": 0, "won": 0, "p": 0.0, "ret": 0.0}


def _add(a: dict, res: str, p: float, book: float) -> None:
    if res == "void":
        return
    a["n"] += 1
    a["p"] += p
    if res == "won":
        a["won"] += 1
        a["ret"] += book - 1
    else:
        a["ret"] -= 1


def _num(x: float, lang: str, digits: int = 0) -> str:
    s = f"{x:,.{digits}f}"
    return s.replace(",", " ").replace(".", ",") if lang == "fr" else s


def _pct(x: float, lang: str, signed: bool = False) -> str:
    v = round(x * 100)
    s = (("+" if v > 0 else "−" if v < 0 else "") + str(abs(v))) if signed else str(v)
    return f"{s} %" if lang == "fr" else f"{s}%"  # espace insécable : « % » jamais seul en début de ligne


def _view(a: dict) -> dict:
    n = a["n"]
    rate = a["won"] / n if n else 0.0
    ann = a["p"] / n if n else 0.0
    roi = a["ret"] / n if n else 0.0
    return {"n": n, "won": a["won"], "rate": round(rate, 4), "announced": round(ann, 4), "roi": round(roi, 4),
            "n_txt": {lg: _num(n, lg) for lg in ("fr", "en")},
            "rate_txt": {lg: _pct(rate, lg) for lg in ("fr", "en")},
            "announced_txt": {lg: _pct(ann, lg) for lg in ("fr", "en")},
            "roi_txt": {lg: _pct(roi, lg, signed=True) for lg in ("fr", "en")}}


def simulate(matches: list[dict], scores: dict) -> dict:
    by_day = defaultdict(list)
    for m in matches:
        by_day[m["kickoff"][:10]].append(m)
    tiers = {t: _acc() for t in picks.TIERS}
    coupons = {t: _acc() for t in picks.COUPON_TARGETS}
    calib = defaultdict(_acc)
    for day in sorted(by_day):
        ms = by_day[day]
        for t in picks.TIERS:
            for c in picks.tier_picks(ms, t):
                res = picks.settle(c["key"], c["line"], c["sel"], *scores[c["mid"]])
                _add(tiers[t], res, c["p"], picks.book_odds(c["fair"]))
                _add(calib[min(9, int(c["p"] * 10))], res, c["p"], picks.book_odds(c["fair"]))
        for cp in picks.day_coupons(ms):
            states = [picks.settle(c["key"], c["line"], c["sel"], *scores[c["mid"]]) for c in cp["legs"]]
            res = picks.coupon_result(states)
            book = 1.0
            for c, s in zip(cp["legs"], states):
                if s != "void":
                    book *= picks.book_odds(c["fair"])
            p = 1.0
            for c, s in zip(cp["legs"], states):
                if s != "void":
                    p *= c["p"]
            _add(coupons[cp["target"]], res, p, book)
    return {"tiers": {t: _view(a) for t, a in tiers.items()},
            "coupons": [{"target": t, **_view(a)} for t, a in coupons.items()],
            "calibration": {f"{k / 10:.1f}": _view(a) for k, a in sorted(calib.items())},
            "days": len(by_day)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", default="2526")
    ap.add_argument("--leagues", nargs="*", default=[lg.code for lg in LEAGUES if lg.category == "domestic"])
    ap.add_argument("--model-only", action="store_true", help="sans calage sur les cotes (modèle seul)")
    ap.add_argument("--dry-run", action="store_true", help="affiche sans écrire simulation.json")
    args = ap.parse_args()
    print(f"Simulation {args.season} ({'modèle seul' if args.model_only else 'calée sur les cotes'})…", flush=True)
    matches, scores = _matches(args.leagues, args.season, not args.model_only, True)
    res = simulate(matches, scores)
    s = args.season
    res.update(season=f"20{s[:2]}/{s[2:]}", matches=len(matches), engine=load_params().version,
               matches_txt={lg: _num(len(matches), lg) for lg in ("fr", "en")},
               calibrated=not args.model_only, leagues=args.leagues)
    for t, v in res["tiers"].items():
        print(f"  {t:<9} {v['n']:>4} paris | réussite {v['rate']:.1%} | annoncé {v['announced']:.1%} | rendement {v['roi']:+.1%}")
    for v in res["coupons"]:
        print(f"  coupon {v['target']:<3} {v['n']:>4} | réussite {v['rate']:.1%} | annoncé {v['announced']:.1%} | rendement {v['roi']:+.1%}")
    for k, v in res["calibration"].items():
        print(f"  tranche {k}: {v['n']:>4} paris | annoncé {v['announced']:.1%} | réel {v['rate']:.1%}")
    if not args.dry_run:
        OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Enregistré dans {OUT}")


if __name__ == "__main__":
    main()
