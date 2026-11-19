"""Construit le site PWA statique dans public/ (une version française et une version anglaise).

Usage : python -m probalis build      (récupère les données, calcule, génère le site)
        python -m probalis serve      (aperçu local sur http://localhost:8000)
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..football.leagues import BY_CODE, LEAGUES
from . import config, i18n
from .icons import GOOGLE_G, icon, logo_mark

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "public"
HERE = Path(__file__).resolve().parent
BRAND = ROOT / "brand"

CREST_COLORS = ("#1F2937", "#15803D", "#0E7490", "#7C3AED", "#B45309", "#BE123C", "#1D4ED8", "#4D7C0F")
LIKELY_MARKETS = (("dc", None, ("1X", "X2", "12")), ("ou", 1.5, ("over",)), ("ou", 3.5, ("under",)),
                  ("1x2", None, ("1", "2")), ("btts", None, ("yes", "no")), ("ou", 2.5, ("over", "under")))
COMPARE_MARKETS = (("1x2", None), ("dc", None), ("dnb", None), ("ou", 1.5), ("ou", 2.5), ("ou", 3.5), ("btts", None))
RING = 2 * math.pi * 23  # anneau de probabilité (rayon 23 px) sur la page Paris
LEGAL_PAGES = (("confidentialite", "privacy_title"), ("conditions", "terms_title"),
               ("jeu-responsable", "responsible_page_title"))


def _img(url: str | None, size: str) -> str | None:
    """Logos TheSportsDB : /tiny = 100 px (listes), /small = 200 px (grands blasons)."""
    return f"{url}/{size}" if url else None


def _crest(team: dict) -> dict:
    name = team["name"]
    words = [w for w in name.replace("-", " ").split() if w[0].isalnum()]
    initials = (words[0][:1] + (words[1][:1] if len(words) > 1 else words[0][1:2])).upper() if words else "?"
    color = CREST_COLORS[int(hashlib.md5(name.encode()).hexdigest(), 16) % len(CREST_COLORS)]
    badge = team.get("badge")
    return {"initials": initials, "color": color, "img": _img(badge, "tiny"), "img_lg": _img(badge, "small")}


# --- Championnats : rubriques de la feuille « Championnats » et ordre d'affichage --------------------------

def category(lg) -> str:
    return getattr(lg, "category", None) or "domestic"


def league_sections() -> list[tuple[str, list]]:
    """Les plus suivis (5 premiers championnats), coupes d'Europe, autres championnats, féminin."""
    domestic = [lg for lg in LEAGUES if category(lg) == "domestic"]
    europe = [lg for lg in LEAGUES if category(lg) == "europe"]
    women = [lg for lg in LEAGUES if category(lg) == "women"]
    other = [lg for lg in LEAGUES if category(lg) not in ("domestic", "europe", "women")]
    return [("popular", domestic[:5]), ("europe", europe), ("others", domestic[5:] + other), ("women", women)]


def _section_of() -> dict[str, str]:
    return {lg.code: key for key, lgs in league_sections() for lg in lgs}


def _league_view(lg, lang: str, info: dict, count: int) -> dict:
    fr = lang == "fr"
    name = lg.name_fr if fr else lg.name_en
    country = lg.country_fr if fr else lg.country_en
    badge = (info.get(lg.code) or {}).get("badge")
    words = [w for w in name.replace("-", " ").split() if w[:1].isalnum()]
    return {"code": lg.code, "name": name, "country": country, "logo": _img(badge, "tiny"),
            "on_dark": bool((info.get(lg.code) or {}).get("badge_on_dark")),
            "initials": "".join(w[0] for w in words[:2]).upper() or "?", "count": count,
            "search": i18n.fold(f"{name} {country} {lg.name_en} {lg.country_en} {lg.name_fr} {lg.country_fr}")}


# --- Vues d'un match ------------------------------------------------------------------------------------

def _level(p: float) -> str:
    return "hi" if p >= 0.7 else "mid" if p >= 0.5 else "lo"


def _sel_view(m: dict, mk: dict, key_sel: str, lang: str) -> dict:
    s = mk["sel"][key_sel]
    line = mk.get("line")
    return {
        "label": i18n.selection_label(mk["key"], key_sel, line, lang, m["home"]["name"], m["away"]["name"]),
        "p": s["p"], "pct": i18n.pct(s["p"], lang), "w": round(min(max(s["p"], 0), 1) * 100, 1), "level": _level(s["p"]),
        "fair": i18n.odds(s["fair"], lang) if s.get("fair") and s["fair"] < 1000 else "—",
        "push": i18n.pct(s["pu"], lang) if s.get("pu") else None,
    }


def _market_view(m: dict, mk: dict, lang: str) -> dict:
    sels = list(mk["sel"])
    is_score = mk["key"] in ("score", "score_1h", "score_2h")
    if is_score:
        sels = sorted((s for s in sels if s != "other"), key=lambda s: -mk["sel"][s]["p"])[:12] + ["other"]
    return {"title": i18n.market_title(mk["key"], mk.get("line"), lang, m["home"]["name"], m["away"]["name"]),
            "rows": [_sel_view(m, mk, s, lang) for s in sels], "tiles": is_score,
            "free": mk["key"] in config.FREE_MARKETS}


def _find(m: dict, key: str, line=None) -> dict | None:
    return next((mk for mk in m["markets"] if mk["key"] == key and mk.get("line") == line), None)


def _key_markets(m: dict, lang: str) -> list[dict]:
    """Les six marchés du résumé : double chance du favori, buts, les deux marquent, l'outsider marque, la pause."""
    t = i18n.UI[lang]
    home, away = m["home"]["name"], m["away"]["name"]
    x12 = _find(m, "1x2")["sel"]
    fav_home = x12["1"]["p"] >= x12["2"]["p"]
    out = []

    def add(key, line, sel, label=None, market=None):
        mk = _find(m, key, line)
        if not mk or sel not in mk["sel"]:
            return
        sv = _sel_view(m, mk, sel, lang)
        out.append({**sv, "label": label or sv["label"], "free": key in config.FREE_MARKETS,
                    "market": market or i18n.market_title(key, line, lang, home, away)})

    def most(key, line=None):
        sel = _find(m, key, line)["sel"]
        return max(sel, key=lambda k: sel[k]["p"])

    add("dc", None, "1X" if fav_home else "X2")
    for line, sel in ((1.5, "over"), (2.5, most("ou", 2.5))):
        add("ou", line, sel, label=f"{i18n.selection_label('ou', sel, line, lang, home, away)} {t['goals_word']}",
            market=t["total_goals"])
    add("btts", None, most("btts"))
    underdog = away if fav_home else home
    add("tt2" if fav_home else "tt1", 0.5, "over", label=t["team_scores"].format(team=underdog),
        market=t["goals_of"].format(team=underdog))
    ht = most("1x2_1h")
    add("1x2_1h", None, ht, market=t["first_half"],
        label=t["ht_draw"] if ht == "X" else t["ht_lead"].format(team=home if ht == "1" else away))
    return out


def _compare_label(key: str, s: str, line, lang: str, home: str, away: str) -> str:
    """Libellé sans ambiguïté dans la liste déroulante (« Victoire Arsenal », « Plus de 2,5 buts »…)."""
    t = i18n.UI[lang]
    base = i18n.selection_label(key, s, line, lang, home, away)
    if key == "1x2":
        return t["draw_long"] if s == "X" else t["home_win"].format(team=base)
    if key == "dnb":
        return f"{base} ({t['dnb_short']})"
    if key == "ou":
        return f"{base} {t['goals_word']}"
    if key == "btts":
        return f"{t['btts_short']}{i18n.JS_COLON[lang]}{base.lower()}"
    return base


def _compare(m: dict, lang: str, best: int) -> dict:
    """Sélections proposées dans « Compare ta cote » : probabilité et cote juste de chacune."""
    home, away = m["home"]["name"], m["away"]["name"]
    groups, items = [], {}
    for key, line in COMPARE_MARKETS:
        mk = _find(m, key, line)
        if not mk:
            continue
        opts = []
        for s, v in mk["sel"].items():
            if not v.get("fair"):
                continue
            sid = f"{key}|{line}|{s}"
            items[sid] = {"p": round(v["p"], 5), "fair": round(v["fair"], 4)}
            opts.append({"id": sid, "label": _compare_label(key, s, line, lang, home, away)})
        groups.append({"title": i18n.market_title(key, line, lang, home, away), "opts": opts})
    return {"groups": groups, "items": items, "default": f"1x2|None|{'1X2'[best]}", "source": m["source"]}


def _round_txt(m: dict, lang: str) -> str | None:
    r = str(m.get("round") or "")
    if r == "200":  # TheSportsDB : 200 = finale des coupes
        return i18n.UI[lang]["final"]
    if r.isdigit() and 0 < int(r) <= 50:
        return i18n.UI[lang]["round"].format(n=int(r))
    return None


def _match_view(m: dict, lang: str, info: dict, sections: dict) -> dict:
    lg = BY_CODE[m["league"]]
    t = i18n.UI[lang]
    x12 = _find(m, "1x2")["sel"]
    ou = _find(m, "ou", 2.5)["sel"]
    btts = _find(m, "btts")["sel"]
    ps = [x12[k]["p"] for k in ("1", "X", "2")]
    best = ps.index(max(ps))
    groups = []
    for g in i18n.GROUP_ORDER:
        mks = [_market_view(m, mk, lang) for mk in m["markets"] if mk["group"] == g]
        if mks:
            groups.append({"key": g, "title": t["groups"][g], "markets": mks,
                           "locked": not any(mk["free"] for mk in mks)})
    priced = [dict(e, label=i18n.selection_label(e["key"], e["sel"], e["line"], lang, m["home"]["name"], m["away"]["name"]),
                   market=i18n.market_title(e["key"], e["line"], lang, m["home"]["name"], m["away"]["name"]),
                   pct=i18n.pct(e["p"], lang), fair_txt=i18n.odds(e["fair"], lang), best_txt=i18n.odds(e["best"], lang),
                   margin_txt=i18n.pct(e["margin"], lang), better=e["best"] > e["fair"])
              for e in (m.get("priced") or {}).values()]
    lam, mu = m["xg"]
    badge = (info.get(m["league"]) or {}).get("badge")
    ko = datetime.fromisoformat(m["kickoff"])
    return {
        **m,
        "section": sections.get(m["league"], "others"),
        "league_name": lg.name_fr if lang == "fr" else lg.name_en,
        "country": lg.country_fr if lang == "fr" else lg.country_en,
        "league_logo": _img(badge, "tiny"),
        "league_on_dark": bool((info.get(m["league"]) or {}).get("badge_on_dark")),  # logo blanc (coupes UEFA)
        "round_txt": _round_txt(m, lang),
        "home_crest": _crest(m["home"]), "away_crest": _crest(m["away"]),
        "p1": ps[0], "px": ps[1], "p2": ps[2], "best": best,
        "p1_txt": i18n.pct(ps[0], lang), "px_txt": i18n.pct(ps[1], lang), "p2_txt": i18n.pct(ps[2], lang),
        "over25": i18n.pct(ou["over"]["p"], lang), "btts_yes": i18n.pct(btts["yes"]["p"], lang),
        "xg_home": i18n.dec(lam, lang, 1), "xg_away": i18n.dec(mu, lang, 1), "xg_total": i18n.dec(lam + mu, lang, 1),
        "xg_share": round(100 * lam / (lam + mu), 1) if lam + mu > 0 else 50,
        "xg_txt": f"{i18n.num(lam, lang, 1)} – {i18n.num(mu, lang, 1)}",
        "top_scores": [(s.replace("-", " - "), i18n.pct(p, lang)) for s, p in m["top_score"]],
        "day_short": i18n.day_short(ko, lang), "day_med": i18n.day_med(ko, lang),
        "groups": groups, "priced_view": priced, "n_markets": len(m["markets"]),
        "key_markets": _key_markets(m, lang), "compare": _compare(m, lang, best),
    }


def _money(amount: float, cur: str, decimals: int, lang: str) -> str:
    """Prix affiché sans JavaScript (le téléphone le remplace ensuite par celui de son pays)."""
    n = f"{amount:,.{decimals}f}"
    n = n.replace(",", " ").replace(".", ",") if lang == "fr" else n
    sym = {"EUR": "€", "USD": "$", "GBP": "£"}.get(cur)
    if not sym:
        return f"{n} {cur}"
    return f"{n} {sym}" if lang == "fr" else f"{sym}{n}"


def _featured(views: list[dict]) -> tuple[list[dict], str | None]:
    """Candidats « à la une » : la plus belle affiche de chaque championnat, chaque jour.

    Le téléphone choisit ensuite selon le jour et les championnats affichés, en préférant les grands
    championnats et les coupes d'Europe. Sans JavaScript, on montre la plus belle affiche du premier jour.
    """
    best: dict[tuple, dict] = {}
    for v in views:
        k = (v["kickoff"][:10], v["league"])
        if k not in best or (v.get("stature") or 0) > (best[k].get("stature") or 0):
            best[k] = v
    cands = sorted(best.values(), key=lambda v: v["kickoff"])
    if not cands:
        return [], None
    first = [v for v in cands if v["kickoff"][:10] == cands[0]["kickoff"][:10]]
    lead = max([v for v in first if v["section"] in ("popular", "europe")] or first, key=lambda v: v.get("stature") or 0)
    return cands, lead["id"]


def _likely(views: list[dict], lang: str, n: int = 15) -> list[dict]:
    out = []
    for v in views:
        for key, line, sels in LIKELY_MARKETS:
            mk = _find(v, key, line)
            if not mk:
                continue
            for s in sels:
                sv = _sel_view(v, mk, s, lang)
                if sv["p"] >= 0.7:
                    home, away = v["home"]["name"], v["away"]["name"]
                    out.append({"match": v, "market": i18n.market_title(key, line, lang, home, away),
                                "dash": f"{RING * sv['p']:.1f} {RING:.1f}", **sv,
                                "label": _compare_label(key, s, line, lang, home, away)})
    out.sort(key=lambda e: -e["p"])
    return out[:n]


def build(data: dict) -> Path:
    env = Environment(loader=FileSystemLoader(HERE / "templates"), autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    env.globals.update(icon=icon, logo_mark=logo_mark, google_g=GOOGLE_G)
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    shutil.copytree(HERE / "static", PUBLIC / "assets")
    icons = PUBLIC / "icons"
    icons.mkdir()
    for f in (BRAND / "png").iterdir():
        shutil.copy2(f, icons / f.name)
    shutil.copy2(BRAND / "probalis-icone.svg", icons / "probalis-icone.svg")

    version = datetime.now().strftime("%Y%m%d%H%M%S")
    generated = datetime.fromisoformat(data["generated_at"])
    info = data.get("leagues") or {}
    sections = _section_of()
    cfg, site = config.public_config(), config.site()
    for lang in i18n.LANGS:
        t = i18n.UI[lang]
        views = [_match_view(m, lang, info, sections) for m in data["matches"] if m["league"] in BY_CODE]
        common = {"lang": lang, "t": t, "other_lang": "en" if lang == "fr" else "fr", "version": version,
                  "generated": generated, "generated_iso": data["generated_at"], "js": i18n.js_strings(lang),
                  "cfg": cfg, "site": site, "free_markets": sorted(config.FREE_MARKETS)}
        out = PUBLIC / lang
        (out / "match").mkdir(parents=True)

        counts: dict[str, int] = {}
        for v in views:
            counts[v["league"]] = counts.get(v["league"], 0) + 1
        sheet, groups, chips = [], [], []
        for key, lgs in league_sections():
            if not lgs:
                continue
            lviews = [_league_view(lg, lang, info, counts.get(lg.code, 0)) for lg in lgs]
            sheet.append({"key": key, "title": t["sec_" + key], "leagues": lviews})
            for lv in lviews:
                if lv["count"]:
                    chips.append(lv)
                    groups.append({**lv, "matches": [v for v in views if v["league"] == lv["code"]]})

        featured, lead = _featured(views)
        (out / "index.html").write_text(env.get_template("matches.html").render(
            **common, page="matches", root="", path="index.html", groups=groups, chips=chips, sheet=sheet,
            featured=featured, lead=lead, n_matches=len(views)), encoding="utf-8")
        (out / "paris.html").write_text(env.get_template("bets.html").render(
            **common, page="bets", likely=_likely(views, lang), root="", path="paris.html"), encoding="utf-8")
        for page, key in (("ticket", "ticket"), ("historique", "history")):
            (out / f"{page}.html").write_text(env.get_template("soon.html").render(
                **common, page=page, root="", path=f"{page}.html", title=t[f"{key}_title"],
                message=t[f"{key}_soon"], features=t[f"{key}_features"],
                big_icon="ticket" if key == "ticket" else "history"), encoding="utf-8")
        # Compte, offres Premium, pages légales
        (out / "compte.html").write_text(env.get_template("account.html").render(
            **common, page="compte", root="", path="compte.html", sheet=sheet), encoding="utf-8")
        cur = cfg["prices"]["default_currency"][lang]
        cp = cfg["prices"]["currencies"][cur]
        (out / "premium.html").write_text(env.get_template("premium.html").render(
            **common, page="premium", root="", path="premium.html",
            price_week=_money(cp["week"], cur, cp["decimals"], lang),
            price_month=_money(cp["month"], cur, cp["decimals"], lang)), encoding="utf-8")
        for doc, key in LEGAL_PAGES:
            (out / f"{doc}.html").write_text(env.get_template("legal.html").render(
                **common, page="legal", root="", path=f"{doc}.html", doc=doc, title=t[key]), encoding="utf-8")
        for v in views:
            (out / "match" / f"{v['slug']}.html").write_text(env.get_template("match.html").render(
                **common, page="matches", m=v, root="../", path=f"match/{v['slug']}.html"), encoding="utf-8")

    (PUBLIC / "index.html").write_text(env.get_template("root.html").render(version=version), encoding="utf-8")
    fonts = sorted(f"/assets/fonts/{f.name}" for f in (HERE / "static" / "fonts").glob("*.woff2"))
    (PUBLIC / "sw.js").write_text((HERE / "sw.template.js").read_text(encoding="utf-8")
                                  .replace("__VERSION__", version).replace("'__FONTS__'", json.dumps(fonts)[1:-1]),
                                  encoding="utf-8")
    (PUBLIC / "manifest.webmanifest").write_text(json.dumps({
        "name": "Probalis", "short_name": "Probalis", "description": "La science du pari · The science of betting",
        "start_url": "/", "scope": "/", "display": "standalone", "background_color": "#F3F5F8", "theme_color": "#F3F5F8",
        "icons": [{"src": "/icons/icone-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
                  {"src": "/icons/icone-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
                  {"src": "/icons/icone-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    data_dir = PUBLIC / "data"
    data_dir.mkdir()
    (data_dir / "matches.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return PUBLIC
