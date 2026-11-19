"""Les premiers matchs d'une journée annoncent-ils les suivants ?

Usage : python -m probalis.football.tendance

Pour chaque championnat et chaque jour où des matchs commencent à des heures différentes, on compare
la « surprise » des premiers matchs (résultat réel moins ce que prévoyaient les cotes) à celle des
matchs qui commencent au moins 2 heures plus tard. Si une tendance du jour existait, les deux surprises
iraient dans le même sens (corrélation nettement positive). Résultats : docs/05-fiabilite.md.
"""
from __future__ import annotations

import csv
import io
import math
import random
from collections import defaultdict

from .data import CACHE, load_season

CODES = ("E0", "SP1", "I1", "D1", "F1", "E1", "N1", "P1", "B1", "T1")
SEASONS = ("2223", "2324", "2425", "2526")
MEASURES = (("goals", "Buts en plus ou en moins que prévu"),
            ("over", "Plus de 2,5 buts plus ou moins souvent que prévu"),
            ("fav", "Favori qui gagne plus ou moins souvent que prévu"))


def _f(s: str | None) -> float | None:
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _goals_from_over(p: float) -> float:
    """Nombre de buts attendu (loi de Poisson) qui donne la probabilité p de « plus de 2,5 buts »."""
    lo, hi = 0.05, 8.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if 1 - math.exp(-mid) * (1 + mid + mid * mid / 2) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def surprises() -> list[dict]:
    rows = []
    for code in CODES:
        for season in SEASONS:
            load_season(code, season, is_current=False)  # télécharge le fichier s'il manque
            path = CACHE / f"{code}_{season}.csv"
            if not path.exists():
                continue
            raw = path.read_bytes()
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = raw.decode("latin-1")
            for r in csv.DictReader(io.StringIO(text)):
                t, d = (r.get("Time") or "").strip(), (r.get("Date") or "").strip()
                hg, ag = _f(r.get("FTHG")), _f(r.get("FTAG"))
                oh, od, oa = _f(r.get("AvgH")), _f(r.get("AvgD")), _f(r.get("AvgA"))
                oo, ou = _f(r.get("Avg>2.5")), _f(r.get("Avg<2.5"))
                if not (t and d and ":" in t and hg is not None and ag is not None and oh and od and oa and oo and ou):
                    continue
                hh, mm = t.split(":")[:2]
                inv = (1 / oh, 1 / od, 1 / oa)
                ph, pa = inv[0] / sum(inv), inv[2] / sum(inv)
                p_over = (1 / oo) / (1 / oo + 1 / ou)
                fav_won = hg > ag if ph >= pa else ag > hg
                rows.append({"day": (code, d), "minute": int(hh) * 60 + int(mm),
                             "goals": hg + ag - _goals_from_over(p_over),
                             "over": float(hg + ag > 2.5) - p_over,
                             "fav": float(fav_won) - max(ph, pa)})
    return rows


def pairs(rows: list[dict], gap_minutes: int = 120) -> list[tuple[dict, dict]]:
    """(surprise moyenne des premiers matchs du jour, match commencé au moins gap_minutes plus tard)."""
    days = defaultdict(list)
    for r in rows:
        days[r["day"]].append(r)
    out = []
    for ms in days.values():
        first = min(m["minute"] for m in ms)
        early = [m for m in ms if m["minute"] == first]
        mean = {k: sum(e[k] for e in early) / len(early) for k, _ in MEASURES}
        out += [(mean, m) for m in ms if m["minute"] >= first + gap_minutes]
    return out


def _corr(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / math.sqrt(sxx * syy)


def main() -> None:
    rows = surprises()
    ps = pairs(rows)
    print(f"{len(rows)} matchs ({', '.join(SEASONS)}), {len(ps)} matchs comparés aux premiers matchs de leur journée\n")
    rng = random.Random(1)
    idx = list(range(len(ps)))
    for k, label in MEASURES:
        xs, ys = [e[k] for e, _ in ps], [m[k] for _, m in ps]
        boots = sorted(_corr([xs[i] for i in s], [ys[i] for i in s])
                       for s in ([rng.choice(idx) for _ in idx] for _ in range(400)))
        print(f"{label} : corrélation {_corr(xs, ys):+.3f} (intervalle à 95 % : {boots[10]:+.3f} à {boots[389]:+.3f})")
    hi = [m["goals"] for e, m in ps if e["goals"] >= 1]
    lo = [m["goals"] for e, m in ps if e["goals"] <= -1]
    up = [m["fav"] for e, m in ps if e["fav"] <= -0.4]
    print(f"\nPremiers matchs avec 1 but ou plus de plus que prévu -> matchs suivants : {sum(hi) / len(hi):+.2f} but ({len(hi)})")
    print(f"Premiers matchs avec 1 but ou plus de moins que prévu -> matchs suivants : {sum(lo) / len(lo):+.2f} but ({len(lo)})")
    print(f"Favoris battus dans les premiers matchs -> favoris suivants : {100 * sum(up) / len(up):+.1f} points "
          f"par rapport aux cotes ({len(up)})")


if __name__ == "__main__":
    main()
