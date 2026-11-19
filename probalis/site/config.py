"""Réglages publics du site : comptes (Supabase), prix Premium, contact.

Tout vient de variables d'environnement (secrets GitHub en production). Sans Supabase, le site tourne en
« mode démo » : la connexion et le Premium sont simulés sur le téléphone, rien n'est envoyé nulle part.

Variables lues au moment du build :
  PROBALIS_SITE_URL           adresse du site, ex. https://probalis.pages.dev (liens des e-mails)
  PROBALIS_SUPABASE_URL       ex. https://abcd1234.supabase.co
  PROBALIS_SUPABASE_ANON_KEY  clé publique « anon » ou « publishable » (faite pour être dans le site)
  PROBALIS_CONTACT_EMAIL      adresse de contact affichée dans les pages légales
  PROBALIS_OWNER_NAME         nom de l'éditeur du site (pages légales)

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

# Marchés gratuits : 1X2, plus / moins de buts, les deux équipes marquent. Tout le reste est Premium.
FREE_MARKETS = frozenset({"1x2", "ou", "btts"})


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
    }


def public_config() -> dict:
    """Ce que le téléphone reçoit (dans chaque page) : rien de secret."""
    s = site()
    return {
        "demo": s["demo"],
        "sb": {"url": s["supabase_url"], "key": s["supabase_key"], "lib": SUPABASE_JS, "sri": SUPABASE_JS_SRI}
        if not s["demo"] else None,
        "prices": prices(),
    }
