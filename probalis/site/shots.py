"""Captures d'écran de l'appli pour le site vitrine (outil de développement, pas utilisé par la construction).

Prend de vraies captures de l'appli avec Google Chrome (ou Edge) sans fenêtre, sur une version du site servie
en local, avec un compte Premium de démonstration pour que rien ne soit sous cadenas. Les images (JPEG, 600 et
360 px de large) vont dans probalis/site/static/shots/ et sont ensuite servies dans /assets/shots/.

Les captures étant publiques, elles ne montrent jamais les vrais chiffres d'un match à venir : le site photographié
est construit avec des données d'exemple (clubs inventés, analyses mélangées entre les matchs, pas d'historique).

Usage :
  1. python -m probalis.site.shots --prepare demo-public          (site d'exemple, construit depuis public/)
  2. le servir : python -m http.server 8766 --directory demo-public
  3. python -m probalis.site.shots --base http://127.0.0.1:8766 --public demo-public
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "static" / "shots"
BROWSERS = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
WIDTH, HEIGHT, SCALE = 390, 844, 2
OUT_WIDTHS = (600, 360)  # deux tailles : la petite pour les téléphones et les connexions lentes

# Petite page posée à côté du site, seulement pendant les captures : elle prépare le navigateur (compte Premium
# de démonstration, thème clair, coupon d'exemple, jour choisi), puis ouvre la page à photographier.
HELPER = """<!doctype html><meta charset="utf-8"><title>shot</title><script>
(async function () {
  var q = new URLSearchParams(location.search), lang = q.get('lang') || 'fr';
  var until = new Date(Date.now() + 30 * 864e5).toISOString();
  localStorage.setItem('pb-acct', JSON.stringify({ demo: true, t: Date.now(),
    user: { id: 'demo', email: 'demo@probalis.app', name: lang === 'fr' ? 'Démo' : 'Demo', avatar: null },
    profile: { premium_until: until, email_news: false, email_reminders: true, favorite_leagues: [], lang: lang,
      country: null, is_adult: true, welcome_sent_at: new Date().toISOString(), tz: null, free_day: null, free_match: null } }));
  localStorage.setItem('theme', q.get('theme') || 'light');
  localStorage.setItem('lang', lang);
  localStorage.removeItem('pb-coupon');
  if (q.get('coupon')) {
    // Les vrais blocs (coupons du jour) sont dans /lk/ : servis sans vérification par le serveur local de démo
    var blocks = (await (await fetch('/lk/' + lang + '/paris.json')).json()).b || {};
    var d = new DOMParser().parseFromString(Object.keys(blocks).map(function (k) { return blocks[k]; }).join(''), 'text/html');
    var btn = Array.prototype.find.call(d.querySelectorAll('button[data-legs]'), function (b) {
      try { var legs = JSON.parse(b.getAttribute('data-legs')); return legs.length >= 3 && legs.every(function (l) { return new Date(l.ko) > Date.now(); }); }
      catch (e) { return false; }
    });
    if (btn) localStorage.setItem('pb-coupon', btn.getAttribute('data-legs'));
  }
  if (q.get('day')) sessionStorage.setItem('pday', q.get('day'));
  if (q.get('tier')) sessionStorage.setItem('ptier', q.get('tier'));
  sessionStorage.setItem('tkmode', 'mine');
  location.replace(q.get('go'));
})();
</script>"""


# Clubs d'exemple pour les captures (noms inventés)
CLUBS = ("FC", "AS", "Sporting", "Racing", "Union", "Olympique", "Athletic", "Dynamo", "Stade", "Real")
TOWNS = ("Aubrecourt", "Valdemar", "Kestrelburg", "Montvert", "Lindahl", "Corvallé", "Brisemont", "Ardenvale",
         "Solmara", "Tavernay", "Quillon", "Marbeck", "Eskholm", "Pradelle", "Ostwyn", "Calvera", "Rocheval",
         "Zennor", "Belcastel", "Norvik", "Vasselin", "Haldor", "Mirabel", "Saint-Aurèle", "Kervallon", "Durnstein",
         "Albarra", "Fennwick", "Lorimont", "Castelmar")
PREDICTION = ("xg", "source", "model_1x2", "confidence", "top_score", "markets", "priced")


def demo_data(data: dict, seed: int = 20) -> dict:
    """Données d'exemple pour les captures publiques : chaque match garde son championnat et son horaire, mais
    ses équipes sont inventées et son analyse est celle d'un autre match, tiré au hasard. Aucun chiffre visible sur
    la vitrine ne peut donc être rattaché à un vrai match à venir."""
    rnd = random.Random(seed)
    d = copy.deepcopy(data)
    matches = d["matches"]
    analyses = [{k: m.get(k) for k in PREDICTION} for m in matches]
    rnd.shuffle(analyses)
    names = [f"{c} {t}" for t in TOWNS for c in CLUBS]
    rnd.shuffle(names)
    teams: dict[str, str] = {}

    def fake(team: dict) -> dict:
        key = team.get("fd") or team.get("name") or str(len(teams))
        if key not in teams:
            teams[key] = names[len(teams) % len(names)]
        return {"name": teams[key]}

    for m, a in zip(matches, analyses):
        m.update(a)
        m["home"], m["away"] = fake(m["home"]), fake(m["away"])
        m["venue"] = None
    return d


def prepare(src_public: Path, out: Path) -> None:
    """Construit dans `out` le site d'exemple à photographier (mode démo, aucun historique réel)."""
    for k in ("PROBALIS_SUPABASE_URL", "PROBALIS_SUPABASE_ANON_KEY"):
        os.environ.pop(k, None)
    from . import build, history
    src = build.full_data_file()
    if not src.exists():
        src = build.locked_dir(src_public) / "data" / "matches.json"
    data = json.loads(src.read_text(encoding="utf-8"))
    out = out.resolve()
    build.PUBLIC = out
    build.ROOT = out.parent / f"{out.name}-root"
    history.LOCAL = out.parent / f"{out.name}-history.json"
    history.LOCAL.unlink(missing_ok=True)
    history.load = lambda site_url: history._empty()
    build.build(demo_data(data))
    print(f"Site d'exemple prêt dans {out}")


def _browser() -> str:
    for b in BROWSERS:
        if Path(b).exists():
            return b
    raise SystemExit("Ni Edge ni Chrome trouvé.")


def _big_match(public: Path) -> dict:
    data = json.loads((public / "lk" / "data" / "matches.json").read_text(encoding="utf-8"))  # site d'exemple : lk/
    now = datetime.now(timezone.utc)
    soon = [m for m in data["matches"] if datetime.fromisoformat(m["kickoff"]) > now + timedelta(hours=2)
            and m["league"] in ("E0", "SP1", "I1", "D1", "F1", "UCL") and m.get("confidence") == "high"]
    soon.sort(key=lambda m: (-(m.get("stature") or 0), m["kickoff"]))
    if not soon:
        raise SystemExit("Aucun grand match à venir pour la capture.")
    return soon[0]


def _jpeg(src: Path, dst: Path, width: int) -> None:
    """Réduit la capture et l'enregistre en JPEG avec les outils de Windows (aucune bibliothèque à installer)."""
    script = (
        "Add-Type -AssemblyName System.Drawing;"
        "$s=[System.Drawing.Image]::FromFile($env:SHOT_IN);$w=[int]$env:SHOT_W;$h=[int]($s.Height*$w/$s.Width);"
        "$b=New-Object System.Drawing.Bitmap $w,$h;$g=[System.Drawing.Graphics]::FromImage($b);"
        "$g.InterpolationMode='HighQualityBicubic';$g.SmoothingMode='HighQuality';$g.PixelOffsetMode='HighQuality';"
        "$g.DrawImage($s,0,0,$w,$h);"
        "$c=[System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders()|Where-Object{$_.MimeType -eq 'image/jpeg'};"
        "$p=New-Object System.Drawing.Imaging.EncoderParameters 1;"
        "$p.Param[0]=New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality,[long]80);"
        "$b.Save($env:SHOT_OUT,$c,$p);$g.Dispose();$b.Dispose();$s.Dispose()")
    env = dict(os.environ, SHOT_IN=str(src), SHOT_OUT=str(dst), SHOT_W=str(width))
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], check=True, env=env)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8766")
    ap.add_argument("--public", default="public", help="dossier servi à l'adresse --base")
    ap.add_argument("--only", nargs="*", help="noms des captures à refaire (matches, match, bets, ticket, history)")
    ap.add_argument("--prepare", metavar="DOSSIER", help="construire d'abord le site d'exemple dans ce dossier")
    args = ap.parse_args()
    if args.prepare:
        prepare(Path(args.public), Path(args.prepare))
        return
    public = Path(args.public)
    big = _big_match(public)
    days = sorted({m["kickoff"][:10] for m in json.loads((public / "lk" / "data" / "matches.json").read_text(encoding="utf-8"))["matches"]})
    tomorrow = (datetime.now(timezone(timedelta(hours=1))) + timedelta(days=1)).date().isoformat()
    day = tomorrow if tomorrow in days else days[0]
    shots = {
        "matches": ("index.html", {}),
        "match": (f"match/{big['slug']}.html", {}),
        "bets": ("paris.html", {"day": day, "tier": "safe"}),
        "ticket": ("ticket.html", {"coupon": "1"}),
        "history": ("historique.html", {}),
    }
    helper = public / "__shot.html"
    helper.write_text(HELPER, encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="probalis-shots-"))
    try:
        for lang in ("fr", "en"):
            for name, (path, extra) in shots.items():
                if args.only and name not in args.only:
                    continue
                q = "&".join(f"{k}={v}" for k, v in {"lang": lang, **extra}.items())
                url = f"{args.base}/__shot.html?{q}&go=/{lang}/{path}"
                png = tmp / f"{lang}-{name}.png"
                profile = tmp / f"profile-{lang}-{name}"
                # Chrome est piloté par shots_cdp.mjs (Node) : seule façon fiable d'avoir un vrai écran de téléphone.
                subprocess.run(["node", str(HERE / "shots_cdp.mjs"), _browser(), str(profile), str(png), url,
                                str(WIDTH), str(HEIGHT), str(SCALE)], check=True, timeout=180)
                if not png.exists():
                    raise SystemExit(f"Le navigateur n'a pas écrit la capture {png.name}.")
                for width in OUT_WIDTHS:
                    dst = OUT / f"{lang}-{name}-{width}.jpg"
                    _jpeg(png, dst, width)
                    print(f"{dst.name} : {dst.stat().st_size // 1024} Ko ({path})")
    finally:
        helper.unlink(missing_ok=True)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
