"""Le « pourquoi » d'une analyse : les facteurs du moteur (football/engine.py) mis en phrases, en FR et en EN.

Mots prudents : on dit ce que les chiffres suggèrent, jamais que c'est sûr.
"""
from __future__ import annotations


def _num(x: float, lang: str, digits: int = 1, signed: bool = False) -> str:
    s = f"{x:+.{digits}f}" if signed else f"{x:.{digits}f}"
    s = s.replace("-", "−")
    return s.replace(".", ",") if lang == "fr" else s


def _ord(r: int, lang: str) -> str:
    if lang == "fr":
        return "1re" if r == 1 else f"{r}e"
    return f"{r}{'th' if 10 <= r % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(r % 10, 'th')}"


def _goal(d: float, lang: str) -> str:
    n = _num(d, lang, 1, signed=True)
    if lang == "fr":
        return f"{n} but" if abs(d) < 1.95 else f"{n} buts"
    return f"{n} goal" if abs(d) < 1.05 else f"{n} goals"


def _rank_text(kind: str, team: str, r: int, n: int, v: float, lang: str) -> tuple[str, str]:
    """Phrase sur l'attaque ou la défense d'une équipe, et son ton (pos, neg, mid)."""
    fr = lang == "fr"
    vs = _num(v, lang, 1)
    if kind == "att":
        unit = f"{vs} buts marqués par match face à une équipe moyenne" if fr else \
            f"{vs} goals scored per game against an average side"
        noun = "attaque" if fr else "attack"
    else:
        unit = f"{vs} buts encaissés par match face à une équipe moyenne" if fr else \
            f"{vs} goals conceded per game against an average side"
        noun = "défense" if fr else "defence"
    top, bottom = max(1, round(n / 3)), n - max(1, round(n / 3)) + 1
    if r == 1:
        txt = f"{team} a la meilleure {noun} ({unit})" if fr else f"{team} have the best {noun} ({unit})"
        return txt, "pos"
    if r <= top:
        txt = (f"{team} a la {_ord(r, lang)} meilleure {noun} sur {n} ({unit})" if fr
               else f"{team} have the {_ord(r, lang)} best {noun} of {n} ({unit})")
        return txt, "pos"
    if r >= bottom:
        txt = (f"{team} a une des {noun}s les plus faibles ({_ord(r, lang)} sur {n}, {unit})" if fr
               else f"{team} have one of the weakest {noun}s ({_ord(r, lang)} of {n}, {unit})")
        return txt, "neg"
    txt = (f"{team} a une {noun} moyenne ({_ord(r, lang)} sur {n}, {unit})" if fr
           else f"{team} have an average {noun} ({_ord(r, lang)} of {n}, {unit})")
    return txt, "mid"


def render(factors: list[dict], lang: str, home: str, away: str) -> list[dict]:
    """[{text, tone, side, key}] dans l'ordre d'importance."""
    fr = lang == "fr"
    out = []
    for f in factors or []:
        team = home if f.get("side") == "h" else away
        k, d = f["k"], float(f.get("d") or 0)
        if k in ("att", "def"):
            text, tone = _rank_text(k, team, int(f["rank"]), int(f["n"]), float(f["v"]), lang)
        elif k == "home":
            text = (f"Avantage du terrain : {_goal(d, lang)} attendu pour {home}" if fr
                    else f"Home advantage: {_goal(d, lang)} expected for {home}")
            tone = "pos"
        elif k == "shots":
            if d >= 0:
                text = (f"{team} se crée plus d'occasions que ses buts ne le montrent : {_goal(d, lang)} attendu"
                        if fr else f"{team} create more chances than their goals show: {_goal(d, lang)} expected")
            else:
                text = (f"{team} marque plus que ses occasions ne le laissent prévoir : {_goal(d, lang)} attendu"
                        if fr else f"{team} score more than their chances suggest: {_goal(d, lang)} expected")
            tone = "pos" if d >= 0 else "neg"
        elif k == "form":
            text = (f"Forme récente de {team} {'en hausse' if d >= 0 else 'en baisse'} : {_goal(d, lang)} attendu"
                    if fr else f"{team}'s recent form is {'rising' if d >= 0 else 'falling'}: {_goal(d, lang)} expected")
            tone = "pos" if d >= 0 else "neg"
        elif k == "market":
            if fr:
                text = (f"Les cotes des bookmakers voient {team} {'plus' if d >= 0 else 'moins'} fort que nos "
                        f"statistiques : {_goal(d, lang)}")
            else:
                text = (f"Bookmakers' odds rate {team} {'higher' if d >= 0 else 'lower'} than our statistics: "
                        f"{_goal(d, lang)}")
            tone = "mid"
        elif k == "data":
            if f.get("conf") == "low":
                text = ("Peu de matchs récents sur ces équipes : analyse à prendre avec beaucoup de prudence" if fr
                        else "Few recent games for these teams: treat this analysis with great caution")
            else:
                text = ("Données moins complètes que pour les grands championnats : analyse à prendre avec prudence"
                        if fr else "Less complete data than for the major leagues: treat this analysis with caution")
            tone = "neg"
        else:
            continue
        out.append({"key": k, "side": f.get("side"), "text": text, "tone": tone})
    return out
