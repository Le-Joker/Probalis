"""python -m probalis.site.emails generate | daily [--dry-run] | test --to ADRESSE [--lang fr|en]"""
from __future__ import annotations

import argparse
import sys

from . import generate
from .daily import run, send_test


def main() -> int:
    ap = argparse.ArgumentParser(prog="python -m probalis.site.emails", description="E-mails Probalis (Resend)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("generate", help="écrit les modèles pour les fonctions Supabase et les aperçus (docs/emails/)")
    d = sub.add_parser("daily", help="envoie les alertes du jour (grand choc demain, fin du Premium)")
    d.add_argument("--dry-run", action="store_true", help="montre ce qui serait envoyé, sans rien envoyer")
    t = sub.add_parser("test", help="envoie les 4 modèles à une adresse pour vérifier Resend")
    t.add_argument("--to", required=True)
    t.add_argument("--lang", choices=("fr", "en"), default="fr")
    a = ap.parse_args()
    if a.cmd == "generate":
        generate()
        return 0
    if a.cmd == "daily":
        return run(a.dry_run)
    return send_test(a.to, a.lang)


if __name__ == "__main__":
    sys.exit(main())
