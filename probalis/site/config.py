"""Réglages publics du site : comptes (Supabase), prix Premium, contact.

Tout vient de variables d'environnement (secrets GitHub en production). Sans Supabase, le site tourne en
« mode démo » : la connexion et le Premium sont simulés sur le téléphone, rien n'est envoyé nulle part.

Variables lues au moment du build :
  PROBALIS_SITE_URL           adresse du site, ex. https://probalis.pages.dev (liens des e-mails)
  PROBALIS_SUPABASE_URL       ex. https://abcd1234.supabase.co
  PROBALIS_SUPABASE_ANON_KEY  clé publique « anon » ou « publishable » (faite pour être dans le site)
  PROBALIS_CONTACT_EMAIL      adresse de contact affichée dans les pages légales
  PROBALIS_OWNER_NAME         nom de l'éditeur du site (pages légales)
  PROBALIS_PAYMENTS           « online » quand Stripe / Flutterwave sont branchés. Sinon (par défaut), le bouton
                              Premium ouvre WhatsApp avec un message prêt, et l'admin active le pass à la main.
  PROBALIS_WHATSAPP           numéro WhatsApp du bouton Premium, chiffres seulement (par défaut celui de Probalis)

Jamais de clé secrète ici : les clés Stripe, Flutterwave, Resend et la clé « service_role » de Supabase
restent dans les secrets des fonctions Supabase et de GitHub.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRICES_FILE = ROOT / "supabase" / "functions" / "_shared" / "prices.json"

# Version figée de la bibliothèque Supabase (chargée seulement sur les pages qui en ont besoin)
SUPABASE_JS = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.js"
SUPABASE_JS_SRI = "sha384-0w2KAL2YHP6wKOkUDzkCDGgVvfmHnj02DHeQ6XcHOgTfFsGyonKOpShMH1x6nk9o"

# Gratuit : 1 analyse complète par jour, sur le match choisi (compté sur le téléphone, voir static/app.js).
# Aucun marché n'est ouvert sur tous les matchs : chaque page de match reste verrouillée jusqu'à ce choix.
FREE_MARKETS: frozenset[str] = frozenset()

# Barème du parrainage par défaut (le vrai est dans la base, table settings, réglable dans l'admin) : analyses
# offertes au parrain à chaque étape de son ami, et bonus de bienvenue de l'ami. Mêmes valeurs que la migration.
REFERRAL_DEFAULTS = {"signup": 2, "active": 3, "active_days": 3, "welcome": 2, "monthly_cap": 10,
                     "purchase": {"week": 4, "month": 5, "quarter": 6, "half": 8, "year": 10}}


def referral_view() -> dict:
    r = REFERRAL_DEFAULTS
    return {**{k: v for k, v in r.items() if k != "purchase"},
            "buy_min": min(r["purchase"].values()), "buy_max": max(r["purchase"].values())}


# Numéro public de Probalis pour payer Premium tant que le paiement en ligne n'est pas branché
WHATSAPP_DEFAULT = "237670375810"


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


@lru_cache(maxsize=1)
def prices() -> dict:
    data = json.loads(PRICES_FILE.read_text(encoding="utf-8"))
    data.pop("_note", None)
    return data


def site() -> dict:
    url = _env("PROBALIS_SUPABASE_URL").rstrip("/")
    key = _env("PROBALIS_SUPABASE_ANON_KEY")
    return {
        "site_url": _env("PROBALIS_SITE_URL").rstrip("/"),
        "supabase_url": url,
        "supabase_key": key,
        "demo": not (url and key),
        "contact_email": _env("PROBALIS_CONTACT_EMAIL"),
        "owner_name": _env("PROBALIS_OWNER_NAME"),
        "pay": "online" if _env("PROBALIS_PAYMENTS").lower() in ("online", "on", "1") else "whatsapp",
        "whatsapp": "".join(ch for ch in (_env("PROBALIS_WHATSAPP") or WHATSAPP_DEFAULT) if ch.isdigit()),
    }


def whatsapp_display(num: str) -> str:
    """« 237670375810 » → « +237 670375810 » (comme le numéro est écrit partout ailleurs)."""
    return f"+{num[:3]} {num[3:]}" if num.startswith("237") and len(num) == 12 else f"+{num}"


def public_config() -> dict:
    """Ce que le téléphone reçoit (dans chaque page) : rien de secret."""
    s = site()
    return {
        "demo": s["demo"],
        "sb": {"url": s["supabase_url"], "key": s["supabase_key"], "lib": SUPABASE_JS, "sri": SUPABASE_JS_SRI}
        if not s["demo"] else None,
        "prices": prices(),
        "pay": s["pay"],
        "wa": s["whatsapp"] if s["pay"] == "whatsapp" else None,
        "wa_n": whatsapp_display(s["whatsapp"]) if s["pay"] == "whatsapp" else None,
    }
