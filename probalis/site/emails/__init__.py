"""E-mails Probalis : bienvenue, reçu d'achat, rappel avant la fin du Premium, grand choc demain, cadeau de l'admin,
récompense du parrainage et Premium activé. Envoyés par Gmail (programme Google Apps Script, voir gmail_script.js)
ou par Resend, selon les secrets enregistrés.

Une seule source pour les modèles : ce fichier + layout.html. La commande
    python -m probalis.site.emails generate
écrit supabase/functions/_shared/emails.json (utilisé par les fonctions Supabase pour la bienvenue et les reçus)
et des aperçus à ouvrir dans le navigateur, dans docs/emails/.

Dans les modèles, {{nom}} est remplacé au moment de l'envoi (texte protégé), {{{nom}}} insère du HTML déjà préparé
par notre code. Le même remplissage existe en Python (ici) et en TypeScript (supabase/functions/_shared/email.ts).
"""
from __future__ import annotations

import hashlib
import hmac
import html
import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SHARED = ROOT / "supabase" / "functions" / "_shared"
PREVIEWS = ROOT / "docs" / "emails"
KINDS = ("welcome", "receipt", "expiry", "big_match", "gift", "reward", "premium_on")
LANGS = ("fr", "en")

_P = 'style="margin:0 0 14px;"'
_ROW = ('<tr><td style="padding:9px 0;border-bottom:1px solid #F0F2F6;color:#5B6B82;font-size:14px;">{k}</td>'
        '<td style="padding:9px 0;border-bottom:1px solid #F0F2F6;font-size:14px;font-weight:700;text-align:right;">{v}</td></tr>')


def _table(rows: list[tuple[str, str]]) -> str:
    inner = "".join(_ROW.format(k=k, v=v) for k, v in rows)
    return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:4px 0 6px;">{inner}</table>'


def _match_card(draw: str) -> str:
    cell = ('<td width="33%" align="center" style="padding:12px 4px;background:#F5F7FA;border-radius:12px;">'
            '<div style="font-size:22px;font-weight:700;color:#0B1F3A;">{p}</div>'
            '<div style="font-size:12px;color:#5B6B82;">{l}</div></td>')
    team = ('<td width="42%" align="center" valign="top" style="font-size:15px;font-weight:700;color:#0B1F3A;">'
            '<img src="{logo}" width="52" height="52" alt="" style="display:block;margin:0 auto 8px;border:0;">{name}</td>')
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:6px 0 14px;">'
        '<tr><td colspan="3" align="center" style="padding-bottom:12px;font-size:13px;font-weight:700;color:#5B6B82;">'
        '{{league}} · {{kickoff}}</td></tr><tr>'
        + team.format(logo="{{home_logo}}", name="{{home}}")
        + '<td width="16%" align="center" style="font-size:14px;font-weight:700;color:#7A889C;">VS</td>'
        + team.format(logo="{{away_logo}}", name="{{away}}")
        + '</tr></table>'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="6" border="0" style="margin:0 0 10px;"><tr>'
        + cell.format(p="{{p1}}", l="1") + cell.format(p="{{px}}", l=draw) + cell.format(p="{{p2}}", l="2")
        + '</tr></table>'
    )


TEXTS = {
    "fr": {
        "responsible": "18+ · Les probabilités ne sont pas des certitudes. Ne mise jamais plus que ce que tu peux perdre.",
        "manage": "Gérer mes e-mails", "unsub": "Me désinscrire",
        "reason_account": "Tu reçois cet e-mail parce que tu as un compte Probalis.",
        "reason_news": "Tu reçois cet e-mail parce que tu as activé les alertes des grands chocs.",
        "reason_reminders": "Tu reçois cet e-mail parce que tu as activé le rappel avant la fin du Premium.",
        "welcome": {
            "subject": "Bienvenue sur Probalis, {{name}}",
            "preheader": "Les vraies probabilités de chaque pari, sans promesse magique.",
            "kicker": "Bienvenue", "title": "Ravi de te compter parmi nous, {{name}} !",
            "body": [
                "Probalis calcule la vraie chance de chaque pari, à partir des cotes du marché et de nos modèles statistiques. Pas de « coup sûr », pas de « pari en or » : juste des chiffres honnêtes pour décider en connaissance de cause.",
                "<b>Pour bien démarrer :</b><br>• Chaque jour, tu as droit à 1 analyse complète gratuite : ouvre le match de ton choix et débloque-la.<br>• Utilise « Compare ta cote » : entre la cote de ton bookmaker, on te dit si c'est un bon prix.<br>• Active les alertes des grands chocs dans <a href=\"{{account_url}}\" style=\"color:#15803D;font-weight:700;\">Mon compte</a> : un e-mail la veille des plus belles affiches.",
                "Invite tes amis avec ton lien : chaque ami inscrit te rapporte des <b>analyses offertes</b>, à utiliser sur les matchs de ton choix. Tu le trouves dans <a href=\"{{rewards_url}}\" style=\"color:#15803D;font-weight:700;\">Récompenses</a>.",
                "Envie d'aller plus loin ? <a href=\"{{premium_url}}\" style=\"color:#15803D;font-weight:700;\">Premium</a> débloque l'analyse de tous les matchs, sans pub, avec un pass de 7 jours à 1 an, sans abonnement.",
            ],
            "cta": "Voir les matchs du jour", "cta_url": "{{home_url}}", "unsubscribe": False, "reason": "reason_account",
        },
        "receipt": {
            "subject": "Ton reçu Probalis Premium · {{plan}}",
            "preheader": "Merci ! Ton Premium est actif jusqu'au {{until}}.",
            "kicker": "Paiement confirmé", "title": "Merci {{name}}, ton Premium est actif !",
            "body": [
                "Voici le reçu de ton achat. Garde-le, il pourra t'être utile en cas de question.",
                _table([("Offre", "{{plan}}"), ("Montant", "{{amount}}"), ("Moyen de paiement", "{{provider}}"),
                        ("Date", "{{date}}"), ("Référence", "{{ref}}"), ("Premium actif jusqu'au", "{{until}}")]),
                "Paiement unique, <b>sans abonnement</b> : rien ne sera prélevé automatiquement à la fin de ton pass.",
            ],
            "cta": "Profiter du Premium", "cta_url": "{{home_url}}", "unsubscribe": False, "reason": "reason_account",
        },
        "expiry": {
            "subject": "Ton Premium se termine le {{until}}",
            "preheader": "Prolonge-le en un clic si tu veux garder l'analyse de tous les matchs.",
            "kicker": "Rappel", "title": "Ton Premium se termine bientôt",
            "body": [
                "Bonjour {{name}}, ton pass Premium prend fin le <b>{{until}}</b>.",
                "Ensuite, tu repasses automatiquement en gratuit (1 analyse complète par jour, avec quelques pubs). Rien n'est prélevé sans ton accord.",
                "Pour garder l'analyse de tous les matchs, sans pub, prends un nouveau pass : il s'ajoutera à la suite de l'actuel.",
            ],
            "cta": "Prolonger mon Premium", "cta_url": "{{premium_url}}", "unsubscribe": True, "reason": "reason_reminders",
        },
        "big_match": {
            "subject": "Demain : {{home}} – {{away}}, nos probabilités",
            "preheader": "{{league}} · {{kickoff}} · {{home}} {{p1}}, nul {{px}}, {{away}} {{p2}}",
            "kicker": "Grand choc demain", "title": "{{home}} – {{away}}",
            "body": [
                _match_card("Nul"),
                "Plus de 2,5 buts : <b>{{over25}}</b> · Les deux équipes marquent : <b>{{btts}}</b>",
                "{{{others_html}}}",
            ],
            "text": ["{{league}} · {{kickoff}}", "{{home}} {{p1}} · Nul {{px}} · {{away}} {{p2}}",
                     "Plus de 2,5 buts : {{over25}} · Les deux équipes marquent : {{btts}}"],
            "cta": "Voir l'analyse complète", "cta_url": "{{match_url}}", "unsubscribe": True, "reason": "reason_news",
        },
        "gift": {
            "subject": "{{name}}, un cadeau t'attend sur Probalis : {{gift}}",
            "preheader": "Touche « Activer la récompense » pour le recevoir sur ton compte.",
            "kicker": "Cadeau", "title": "Un cadeau pour toi, {{name}} !",
            "body": [
                "L'équipe Probalis t'offre un cadeau : <b>{{gift}}</b>.",
                "{{{note_html}}}",
                "Touche le bouton ci-dessous pour activer ta récompense. Elle arrivera dans l'onglet <b>Récompenses</b> de ton compte : tu pourras l'utiliser quand tu veux.",
                "Ce lien est valable jusqu'au {{expires}}. Si tu n'es pas connecté, Probalis te demandera d'abord de te connecter avec le compte Google qui reçoit cet e-mail.",
            ],
            "text": ["L'équipe Probalis t'offre un cadeau : {{gift}}.", "{{note}}",
                     "Active ta récompense avec ce lien (valable jusqu'au {{expires}}) : elle arrivera dans l'onglet Récompenses de ton compte."],
            "cta": "Activer la récompense", "cta_url": "{{claim_url}}", "unsubscribe": False, "reason": "reason_account",
        },
        "reward": {
            "subject": "+{{amount}} analyses offertes sur Probalis",
            "preheader": "{{why}}",
            "kicker": "Parrainage", "title": "Bravo {{name}} : +{{amount}} analyses offertes",
            "body": [
                "{{why}}",
                "Tes <b>{{amount}} analyses offertes</b> t'attendent dans l'onglet Récompenses de ton compte. Active-les, puis utilise-les sur les matchs de ton choix : chaque analyse offerte ouvre l'analyse complète d'un match.",
                "Continue d'inviter avec ton lien : <a href=\"{{invite_url}}\" style=\"color:#15803D;font-weight:700;\">{{invite_url}}</a>",
            ],
            "cta": "Voir mes récompenses", "cta_url": "{{rewards_url}}", "unsubscribe": False, "reason": "reason_account",
        },
        "premium_on": {
            "subject": "Ton Premium est activé jusqu'au {{until}}",
            "preheader": "Ton cadeau ({{gift}}) est activé sur ton compte.",
            "kicker": "Premium activé", "title": "C'est parti, {{name}} : ton Premium est actif !",
            "body": [
                "Ton cadeau, <b>{{gift}}</b>, vient d'être ajouté à ton compte.",
                _table([("Offre", "{{gift}}"), ("Premium actif jusqu'au", "{{until}}")]),
                "Profite de l'analyse de tous les matchs, des 5 paris de chaque niveau et des coupons du jour, sans pub. Rien ne sera prélevé à la fin.",
            ],
            "cta": "Voir les matchs du jour", "cta_url": "{{home_url}}", "unsubscribe": False, "reason": "reason_account",
        },
    },
    "en": {
        "responsible": "18+ · Probabilities are not certainties. Never stake more than you can afford to lose.",
        "manage": "Manage my emails", "unsub": "Unsubscribe",
        "reason_account": "You're receiving this email because you have a Probalis account.",
        "reason_news": "You're receiving this email because you turned on big-match alerts.",
        "reason_reminders": "You're receiving this email because you turned on the Premium reminder.",
        "welcome": {
            "subject": "Welcome to Probalis, {{name}}",
            "preheader": "The real probability of every bet, no magic promises.",
            "kicker": "Welcome", "title": "Great to have you on board, {{name}}!",
            "body": [
                "Probalis works out the real chance of every bet from market odds and our statistical models. No \"sure bets\", no \"golden tips\": just honest numbers so you can decide with full knowledge.",
                "<b>Getting started:</b><br>• Every day you get 1 free full analysis: open the match of your choice and unlock it.<br>• Use \"Check your odds\": enter your bookmaker's price and we tell you if it's a good one.<br>• Turn on big-match alerts in <a href=\"{{account_url}}\" style=\"color:#15803D;font-weight:700;\">My account</a>: an email the day before the biggest matches.",
                "Invite your friends with your link: every friend who signs up earns you <b>free analyses</b> to use on the matches you choose. You'll find it in <a href=\"{{rewards_url}}\" style=\"color:#15803D;font-weight:700;\">Rewards</a>.",
                "Want more? <a href=\"{{premium_url}}\" style=\"color:#15803D;font-weight:700;\">Premium</a> unlocks the analysis of every match, ad-free, with a pass from 7 days to 1 year and no subscription.",
            ],
            "cta": "See today's matches", "cta_url": "{{home_url}}", "unsubscribe": False, "reason": "reason_account",
        },
        "receipt": {
            "subject": "Your Probalis Premium receipt · {{plan}}",
            "preheader": "Thank you! Your Premium is active until {{until}}.",
            "kicker": "Payment confirmed", "title": "Thanks {{name}}, your Premium is active!",
            "body": [
                "Here is the receipt for your purchase. Keep it in case you have a question.",
                _table([("Plan", "{{plan}}"), ("Amount", "{{amount}}"), ("Payment method", "{{provider}}"),
                        ("Date", "{{date}}"), ("Reference", "{{ref}}"), ("Premium active until", "{{until}}")]),
                "One-off payment, <b>no subscription</b>: nothing will be charged automatically when your pass ends.",
            ],
            "cta": "Enjoy Premium", "cta_url": "{{home_url}}", "unsubscribe": False, "reason": "reason_account",
        },
        "expiry": {
            "subject": "Your Premium ends on {{until}}",
            "preheader": "Extend it in one tap if you want to keep every match's analysis.",
            "kicker": "Reminder", "title": "Your Premium ends soon",
            "body": [
                "Hi {{name}}, your Premium pass ends on <b>{{until}}</b>.",
                "After that you're automatically back on the free plan (1 full analysis a day, with a few ads). Nothing is charged without your consent.",
                "To keep the analysis of every match, ad-free, get a new pass: it will be added after the current one.",
            ],
            "cta": "Extend my Premium", "cta_url": "{{premium_url}}", "unsubscribe": True, "reason": "reason_reminders",
        },
        "big_match": {
            "subject": "Tomorrow: {{home}} – {{away}}, our probabilities",
            "preheader": "{{league}} · {{kickoff}} · {{home}} {{p1}}, draw {{px}}, {{away}} {{p2}}",
            "kicker": "Big match tomorrow", "title": "{{home}} – {{away}}",
            "body": [
                _match_card("Draw"),
                "Over 2.5 goals: <b>{{over25}}</b> · Both teams to score: <b>{{btts}}</b>",
                "{{{others_html}}}",
            ],
            "text": ["{{league}} · {{kickoff}}", "{{home}} {{p1}} · Draw {{px}} · {{away}} {{p2}}",
                     "Over 2.5 goals: {{over25}} · Both teams to score: {{btts}}"],
            "cta": "See the full analysis", "cta_url": "{{match_url}}", "unsubscribe": True, "reason": "reason_news",
        },
        "gift": {
            "subject": "{{name}}, a gift is waiting for you on Probalis: {{gift}}",
            "preheader": "Tap “Activate the reward” to get it on your account.",
            "kicker": "Gift", "title": "A gift for you, {{name}}!",
            "body": [
                "The Probalis team is giving you a gift: <b>{{gift}}</b>.",
                "{{{note_html}}}",
                "Tap the button below to activate your reward. It will appear in the <b>Rewards</b> tab of your account: use it whenever you like.",
                "This link is valid until {{expires}}. If you're not signed in, Probalis will first ask you to sign in with the Google account that receives this email.",
            ],
            "text": ["The Probalis team is giving you a gift: {{gift}}.", "{{note}}",
                     "Activate your reward with this link (valid until {{expires}}): it will appear in the Rewards tab of your account."],
            "cta": "Activate the reward", "cta_url": "{{claim_url}}", "unsubscribe": False, "reason": "reason_account",
        },
        "reward": {
            "subject": "+{{amount}} free analyses on Probalis",
            "preheader": "{{why}}",
            "kicker": "Referral", "title": "Well done {{name}}: +{{amount}} free analyses",
            "body": [
                "{{why}}",
                "Your <b>{{amount}} free analyses</b> are waiting in the Rewards tab of your account. Activate them, then use them on the matches you choose: each free analysis opens the full analysis of one match.",
                "Keep inviting with your link: <a href=\"{{invite_url}}\" style=\"color:#15803D;font-weight:700;\">{{invite_url}}</a>",
            ],
            "cta": "See my rewards", "cta_url": "{{rewards_url}}", "unsubscribe": False, "reason": "reason_account",
        },
        "premium_on": {
            "subject": "Your Premium is on until {{until}}",
            "preheader": "Your gift ({{gift}}) is now on your account.",
            "kicker": "Premium on", "title": "Here we go, {{name}}: your Premium is active!",
            "body": [
                "Your gift, <b>{{gift}}</b>, has just been added to your account.",
                _table([("Plan", "{{gift}}"), ("Premium active until", "{{until}}")]),
                "Enjoy the analysis of every match, all 5 bets of each level and today's accumulators, ad-free. Nothing will be charged at the end.",
            ],
            "cta": "See today's matches", "cta_url": "{{home_url}}", "unsubscribe": False, "reason": "reason_account",
        },
    },
}

# Libellés utilisés par les e-mails de la tâche quotidienne
OTHERS_TITLE = {"fr": "Les autres belles affiches de demain", "en": "Tomorrow's other big matches"}


def _env() -> Environment:
    return Environment(loader=FileSystemLoader(HERE), autoescape=False, variable_start_string="[[",
                       variable_end_string="]]", block_start_string="[%", block_end_string="%]",
                       trim_blocks=True, lstrip_blocks=True)


def _text(s: str) -> str:
    s = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>',
               lambda m: m.group(2) if m.group(2) == m.group(1) else f"{m.group(2)} ({m.group(1)})", s)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</tr>", "\n", s)
    s = re.sub(r"</div>", " ", s)
    s = re.sub(r"</td><td[^>]*>", " : ", s)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(re.sub(r"[ \t]+", " ", s)).strip()


def build_templates() -> dict:
    """{kind: {lang: {subject, html, text}}}, avec les {{variables}} à remplir au moment de l'envoi."""
    layout = _env().get_template("layout.html")
    out: dict = {}
    for kind in KINDS:
        out[kind] = {}
        for lang in LANGS:
            t = TEXTS[lang]
            e = t[kind]
            body = "".join(p if p.startswith(("<table", "{{{")) else f"<p {_P}>{p}</p>" for p in e["body"])
            page = layout.render(lang=lang, subject=e["subject"], preheader=e["preheader"], kicker=e["kicker"],
                                 title=e["title"], body=body, cta=e["cta"], cta_url=e["cta_url"],
                                 responsible=t["responsible"], reason=t[e["reason"]], manage=t["manage"],
                                 unsub=t["unsub"], unsubscribe=e["unsubscribe"])
            sep = " : " if lang == "fr" else ": "
            body_text = e.get("text") or [_text(p) for p in e["body"] if not p.startswith("{{{")]
            parts = [e["title"], *body_text]
            if kind == "big_match":
                parts.append("{{{others_text}}}")
            parts += [f"{e['cta']}{sep}{e['cta_url']}", "—", t["responsible"], t[e["reason"]],
                      f"{t['manage']}{sep}{{{{account_url}}}}"]
            if e["unsubscribe"]:
                parts.append(f"{t['unsub']}{sep}{{{{unsubscribe_url}}}}")
            out[kind][lang] = {"subject": e["subject"], "html": page, "text": "\n\n".join(parts),
                               "unsubscribe": e["unsubscribe"]}
    return out


_VAR = re.compile(r"\{\{\{(\w+)\}\}\}|\{\{(\w+)\}\}")


def fill(tpl: str, values: dict, as_html: bool = True) -> str:
    """Remplit un modèle. {{x}} est protégé (HTML), {{{x}}} est inséré tel quel (HTML préparé par notre code)."""
    def rep(m: re.Match) -> str:
        raw, key = m.group(1), m.group(2)
        if raw:
            return str(values.get(raw, ""))
        v = str(values.get(key, ""))
        return html.escape(v, quote=True) if as_html else v
    out = _VAR.sub(rep, tpl)
    return out if as_html else re.sub(r"\n{3,}", "\n\n", out)


def unsubscribe_token(user_id: str, kind: str, secret: str) -> str:
    return hmac.new(secret.encode(), f"{user_id}:{kind}".encode(), hashlib.sha256).hexdigest()[:32]


SAMPLES = {
    "fr": {"name": "Awa", "plan": "Pass 30 jours", "amount": "3 000 FCFA", "provider": "Mobile money (Flutterwave)",
           "date": "19 novembre 2026", "ref": "PB-4F2A9C", "until": "19 décembre 2026",
           "home": "Arsenal", "away": "Borussia Dortmund", "league": "Ligue des champions", "kickoff": "mardi 24 nov. à 21:00",
           "p1": "56 %", "px": "23 %", "p2": "21 %", "over25": "58 %", "btts": "55 %",
           "gift": "Pass Premium 30 jours", "expires": "20 décembre 2026", "claim_url": "#", "amount": "3",
           "note": "Merci de faire partie des premiers membres !",
           "why": "Ton ami Paul a utilisé Probalis 3 jours différents.", "invite_url": "https://probalis.pages.dev/i/K7M2QX"},
    "en": {"name": "Awa", "plan": "30-day pass", "amount": "€7.99", "provider": "Card (Stripe)",
           "date": "19 November 2026", "ref": "PB-4F2A9C", "until": "19 December 2026",
           "home": "Arsenal", "away": "Borussia Dortmund", "league": "Champions League", "kickoff": "Tue 24 Nov, 21:00",
           "p1": "56%", "px": "23%", "p2": "21%", "over25": "58%", "btts": "55%",
           "gift": "30-day Premium pass", "expires": "20 December 2026", "claim_url": "#", "amount": "3",
           "note": "Thanks for being one of our first members!",
           "why": "Your friend Paul has used Probalis on 3 different days.", "invite_url": "https://probalis.pages.dev/i/K7M2QX"},
}


def links(site: str, lang: str) -> dict:
    """Liens communs à tous les e-mails."""
    return {"site_url": site, "home_url": f"{site}/{lang}/", "account_url": f"{site}/{lang}/compte.html",
            "premium_url": f"{site}/{lang}/premium.html", "responsible_url": f"{site}/{lang}/jeu-responsable.html",
            "rewards_url": f"{site}/{lang}/recompenses.html"}


def generate() -> None:
    tpls = build_templates()
    SHARED.mkdir(parents=True, exist_ok=True)
    (SHARED / "emails.json").write_text(json.dumps(tpls, ensure_ascii=False, indent=1), encoding="utf-8")
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    # Aperçus : liens vers le site construit dans public/ ; le grand choc vient des vraies données si elles existent
    site = "../../public"
    from . import daily
    data = daily.local_data()
    items = []
    for kind in KINDS:
        for lang in LANGS:
            v = {**SAMPLES[lang], **links(site, lang), "unsubscribe_url": "#",
                 "home_logo": f"{site}/icons/icone-192.png", "away_logo": f"{site}/icons/icone-192.png",
                 "others_html": others_html([("Real Madrid – Liverpool", "Ligue des champions" if lang == "fr"
                                              else "Champions League", "21:00")], lang),
                 "note_html": note_html(SAMPLES[lang]["note"])}
            if kind == "big_match" and data:
                picks = daily.big_matches(data, None)
                if picks:
                    v.update(daily.match_values(picks[0], picks[1:4], lang, site))
            name = f"{kind}_{lang}.html"
            (PREVIEWS / name).write_text(fill(tpls[kind][lang]["html"], v), encoding="utf-8")
            (PREVIEWS / f"{kind}_{lang}.txt").write_text(fill(tpls[kind][lang]["text"], v, False), encoding="utf-8")
            items.append(f'<li><a href="{name}">{kind} · {lang}</a> — {html.escape(fill(tpls[kind][lang]["subject"], v, False))}</li>')
    (PREVIEWS / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Aperçu des e-mails Probalis</title>'
        '<body style="font-family:system-ui,sans-serif;padding:24px;line-height:1.7"><h1>Aperçu des e-mails Probalis</h1>'
        '<p>Exemples remplis avec de fausses valeurs (le « grand choc » utilise les vrais matchs de public/data '
        f'quand ils existent). Une version texte .txt accompagne chaque e-mail.</p><ul>{"".join(items)}</ul></body>',
        encoding="utf-8")
    print(f"Modèles écrits dans {SHARED / 'emails.json'}")
    print(f"Aperçus dans {PREVIEWS / 'index.html'}")


def others_html(items: list[tuple[str, str, str]], lang: str) -> str:
    """Petite liste « autres affiches de demain » (texte protégé ici, inséré tel quel dans le modèle)."""
    if not items:
        return ""
    lis = "".join(f'<li style="margin:0 0 6px;"><b>{html.escape(m)}</b> · {html.escape(lg)} · {html.escape(ko)}</li>'
                  for m, lg, ko in items)
    return (f'<p style="margin:18px 0 6px;font-weight:700;">{OTHERS_TITLE[lang]}</p>'
            f'<ul style="margin:0;padding-left:18px;color:#5B6B82;font-size:14px;">{lis}</ul>')


def note_html(note: str | None) -> str:
    """Petit mot de l'admin dans l'e-mail cadeau (texte protégé ici, inséré tel quel dans le modèle)."""
    note = (note or "").strip()
    if not note:
        return ""
    return ('<p style="margin:0 0 14px;padding:12px 14px;background:#F0FDF4;border-left:3px solid #22C55E;'
            f'border-radius:8px;font-style:italic;">« {html.escape(note)} »</p>')
