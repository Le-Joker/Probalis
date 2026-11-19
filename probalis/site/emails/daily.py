"""Tâche quotidienne des e-mails (GitHub Actions, une fois par jour, voir .github/workflows/emails.yml).

1. Rappel « ton Premium se termine bientôt » (1 à 3 jours avant), si le rappel est activé (activé par défaut).
2. « Grand choc demain » : le plus beau match de demain (ou de ses championnats favoris) aux inscrits qui ont
   activé les alertes, majeurs. Pas de grand match demain = pas d'e-mail ce jour-là.

Chaque envoi est d'abord noté dans la table email_log (un e-mail par personne, par sorte et par sujet) :
personne ne reçoit deux fois le même e-mail, même si la tâche est relancée.

Variables (secrets GitHub) : SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, RESEND_API_KEY, EMAIL_FROM,
UNSUBSCRIBE_SECRET, PROBALIS_SITE_URL. Optionnelles : EMAIL_DAILY_CAP (90 par défaut, l'offre gratuite de
Resend permet 100 e-mails par jour), BIG_MATCH_MIN (3.0), PROBALIS_DATA (fichier ou adresse de matches.json),
PROBALIS_CONTACT_EMAIL (adresse de réponse).
Sans ces secrets, la tâche s'arrête proprement sans rien envoyer.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from . import ROOT, LANGS, build_templates, fill, links, others_html, unsubscribe_token

UA = "probalis-emails/1.0"
MONTHS = {
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
           "novembre", "décembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December"],
}
MONTHS_SHORT = {
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}
DAYS = {"fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
        "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}


# --- Dates et chiffres ----------------------------------------------------------------------------------------

def _zone(tz: str | None):
    if tz:
        try:
            from zoneinfo import ZoneInfo
            return ZoneInfo(tz), False
        except Exception:  # fuseau inconnu ou base des fuseaux absente : heure universelle
            pass
    return timezone.utc, True


def fmt_date(iso: str, lang: str) -> str:
    d = _parse(iso)
    return f"{d.day} {MONTHS[lang][d.month - 1]} {d.year}"


def fmt_kickoff(iso: str, lang: str, tz: str | None) -> str:
    zone, utc = _zone(tz)
    d = _parse(iso).astimezone(zone)
    hm = d.strftime("%H:%M") + (" GMT" if utc else "")
    if lang == "fr":
        return f"{DAYS['fr'][d.weekday()]} {d.day} {MONTHS_SHORT['fr'][d.month - 1]} à {hm}"
    return f"{DAYS['en'][d.weekday()]} {d.day} {MONTHS_SHORT['en'][d.month - 1]}, {hm}"


def _parse(iso: str) -> datetime:
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def pct(p: float | None, lang: str) -> str:
    if p is None:
        return "–"
    return f"{round(p * 100)} %" if lang == "fr" else f"{round(p * 100)}%"


def _z(d: datetime) -> str:
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- Matchs ---------------------------------------------------------------------------------------------------

def local_data() -> dict | None:
    f = ROOT / "public" / "data" / "matches.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def load_data(site: str) -> dict | None:
    src = os.environ.get("PROBALIS_DATA", "").strip()
    if src and not src.startswith("http"):
        return json.loads(open(src, encoding="utf-8").read())
    url = src or (f"{site}/data/matches.json" if site else "")
    if url:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, ValueError) as e:
            print(f"Données des matchs introuvables à {url} : {e}")
    return local_data()


def _market(m: dict, key: str, line: float | None = None) -> dict:
    for mk in m.get("markets") or []:
        if mk.get("key") == key and (line is None or mk.get("line") == line):
            return mk.get("sel") or {}
    return {}


def _p(sel: dict, k: str) -> float | None:
    v = sel.get(k)
    return v.get("p") if isinstance(v, dict) else None


def big_matches(data: dict, now: datetime | None, minimum: float | None = None) -> list[dict]:
    """Matchs de demain (heure universelle), les plus attendus d'abord. now=None : tous les matchs (aperçus)."""
    minimum = float(os.environ.get("BIG_MATCH_MIN") or 3.0) if minimum is None else minimum
    ms = [m for m in data.get("matches") or [] if (m.get("stature") or 0) >= minimum and m.get("kickoff")]
    if now is not None:
        start = (now.astimezone(timezone.utc) + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        ms = [m for m in ms if start <= _parse(m["kickoff"]) < end]
    return sorted(ms, key=lambda m: -(m.get("stature") or 0))


def _league_name(code: str, lang: str) -> str:
    try:
        from ...football.leagues import BY_CODE
        lg = BY_CODE.get(code)
        return (lg.name_fr if lang == "fr" else lg.name_en) if lg else code
    except Exception:
        return code


def match_values(m: dict, others: list[dict], lang: str, site: str, tz: str | None = None) -> dict:
    x = _market(m, "1x2")
    model = m.get("model_1x2") or [None, None, None]
    p1, px, p2 = (_p(x, "1"), _p(x, "X"), _p(x, "2")) if x else tuple(model)
    badge = lambda t: f"{t['badge']}/small" if t.get("badge") else f"{site}/icons/icone-192.png"  # noqa: E731
    rows = [(f"{o['home']['name']} – {o['away']['name']}", _league_name(o["league"], lang),
             fmt_kickoff(o["kickoff"], lang, tz)) for o in others]
    title = "Les autres belles affiches de demain" if lang == "fr" else "Tomorrow's other big matches"
    return {
        "home": m["home"]["name"], "away": m["away"]["name"], "home_logo": badge(m["home"]), "away_logo": badge(m["away"]),
        "league": _league_name(m["league"], lang), "kickoff": fmt_kickoff(m["kickoff"], lang, tz),
        "p1": pct(p1, lang), "px": pct(px, lang), "p2": pct(p2, lang),
        "over25": pct(_p(_market(m, "ou", 2.5), "over"), lang), "btts": pct(_p(_market(m, "btts"), "yes"), lang),
        "match_url": f"{site}/{lang}/match/{m['slug']}.html",
        "others_html": others_html(rows, lang),
        "others_text": (title + "\n" + "\n".join(f"• {a} · {b} · {c}" for a, b, c in rows)) if rows else "",
    }


# --- Supabase et Resend (sans bibliothèque : urllib) ------------------------------------------------------------

class Http:
    def __init__(self, sb_url: str, sb_key: str, resend_key: str):
        self.sb_url, self.sb_key, self.resend_key = sb_url.rstrip("/"), sb_key, resend_key

    @staticmethod
    def call(method: str, url: str, headers: dict, body=None) -> tuple[int, object]:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method,
                                     headers={"User-Agent": UA, "Content-Type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read().decode("utf-8") or "null"
                return r.status, json.loads(raw)
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")[:500]

    def sb(self, method: str, path: str, body=None, prefer: str | None = None) -> object:
        h = {"apikey": self.sb_key}
        if self.sb_key.startswith("eyJ"):  # ancienne clé « service_role » (JWT) ; les nouvelles clés sb_secret_ non
            h["Authorization"] = f"Bearer {self.sb_key}"
        if prefer:
            h["Prefer"] = prefer
        status, data = self.call(method, f"{self.sb_url}/rest/v1/{path}", h, body)
        if status >= 300:
            raise RuntimeError(f"Supabase {method} {path.split('?')[0]} : {status} {data}")
        return data

    def resend_batch(self, emails: list[dict], key: str) -> tuple[bool, object]:
        status, data = self.call("POST", "https://api.resend.com/emails/batch",
                                 {"Authorization": f"Bearer {self.resend_key}", "Idempotency-Key": key}, emails)
        return status < 300, data


def _log(http: Http, rows: list[dict]) -> set[tuple[str, str, str]]:
    """Note les envois prévus ; ne renvoie que ceux qui n'avaient jamais été faits."""
    if not rows:
        return set()
    done = http.sb("POST", "email_log?on_conflict=user_id,kind,ref", rows,
                   prefer="resolution=ignore-duplicates,return=representation") or []
    return {(r["user_id"], r["kind"], r["ref"]) for r in done}


def _unlog(http: Http, rows: list[dict]) -> None:
    for r in rows:
        q = urllib.parse.urlencode({"user_id": f"eq.{r['user_id']}", "kind": f"eq.{r['kind']}", "ref": f"eq.{r['ref']}"})
        try:
            http.sb("DELETE", f"email_log?{q}")
        except RuntimeError as e:
            print(e)


def _first(name: str | None, email: str) -> str:
    n = (name or "").strip().split(" ")[0]
    return n or email.split("@")[0]


def run(dry: bool = False) -> int:
    env = {k: os.environ.get(k, "").strip() for k in (
        "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "RESEND_API_KEY", "EMAIL_FROM", "UNSUBSCRIBE_SECRET",
        "PROBALIS_SITE_URL")}
    missing = [k for k, v in env.items() if not v]
    if missing and not dry:
        print("::notice::E-mails non configurés (secrets manquants : " + ", ".join(missing) + "). Rien n'est envoyé.")
        return 0
    site = env["PROBALIS_SITE_URL"].rstrip("/")
    cap = int(os.environ.get("EMAIL_DAILY_CAP") or 90)
    now = datetime.now(timezone.utc)
    tpls = build_templates()
    http = Http(env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"], env["RESEND_API_KEY"])
    reply = os.environ.get("PROBALIS_CONTACT_EMAIL", "").strip()
    fn_base = f"{env['SUPABASE_URL'].rstrip('/')}/functions/v1/unsubscribe"

    def email(kind: str, p: dict, values: dict, unsub_kind: str | None) -> dict:
        lang = p.get("lang") if p.get("lang") in LANGS else "fr"
        t = tpls[kind][lang]
        v = {**links(site, lang), "name": _first(p.get("name"), p["email"]), **values}
        headers = {}
        if unsub_kind:
            tok = unsubscribe_token(p["id"], unsub_kind, env["UNSUBSCRIBE_SECRET"])
            # Lien dans l'e-mail : page Mon compte du site ; en-tête « un clic » des messageries : la fonction
            v["unsubscribe_url"] = f"{site}/{lang}/compte.html?" + urllib.parse.urlencode(
                {"desabo": unsub_kind, "u": p["id"], "t": tok})
            one_click = f"{fn_base}?" + urllib.parse.urlencode({"u": p["id"], "k": unsub_kind, "t": tok, "l": lang})
            headers = {"List-Unsubscribe": f"<{one_click}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}
        out = {"from": env["EMAIL_FROM"], "to": [p["email"]], "subject": fill(t["subject"], v, False),
               "html": fill(t["html"], v), "text": fill(t["text"], v, False)}
        if headers:
            out["headers"] = headers
        if reply:
            out["reply_to"] = reply
        return out

    if dry and missing:
        print("Simulation sans Supabase : seuls les matchs de demain sont calculés.")
        data = load_data(site)
        picks = big_matches(data or {}, now)
        print(f"{len(picks)} grand(s) match(s) demain :", ", ".join(f"{m['home']['name']} – {m['away']['name']} "
                                                                  f"({m['stature']})" for m in picks[:5]) or "aucun")
        return 0

    queue: list[tuple[dict, dict]] = []  # (ligne email_log, e-mail)

    # 1) Rappels de fin de Premium (entre 24 h et 72 h avant la fin)
    q = urllib.parse.urlencode({
        "select": "id,email,name,lang,premium_until",
        "email_reminders": "is.true", "email": "not.is.null",
        "and": f"(premium_until.gte.{_z(now + timedelta(hours=24))},premium_until.lt.{_z(now + timedelta(hours=72))})",
        "limit": "1000"})
    for p in http.sb("GET", f"profiles?{q}") or []:
        lang = p.get("lang") if p.get("lang") in LANGS else "fr"
        row = {"user_id": p["id"], "kind": "expiry", "ref": p["premium_until"][:10]}
        queue.append((row, email("expiry", p, {"until": fmt_date(p["premium_until"], lang)}, "reminders")))

    # 2) Grand choc demain
    data = load_data(site)
    picks = big_matches(data or {}, now)
    if picks:
        q = urllib.parse.urlencode({
            "select": "id,email,name,lang,favorite_leagues,tz", "email_news": "is.true", "is_adult": "is.true",
            "email": "not.is.null", "order": "created_at.asc", "limit": "5000"})
        for p in http.sb("GET", f"profiles?{q}") or []:
            lang = p.get("lang") if p.get("lang") in LANGS else "fr"
            fav = set(p.get("favorite_leagues") or [])
            mine = [m for m in picks if m["league"] in fav]
            main = (mine or picks)[0]
            others = [m for m in picks if m is not main][:3]
            row = {"user_id": p["id"], "kind": "big_match", "ref": main["slug"][:10]}  # une alerte par jour au plus
            queue.append((row, email("big_match", p, match_values(main, others, lang, site, p.get("tz")), "news")))
    else:
        print("Pas de grand match demain : pas d'alerte aujourd'hui.")

    if len(queue) > cap:
        print(f"::warning::{len(queue)} e-mails prévus, limite {cap} par jour : {len(queue) - cap} attendront demain.")
        queue = queue[:cap]
    print(f"{len(queue)} e-mail(s) à envoyer.")
    if dry:
        for row, e in queue[:10]:
            print(f"  [{row['kind']}] {e['subject']}")
        return 0

    fresh = _log(http, [row for row, _ in queue])
    todo = [(row, e) for row, e in queue if (row["user_id"], row["kind"], row["ref"]) in fresh]
    sent = 0
    for i in range(0, len(todo), 100):
        chunk = todo[i:i + 100]
        ok, res = http.resend_batch([e for _, e in chunk], f"probalis-daily-{now:%Y-%m-%d}-{i // 100}")
        if ok:
            sent += len(chunk)
        else:
            print(f"::error::Resend a refusé l'envoi : {res}")
            _unlog(http, [row for row, _ in chunk])  # on réessaiera au prochain passage
    print(f"{sent} e-mail(s) envoyé(s), {len(queue) - len(todo)} déjà envoyé(s) avant.")
    return 0 if sent == len(todo) else 1


def send_test(to: str, lang: str) -> int:
    """Envoie les 4 modèles (valeurs d'exemple) à une adresse, pour vérifier la configuration de Resend."""
    from . import KINDS, SAMPLES
    key, sender = os.environ.get("RESEND_API_KEY", "").strip(), os.environ.get("EMAIL_FROM", "").strip()
    if not key or not sender:
        print("Il faut RESEND_API_KEY et EMAIL_FROM.")
        return 1
    site = (os.environ.get("PROBALIS_SITE_URL") or "https://example.com").rstrip("/")
    tpls = build_templates()
    v = {**SAMPLES[lang], **links(site, lang), "unsubscribe_url": f"{site}/{lang}/compte.html",
         "match_url": f"{site}/{lang}/", "home_logo": f"{site}/icons/icone-192.png", "away_logo": f"{site}/icons/icone-192.png"}
    data = load_data(site)
    picks = big_matches(data or {}, None)
    if picks:
        v.update(match_values(picks[0], picks[1:4], lang, site))
    emails = [{"from": sender, "to": [to], "subject": "[Test] " + fill(tpls[k][lang]["subject"], v, False),
               "html": fill(tpls[k][lang]["html"], v), "text": fill(tpls[k][lang]["text"], v, False)} for k in KINDS]
    ok, res = Http("", "", key).resend_batch(emails, f"probalis-test-{datetime.now(timezone.utc):%Y%m%d%H%M%S}")
    print("Envoyé." if ok else f"Refusé : {res}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run("--dry-run" in sys.argv))
