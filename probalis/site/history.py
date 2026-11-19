"""Historique des paris du jour : enregistrés avant les matchs, réglés tout seuls avec le score final.

Le fichier vit sur le site lui-même (/data/history.json) : chaque construction relit la version en ligne,
y ajoute les listes des jours à venir et les résultats des matchs terminés, puis la republie.
Une copie est gardée dans data/cache/history.json (utile si le site est momentanément injoignable).

Règle d'honnêteté : la liste d'un jour est figée dès le premier calcul fait ce jour-là (ou plus tard) ;
ensuite elle ne change plus, même si le modèle change d'avis. Les listes des jours suivants restent
provisoires jusque-là. Tout pari enregistré a donc été publié avant le coup d'envoi de son match.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..football import fixtures
from ..football.data import CACHE, USER_AGENT
from . import picks

LOCAL = CACHE / "history.json"
VERSION = 1
SETTLE_AFTER = timedelta(hours=2, minutes=30)   # un match est fini environ 2 h après le coup d'envoi
GIVE_UP_AFTER = timedelta(days=6)                # sans score au bout de 6 jours (reporté, annulé) : remboursé
MAX_LOOKUPS = 40                                 # appels TheSportsDB par construction pour les scores manquants


def _empty() -> dict:
    return {"version": VERSION, "days": {}}


def _remote(site_url: str) -> dict | None:
    """Version en ligne. None si elle n'existe pas encore (le site renvoie alors sa page d'accueil)."""
    req = urllib.request.Request(f"{site_url}/data/history.json", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            ctype = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    if "json" not in ctype:
        return None
    data = json.loads(body.decode("utf-8"))
    return data if isinstance(data, dict) and "days" in data else None


def _settled(entry: dict) -> int:
    return sum(1 for mt in entry.get("matches", {}).values() if mt.get("score") or mt.get("void"))


def merge(a: dict | None, b: dict | None) -> dict:
    """Réunit deux versions : pour chaque jour, la liste figée d'abord, puis celle qui a le plus de résultats."""
    out = _empty()
    for src in (a, b):
        for day, e in ((src or {}).get("days") or {}).items():
            cur = out["days"].get(day)
            if cur is None or (e.get("frozen") and not cur.get("frozen")) or \
                    (e.get("frozen") == cur.get("frozen") and _settled(e) > _settled(cur)):
                out["days"][day] = e
    return out


def load(site_url: str) -> dict:
    """Historique actuel : version en ligne + copie locale. Échoue si le site est injoignable et qu'aucune
    copie locale n'existe (on ne republie jamais un historique vide par erreur)."""
    local = None
    if LOCAL.exists():
        try:
            local = json.loads(LOCAL.read_text(encoding="utf-8"))
        except ValueError:
            local = None
    remote = None
    if site_url:
        try:
            remote = _remote(site_url)
        except Exception as e:  # réseau, page cassée…
            if local is None:
                raise RuntimeError(f"Historique en ligne illisible ({e}) et pas de copie locale : arrêt.") from e
            print(f"  (historique en ligne illisible : {e} ; copie locale utilisée)")
    return merge(remote, local)


def _match_info(m: dict) -> dict:
    return {"slug": m["slug"], "league": m["league"], "kickoff": m["kickoff"], "conf": m.get("confidence"),
            "home": {"name": m["home"]["name"], "badge": m["home"].get("badge")},
            "away": {"name": m["away"]["name"], "badge": m["away"].get("badge")}}


def _slim(c: dict) -> dict:
    return {k: c[k] for k in ("id", "mid", "key", "line", "sel", "p", "fair")}


def day_lists(matches: list[dict], after: datetime | None) -> dict:
    """Les trois listes et les coupons d'un jour, avec ce qu'il faut pour les afficher plus tard."""
    tiers = {t: [_slim(c) for c in picks.tier_picks(matches, t, after=after)] for t in picks.TIERS}
    coupons = [{"target": cp["target"], "p": cp["p"], "fair": cp["fair"], "book": cp["book"],
                "legs": [_slim(c) for c in cp["legs"]]} for cp in picks.day_coupons(matches, after=after)]
    used = {c["mid"] for lst in tiers.values() for c in lst} | {c["mid"] for cp in coupons for c in cp["legs"]}
    by_id = {m["id"]: m for m in matches}
    return {"tiers": tiers, "coupons": coupons, "matches": {mid: _match_info(by_id[mid]) for mid in sorted(used)}}


def update(hist: dict, matches: list[dict], now: datetime) -> dict:
    """Ajoute ou recalcule les listes des jours à venir ; fige celles d'aujourd'hui et des jours passés."""
    today = picks.day_key(now)
    days = hist.setdefault("days", {})
    for day, e in days.items():
        if day <= today:
            e["frozen"] = True
    by_day: dict[str, list[dict]] = {}
    for m in matches:
        by_day.setdefault(picks.day_key(m["kickoff"]), []).append(m)
    for day, ms in sorted(by_day.items()):
        if day < today or (days.get(day) or {}).get("frozen"):
            continue
        lists = day_lists(ms, after=now)
        if not lists["matches"]:
            continue
        days[day] = {"built": now.isoformat(timespec="seconds"), "frozen": day == today, **lists}
    return hist


def _scores_from_cache() -> dict[str, dict]:
    """Matchs déjà téléchargés (journées de championnat, coupes) : idEvent -> événement TheSportsDB."""
    out = {}
    for f in (CACHE / "tsdb").glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for e in (data.get("events") or []) if isinstance(data, dict) else []:
            if isinstance(e, dict) and e.get("idEvent"):
                out[str(e["idEvent"])] = e
    return out


_VOID_STATUS = {"postponed", "pst", "cancelled", "canc", "abandoned", "abd"}


def settle(hist: dict, now: datetime, lookups: int = MAX_LOOKUPS) -> int:
    """Remplit les scores des matchs terminés, puis le résultat de chaque pari et de chaque coupon."""
    known = None
    filled = 0
    for day in sorted(hist.get("days", {})):
        e = hist["days"][day]
        if not e.get("frozen"):
            continue
        for mid, mt in e.get("matches", {}).items():
            if mt.get("score") or mt.get("void"):
                continue
            ko = datetime.fromisoformat(mt["kickoff"])
            if now < ko + SETTLE_AFTER:
                continue
            if known is None:
                known = _scores_from_cache()
            ev = known.get(mid)
            sc = fixtures.score(ev) if ev else None
            if sc is None and lookups > 0:
                lookups -= 1
                res = fixtures._get("lookupevent", {"id": mid}, 2)
                ev = ((res or {}).get("events") or [None])[0]
                if ev:
                    known[mid] = ev
                    sc = fixtures.score(ev)
            status = ((ev or {}).get("strStatus") or "").strip().lower()
            if sc:
                mt["score"] = list(sc)
                filled += 1
            elif status in _VOID_STATUS or now > ko + GIVE_UP_AFTER:
                mt["void"] = True
                filled += 1
        _apply_results(e)
    return filled


def _leg_result(e: dict, c: dict) -> str | None:
    mt = e["matches"].get(c["mid"]) or {}
    if mt.get("void"):
        return "void"
    if not mt.get("score"):
        return None
    hg, ag = mt["score"]
    return picks.settle(c["key"], c["line"], c["sel"], hg, ag)


def _apply_results(e: dict) -> None:
    for lst in e.get("tiers", {}).values():
        for c in lst:
            c["res"] = _leg_result(e, c)
    for cp in e.get("coupons", []):
        for c in cp["legs"]:
            c["res"] = _leg_result(e, c)
        cp["res"] = picks.coupon_result([c["res"] for c in cp["legs"]])


def save(hist: dict, public_dir: Path, now: datetime) -> None:
    hist["version"] = VERSION
    hist["updated"] = now.isoformat(timespec="seconds")
    txt = json.dumps(hist, ensure_ascii=False, separators=(",", ":"))
    LOCAL.parent.mkdir(parents=True, exist_ok=True)
    LOCAL.write_text(txt, encoding="utf-8")
    public_dir.mkdir(parents=True, exist_ok=True)
    (public_dir / "history.json").write_text(txt, encoding="utf-8")


# --- Bilan ------------------------------------------------------------------------------------------------

def _rate(items: list[tuple[float, str]]) -> dict:
    done = [(p, r) for p, r in items if r in ("won", "lost")]
    n, won = len(done), sum(1 for _, r in done if r == "won")
    return {"n": n, "won": won, "rate": won / n if n else None,
            "announced": sum(p for p, _ in done) / n if n else None}


def summary(days: dict) -> dict:
    """Taux de réussite par niveau et par coupon, comparé à la chance annoncée."""
    tiers = {t: _rate([(c["p"], c.get("res")) for e in days.values() if e.get("frozen")
                       for c in e.get("tiers", {}).get(t, [])]) for t in picks.TIERS}
    coupons = {}
    for target in picks.COUPON_TARGETS:
        coupons[target] = _rate([(cp["p"], cp.get("res")) for e in days.values() if e.get("frozen")
                                 for cp in e.get("coupons", []) if cp["target"] == target])
    return {"tiers": tiers, "coupons": coupons,
            "days": sum(1 for e in days.values() if e.get("frozen"))}
