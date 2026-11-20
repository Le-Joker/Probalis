"""Chiffres protégés : la page publique ne contient qu'une forme vide sous cadenas.

Dans les modèles, un bloc protégé s'écrit :

    {% call lk(m=match_slug, free=False, hide=False) %} … vrai contenu … {% endcall %}

La page publique reçoit `<!--lk:N-->forme vide<!--/lk-->` : même structure (pour garder la place à l'écran), mais
sans aucun texte, chiffre, largeur, couleur ou attribut de données. Le vrai contenu est rangé à part
(fichiers JSON dans un dossier au nom secret, voir build._lk_dir) et n'est envoyé qu'aux comptes qui y ont droit,
après vérification côté serveur (Cloudflare Pages Function, functions/lk/[[path]].js, adresses /lk/…). L'appli
remet alors le vrai bloc à la place du cadenas.

- m : le match concerné (analyse gratuite du jour : un compte gratuit reçoit les blocs de ce match-là) ;
- free : bloc offert à tout compte connecté (le n° 1 de chaque liste de paris) ;
- hide : bouton à cacher (au lieu d'un cadenas) tant que le vrai bloc n'est pas là ;
- own : le modèle écrit lui-même sa forme vide (`{% if lk.pub %}…{% else %}…{% endif %}`), pour garder un texte fixe
  comme « Pari verrouillé » ;
- on : faux pour écrire le bloc tel quel (contenu déjà public, comme un pari réglé).
"""
from __future__ import annotations

from html import escape
from html.parser import HTMLParser

from markupsafe import Markup

# Attributs sans information gardés dans la forme vide (taille et structure seulement)
KEEP_ATTRS = {"id", "type", "hidden", "viewbox", "width", "height", "cx", "cy", "r", "fill", "stroke-width",
              "stroke-linecap", "stroke-linejoin", "transform", "xmlns"}
# Classes de structure gardées (tout le reste, comme fav, on, best, hi, mid, up…, disparaît)
KEEP_CLASSES = {
    "bar3", "big", "pcts", "boxes", "box", "mc-stats", "f-chips",
    "xg", "split", "scores", "score", "rows", "r", "r-l", "meter", "r-p", "pill", "tiles", "tile",
    "otable", "orow", "head", "lbl", "cmp-grid", "field",
    "ring", "trk", "val", "pk-fair", "pk-add", "js-only", "ic",
    "dc-legs", "dc-l", "dc-p", "dc-odds", "dc-load", "btn", "ghost",
}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
FILL = "—"


class _Scrub(HTMLParser):
    """Recopie la structure d'un bloc HTML en effaçant tout ce qui pourrait révéler un chiffre."""

    def __init__(self, mark: str):
        super().__init__(convert_charrefs=True)
        self.mark = mark
        self.out: list[str] = []
        self.depth = 0
        self.skip = 0          # contenu d'un <script> ou <style> : effacé

    def _open(self, tag: str, attrs, close: bool) -> None:
        kept = []
        cls = []
        for k, v in attrs:
            k = k.lower()
            if k == "class":
                cls = [c for c in (v or "").split() if c in KEEP_CLASSES]
            elif k in KEEP_ATTRS:
                kept.append((k, v))
        if self.depth == 0:
            cls.append(self.mark)
            kept.append(("aria-hidden", "true"))
        if cls:
            kept.insert(0, ("class", " ".join(cls)))
        a = "".join(f' {k}="{escape(v, quote=True)}"' if v is not None else f" {k}" for k, v in kept)
        self.out.append(f"<{tag}{a}{' /' if close else ''}>")

    def handle_starttag(self, tag, attrs):
        self._open(tag, attrs, False)
        if tag in ("script", "style"):
            self.skip += 1
        if tag not in VOID:
            self.depth += 1

    def handle_startendtag(self, tag, attrs):
        self._open(tag, attrs, True)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        self.depth = max(0, self.depth - 1)
        self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if self.skip:
            return
        # Les espaces restent (mise en page), tout texte devient un tiret
        self.out.append(data if not data.strip() else FILL)


def scrub(html: str, hide: bool = False) -> str:
    p = _Scrub("lkh" if hide else "lkd")
    p.feed(html)
    p.close()
    return "".join(p.out)


class Locker:
    """Collecte les blocs protégés de chaque page pendant la construction."""

    def __init__(self):
        self.pages: dict[str, dict[str, dict]] = {}
        self.page: str | None = None
        self.n = 0
        self.pub = False       # vrai pendant l'écriture de la forme vide d'un bloc « own »

    def start(self, page: str) -> None:
        """À appeler avant de construire une page (« index », « paris », « match/<slug> »…)."""
        self.page = page
        self.pages[page] = {}
        self.n = 0

    def __call__(self, m: str | None = None, free: bool = False, hide: bool = False, own: bool = False,
                 on: bool = True, caller=None) -> Markup:
        """own : le bloc écrit lui-même sa forme vide ({% if lk.pub %} … {% else %} … {% endif %}).
        on=False : rien à protéger (pari déjà réglé…), le bloc est écrit tel quel."""
        if not on:
            return caller()
        if self.page is None:
            raise RuntimeError("Locker.start() n'a pas été appelé pour cette page")
        self.pub = False
        real = str(caller())
        if own:
            self.pub = True
            try:
                fake = str(caller())
            finally:
                self.pub = False
        else:
            fake = scrub(real, hide)
        self.n += 1
        key = str(self.n)
        self.pages[self.page][key] = {"h": real, "m": m, "f": bool(free)}
        return Markup(f"<!--lk:{key}-->{fake}<!--/lk-->")

    # --- Fichiers à servir ---
    def all_of(self, page: str) -> dict[str, str]:
        return {k: b["h"] for k, b in self.pages.get(page, {}).items()}

    def free_of(self) -> dict[str, dict[str, str]]:
        out = {}
        for page, blocks in self.pages.items():
            got = {k: b["h"] for k, b in blocks.items() if b["f"]}
            if got:
                out[page] = got
        return out

    def by_match(self) -> dict[str, dict[str, dict[str, str]]]:
        out: dict[str, dict[str, dict[str, str]]] = {}
        for page, blocks in self.pages.items():
            for k, b in blocks.items():
                if b["m"]:
                    out.setdefault(b["m"], {}).setdefault(page, {})[k] = b["h"]
        return out
