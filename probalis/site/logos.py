"""Logos des équipes et des championnats, servis par notre site (/logos/…) au lieu du serveur de TheSportsDB.

Le serveur de TheSportsDB est lent : sur téléphone, beaucoup de logos restaient vides. À la construction, chaque logo
est donc téléchargé une seule fois (version 200 px), réduit en 64 et 128 px (WebP, transparence gardée), rangé dans
data/cache/logos/ (gardé d'une construction à l'autre), puis copié dans public/logos/. Le nom du fichier vient de
son contenu : il ne change jamais, le téléphone peut le garder longtemps.

Un logo presque tout blanc (illisible sur fond clair, comme ceux de l'Eredivisie ou de la Liga Portugal) est repéré
tout seul : il s'affiche sur une pastille bleu nuit. logo_overrides.json remplace un logo faux ou ancien
(« league:CODE » ou « team:Nom TheSportsDB » -> adresse d'une image). Logo introuvable : on garde les initiales,
et c'est signalé dans le rapport de construction.
"""
from __future__ import annotations

import hashlib
import io
import json
import shutil
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

from ..football.data import CACHE, USER_AGENT

DIR = CACHE / "logos"
INDEX = DIR / "index.json"
OVERRIDES = Path(__file__).with_name("logo_overrides.json")
SIZES = {"tiny": 64, "small": 128}
RETRY_AFTER = 24 * 3600      # un logo qui n'a pas pu être téléchargé : nouvel essai le lendemain
LIGHT_SHARE = 0.62           # part de pixels clairs au-delà de laquelle un logo est « blanc »
VERSION = 1


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read()


def light_share(img: Image.Image) -> float:
    """Part des pixels visibles qui sont clairs et peu colorés (0 à 1). 0 pour une image sans transparence :
    elle a son propre fond, elle reste lisible partout."""
    im = img.convert("RGBA")
    im.thumbnail((64, 64))
    px = list(im.getdata())
    if not any(a < 40 for *_, a in px):
        return 0.0
    vis = [(r, g, b) for r, g, b, a in px if a >= 128]
    if not vis:
        return 0.0
    light = sum(1 for r, g, b in vis if min(r, g, b) >= 205 and max(r, g, b) - min(r, g, b) <= 40)
    return light / len(vis)


class Logos:
    """Index des logos déjà préparés : adresse source -> {"f": nom de fichier, "light": blanc ?}."""

    def __init__(self):
        self.index: dict[str, dict] = {}
        try:
            data = json.loads(INDEX.read_text(encoding="utf-8"))
            if data.get("version") == VERSION:
                self.index = data.get("logos") or {}
        except (OSError, ValueError):
            pass
        try:
            self.overrides: dict[str, str] = json.loads(OVERRIDES.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.overrides = {}
        self.used: set[str] = set()
        self.missing: set[str] = set()

    # --- Adresse source d'un logo (avec la table de remplacement) ---
    def team_url(self, name: str, badge: str | None) -> str | None:
        return self.overrides.get(f"team:{name}") or badge

    def league_url(self, code: str, badge: str | None) -> str | None:
        return self.overrides.get(f"league:{code}") or badge

    # --- Préparation ---
    def _make(self, url: str) -> dict:
        src = f"{url}/small" if "thesportsdb.com" in url else url
        try:
            raw = _fetch(src)
            img = Image.open(io.BytesIO(raw))
            img.load()
        except Exception:
            try:  # certaines images n'ont pas de version réduite
                raw = _fetch(url)
                img = Image.open(io.BytesIO(raw))
                img.load()
            except Exception:
                return {"err": int(time.time())}
        img = img.convert("RGBA")
        bbox = img.getchannel("A").getbbox()
        if bbox:
            img = img.crop(bbox)
        name = hashlib.sha1(raw).hexdigest()[:14]
        DIR.mkdir(parents=True, exist_ok=True)
        for px in SIZES.values():
            im = img.copy()
            im.thumbnail((px, px), Image.LANCZOS)
            canvas = Image.new("RGBA", (px, px), (0, 0, 0, 0))
            canvas.paste(im, ((px - im.width) // 2, (px - im.height) // 2))
            canvas.save(DIR / f"{name}-{px}.webp", "WEBP", quality=88, method=6)
        return {"f": name, "light": round(light_share(img), 3)}

    def _ready(self, url: str) -> bool:
        e = self.index.get(url) or {}
        if e.get("f"):
            return all((DIR / f"{e['f']}-{px}.webp").exists() for px in SIZES.values())
        return bool(e.get("err") and time.time() - e["err"] < RETRY_AFTER)

    def prepare(self, urls, jobs: int = 8) -> int:
        """Télécharge et réduit les logos pas encore prêts. Renvoie le nombre de logos ajoutés."""
        todo = sorted({u for u in urls if u and not self._ready(u)})
        if not todo:
            return 0
        with ThreadPoolExecutor(max_workers=jobs) as ex:
            for url, res in zip(todo, ex.map(self._make, todo)):
                self.index[url] = res
        DIR.mkdir(parents=True, exist_ok=True)
        INDEX.write_text(json.dumps({"version": VERSION, "logos": self.index}, ensure_ascii=False), encoding="utf-8")
        return sum(1 for u in todo if self.index[u].get("f"))

    # --- Utilisation dans les pages ---
    def src(self, url: str | None, size: str) -> str | None:
        """Adresse à mettre dans la page : notre copie si elle existe, sinon l'image d'origine."""
        if not url:
            return None
        e = self.index.get(url) or {}
        if e.get("f"):
            self.used.add(e["f"])
            return f"/logos/{e['f']}-{SIZES[size]}.webp"
        self.missing.add(url)
        return f"{url}/{size}" if "thesportsdb.com" in url else url

    def light(self, url: str | None) -> bool:
        return bool(url and (self.index.get(url) or {}).get("light", 0) >= LIGHT_SHARE)

    def publish(self, public: Path) -> int:
        out = public / "logos"
        out.mkdir(parents=True, exist_ok=True)
        n = 0
        for name in sorted(self.used):
            for px in SIZES.values():
                f = DIR / f"{name}-{px}.webp"
                if f.exists():
                    shutil.copy2(f, out / f.name)
                    n += 1
        return n
