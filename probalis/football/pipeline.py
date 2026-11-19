"""Chaîne complète : données -> modèles -> prédictions des prochains matchs (avec cotes si disponibles)."""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta, timezone

from ..core.implied import implied_rates
from ..core.value import Outcome, devig
from .data import load_history, load_upcoming_odds, MatchRow
from .fixtures import Fixture, finished, league_badge, league_rounds, match_names, upcoming_fixtures
from .leagues import LEAGUES, League, current_season_start, season_codes
from .linked import FINAL_ROUND, Linked, men_cups, women
from .model import fit
from .predict import Prediction, confidence, predict, predict_from_rates

# Fenêtre glissante : chaque lancement analyse les matchs d'aujourd'hui jusqu'à J+8
# (le 19, du 19 au 27 ; le 20, du 20 au 28, etc.).
HORIZON_DAYS = 8


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _odds_markets(row: MatchRow) -> dict:
    """Cotes du fichier football-data.co.uk, rangées par marché : {(clé, ligne): {sélection: {best, avg}}}."""
    o = row.odds
    out: dict = {}

    def pack(key, line, cols):
        sel = {}
        for s, (best, avg) in cols.items():
            if o.get(best) and o.get(avg):
                sel[s] = {"best": o[best], "avg": o[avg]}
        if len(sel) == len(cols):
            out[(key, line)] = sel

    pack("1x2", None, {"1": ("MaxH", "AvgH"), "X": ("MaxD", "AvgD"), "2": ("MaxA", "AvgA")})
    pack("ou", 2.5, {"over": ("Max>2.5", "Avg>2.5"), "under": ("Max<2.5", "Avg<2.5")})
    if row.ah_line is not None:
        pack("ah", row.ah_line, {"1": ("MaxAHH", "AvgAHH"), "2": ("MaxAHA", "AvgAHA")})
    return out


def _priced(pred: Prediction, odds: dict) -> dict:
    """Pour chaque sélection cotée : notre probabilité, la cote juste, la meilleure et la moyenne du marché.

    Pas d'étiquette « valeur » : le test sur la saison 2025/26 montre qu'aucune règle simple ne bat
    les cotes de clôture (voir docs/05-fiabilite.md).
    """
    priced: dict = {}
    for (key, line), sels in odds.items():
        try:
            market = pred.market(key, line)
        except KeyError:
            continue
        keys = list(sels)
        bk_margin = sum(1 / sels[k]["avg"] for k in keys) - 1
        for k in keys:
            outcome: Outcome = market.selections[k]
            priced[f"{key}|{line}|{k}"] = {"key": key, "line": line, "sel": k, "p": outcome.prob,
                                            "fair": outcome.fair_odds, "best": sels[k]["best"],
                                            "avg": sels[k]["avg"], "margin": bk_margin}
    return priced


def _season_teams(hist: list[MatchRow], season_start: int) -> list[str]:
    start = date(season_start, 7, 1)
    return sorted({m.home for m in hist if m.date >= start} | {m.away for m in hist if m.date >= start})


def _upcoming(lg: League, today: date, events: list[dict] | None = None) -> list[Fixture]:
    return upcoming_fixtures(lg, today, today + timedelta(days=HORIZON_DAYS), events)


def _fresh_results(lg: League, events: list[dict], hist: list[MatchRow], names: dict[str, str]) -> list[MatchRow]:
    """Résultats que TheSportsDB connaît déjà mais pas encore le fichier football-data.co.uk (mis à jour
    environ deux fois par semaine). Ainsi, un match joué à 13 h compte dès la relance suivante pour les
    prochains matchs des deux équipes."""
    seen = {(m.home, m.away): m.date for m in hist[-600:]}
    out = []
    for e, ko, (hg, ag) in finished(events):
        h, a = names.get(e.get("strHomeTeam") or ""), names.get(e.get("strAwayTeam") or "")
        d = ko.date()
        if not (h and a) or (h, a) in seen and abs((seen[(h, a)] - d).days) <= 3:
            continue
        out.append(MatchRow(league=lg.code, date=d, home=h, away=a, fthg=hg, ftag=ag))
    return out


def _badge(lg: League, fixtures: list[Fixture]) -> dict:
    return {"badge": next((f.league_badge for f in fixtures if f.league_badge), None) or league_badge(lg.tsdb_id),
            "badge_on_dark": lg.logo_on_dark}


def _match_dict(lg: League, f: Fixture, h: str, a: str, pred: Prediction, model_pred: Prediction, source: str,
                stature: float, conf: str, priced: dict) -> dict:
    return {
        "id": f.event_id,
        "slug": f"{f.kickoff_utc.date().isoformat()}-{slugify(f.home_tsdb)}-{slugify(f.away_tsdb)}",
        "league": lg.code, "kickoff": f.kickoff_utc.isoformat(), "round": f.round, "venue": f.venue,
        "home": {"name": f.home_tsdb, "fd": h, "badge": f.home_badge},
        "away": {"name": f.away_tsdb, "fd": a, "badge": f.away_badge},
        "xg": [round(pred.lam, 3), round(pred.mu, 3)],
        "source": source,
        "stature": round(stature, 3),
        "model_1x2": [round(model_pred.p("1x2", s), 4) for s in ("1", "X", "2")],
        "confidence": conf,
        "top_score": _top_scores(pred, 3),
        "markets": [m.to_dict() for m in pred.markets],
        "priced": priced,
    }


def _linked_matches(lg: League, linked: Linked, today: date, report: dict) -> tuple[list[dict], dict]:
    """Matchs d'une coupe d'Europe ou d'un championnat féminin, analysés par le modèle relié.

    Pas de cotes gratuites pour ces compétitions : l'analyse vient du modèle seul, la confiance est donc
    plafonnée à « moyenne ».
    """
    fixtures = _upcoming(lg, today)
    kind = "cup" if lg.cup else "dom"
    m = linked.model
    quality = {t: float(m.attack[i] - m.defence[i]) for i, t in enumerate(m.teams)}
    out = []
    for f in fixtures:
        h, a = linked.node(f.home_id), linked.node(f.away_id)
        if not (h and a):
            report["unmatched"].append(f"{lg.code}: {f.home_tsdb} - {f.away_tsdb}")
            continue
        view = m.view(kind, neutral=str(f.round) == FINAL_ROUND)
        pred = predict(view, h, a)
        conf = confidence(view, h, a)
        out.append(_match_dict(lg, f, h, a, pred, pred, "model", quality[h] + quality[a],
                               "medium" if conf == "high" else conf, {}))
    report["leagues"][lg.code] = {"fixtures": len(fixtures), "predicted": len(out), "train_matches": m.n_matches,
                                  "rho": round(m.rho, 3),
                                  "home_adv": round(m.home_cup if lg.cup else m.home_dom, 3)}
    return out, _badge(lg, fixtures)


def _run_linked(name: str, builder, lgs: list[League], today: date, matches: list, report: dict,
                league_info: dict, verbose: bool) -> None:
    if not lgs:
        return
    try:
        linked = builder(lgs, today, verbose)
    except Exception as e:  # une source en panne ne doit pas bloquer le reste du site
        for lg in lgs:
            report["leagues"][lg.code] = f"indisponible ({type(e).__name__}: {e})"
        if verbose:
            print(f"  {name} : indisponible ({e})")
        return
    report[name] = linked.report
    for lg in lgs:
        ms, league_info[lg.code] = _linked_matches(lg, linked, today, report)
        matches += ms
        if verbose:
            print(f"  {lg.code:>5} {lg.name_fr:<28} {len(ms)}/{report['leagues'][lg.code]['fixtures']} matchs analysés")


def run(today: date | None = None, leagues: tuple[League, ...] = LEAGUES, verbose: bool = True) -> dict:
    today = today or date.today()
    start = current_season_start(today)
    seasons = season_codes(start, 4)
    odds_rows = load_upcoming_odds()
    matches, report = [], {"unmatched": [], "leagues": {}}
    league_info: dict[str, dict] = {}
    for lg in (lg for lg in leagues if lg.category == "domestic"):
        hist = load_history(lg.code, seasons)
        if len(hist) < 100:
            report["leagues"][lg.code] = "pas assez de données"
            continue
        events = league_rounds(lg, today + timedelta(days=HORIZON_DAYS))
        fixtures = _upcoming(lg, today, events)
        league_info[lg.code] = _badge(lg, fixtures)
        tsdb_teams = {f.home_tsdb for f in fixtures} | {f.away_tsdb for f in fixtures}
        tsdb_teams |= {n for e, _, _ in finished(events) for n in (e.get("strHomeTeam"), e.get("strAwayTeam")) if n}
        names = match_names(sorted(tsdb_teams), _season_teams(hist, start))
        fresh = _fresh_results(lg, events, hist, names)
        if fresh:
            hist = sorted(hist + fresh, key=lambda m: m.date)
        model = fit(hist, today, include_ref_day=True)
        quality = {t: a - d for t, a, d in model.ratings()}  # attaque moins défense : sert à choisir le match à la une
        n_ok = 0
        for f in fixtures:
            h, a = names.get(f.home_tsdb), names.get(f.away_tsdb)
            if not (h and a and model.knows(h) and model.knows(a)):
                report["unmatched"].append(f"{lg.code}: {f.home_tsdb} - {f.away_tsdb}")
                continue
            row = next((r for r in odds_rows if r.league == lg.code and r.home == h and r.away == a
                        and abs((r.date - f.kickoff_utc.date()).days) <= 1), None)
            odds = _odds_markets(row) if row else {}
            model_pred = predict(model, h, a)
            source = "model"
            pred = model_pred
            if ("1x2", None) in odds:
                # Les cotes du marché sont plus précises que notre modèle seul (voir docs/05-fiabilite.md) :
                # on cale les buts attendus sur elles, puis on en déduit tous les autres marchés.
                sel = odds[("1x2", None)]
                p1x2 = devig([sel[k]["avg"] for k in ("1", "X", "2")])
                ou = odds.get(("ou", 2.5))
                p_over = devig([ou["over"]["avg"], ou["under"]["avg"]])[0] if ou else None
                lam, mu = implied_rates(p1x2, model.rho, p_over, start=(model_pred.lam, model_pred.mu))
                pred = predict_from_rates(model, h, a, lam, mu)
                source = "market"
            matches.append(_match_dict(lg, f, h, a, pred, model_pred, source, quality[h] + quality[a],
                                       "high" if source == "market" else confidence(model, h, a),
                                       _priced(pred, odds)))
            n_ok += 1
        report["leagues"][lg.code] = {"fixtures": len(fixtures), "predicted": n_ok, "train_matches": model.n_matches,
                                      "fresh_results": len(fresh),
                                      "rho": round(model.rho, 3), "home_adv": round(model.home_adv, 3),
                                      "first_half_share": round(model.first_half_share, 3)}
        if verbose:
            extra = f", dont {len(fresh)} résultats tout récents" if fresh else ""
            print(f"  {lg.code:>3} {lg.name_fr:<15} {n_ok}/{len(fixtures)} matchs analysés "
                  f"({model.n_matches} matchs d'entraînement{extra})")
    _run_linked("europe", men_cups, [lg for lg in leagues if lg.category == "europe"], today, matches, report,
                league_info, verbose)
    _run_linked("women", women, [lg for lg in leagues if lg.category == "women"], today, matches, report,
                league_info, verbose)
    matches.sort(key=lambda m: m["kickoff"])
    return {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "leagues": league_info, "matches": matches, "report": report}


def _top_scores(pred: Prediction, n: int) -> list[list]:
    ft = pred.ft
    cells = sorted(((float(ft[h, a]), h, a) for h in range(6) for a in range(6)), reverse=True)[:n]
    return [[f"{h}-{a}", round(p, 4)] for p, h, a in cells]
