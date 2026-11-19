"""Commandes Probalis.

  python -m probalis build      Récupère les données, calcule les analyses et génère le site dans public/
  python -m probalis serve      Aperçu local du site sur http://localhost:8000
  python -m probalis backtest   Test de fiabilité sur une saison passée (voir probalis/football/backtest.py)
"""
from __future__ import annotations

import sys


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        from .football.pipeline import run
        from .site.build import build
        print("Analyse des prochains matchs…")
        data = run()
        rep = data["report"]
        if rep["unmatched"]:
            print("Équipes non reconnues :", *rep["unmatched"], sep="\n  ")
        if not data["matches"]:
            # Sources en panne : on ne remplace pas le site en ligne par un site vide.
            print("Aucun match analysé : site non généré.")
            sys.exit(1)
        out = build(data)
        print(f"{len(data['matches'])} matchs analysés. Site généré dans {out}")
    elif cmd == "serve":
        import functools
        import http.server
        from .site.build import PUBLIC
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(PUBLIC))
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        print(f"Aperçu : http://localhost:{port}")
        http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
    elif cmd == "backtest":
        from .football import backtest
        sys.argv = [sys.argv[0], *sys.argv[2:]]
        backtest.main()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
