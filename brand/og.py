"""Images de partage (WhatsApp, Facebook, X…) : 1200 × 630, sans aucun chiffre de match.

    python brand/og.py   →   brand/og/probalis-fr.png, probalis-en.png, invite-fr.png, invite-en.png

Le site les copie dans /og/ à chaque construction. Dessinées deux fois plus grandes puis réduites (bords nets).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "probalis" / "site" / "static" / "fonts"
OUT = HERE / "og"
S = 2                       # suréchantillonnage
W, H = 1200 * S, 630 * S

NIGHT = (11, 31, 58)
NIGHT_2 = (19, 42, 76)
WHITE = (255, 255, 255)
SOFT = (213, 222, 234)
MUTED = (167, 180, 200)
GREEN = (34, 197, 94)
GREEN_LT = (74, 222, 128)
GOLD = (250, 204, 21)
GOLD_INK = (66, 32, 6)

TEXT = {
    "fr": {
        "home": ("La vraie chance de chaque pari de foot.",
                 "Probabilités calculées à partir des cotes, paris du jour par niveau de risque, historique transparent."),
        "invite": ("Ton ami t’invite sur Probalis",
                   "Des analyses de match offertes à l’inscription. Gratuit, sans carte bancaire."),
        "chip": "18+ · Joue de façon responsable",
        "bar": "Exemple de lecture",
        "gift": "Cadeau",
    },
    "en": {
        "home": ("The real chance of every football bet.",
                 "Probabilities worked out from market odds, daily bets by risk level, a transparent track record."),
        "invite": ("Your friend invites you to Probalis",
                   "Free match analyses when you sign up. No card needed."),
        "chip": "18+ · Play responsibly",
        "bar": "How to read it",
        "gift": "Gift",
    },
}


def font(name: str, size: int, weight: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTS / f"{name}-latin.woff2"), size * S)
    f.set_variation_by_axes([weight])
    return f


def wrap(d: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        test = (cur + " " + word).strip()
        if d.textlength(test, font=f) <= width or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def mark(img: Image.Image, x: int, y: int, size: int) -> None:
    """L'icône de Probalis (brand/png/icone-512.png), réduite."""
    icon = Image.open(HERE / "png" / "icone-512.png").convert("RGBA").resize((size, size), Image.LANCZOS)
    img.paste(icon, (x, y), icon)


def base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), NIGHT)
    d = ImageDraw.Draw(img, "RGBA")
    # Anneaux verts (comme les cartes de l'appli)
    for (cx, cy, r, w, a) in ((1080, -40, 330, 54, 34), (1180, 600, 210, 34, 22)):
        d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), outline=GREEN + (a,), width=w * S)
    # Marque et nom
    mark(img, 72 * S, 64 * S, 76 * S)
    wf = font("sora", 40, 700)
    d.text((166 * S, 101 * S), "Proba", font=wf, fill=WHITE, anchor="lm")
    d.text((166 * S + d.textlength("Probalis", font=wf), 101 * S), "lis", font=wf, fill=GREEN_LT, anchor="rm")
    return img, d


def chip(d: ImageDraw.ImageDraw, text: str, x: int, y: int) -> None:
    f = font("jakarta", 22, 700)
    w = d.textlength(text, font=f) + 40 * S
    d.rounded_rectangle((x, y, x + w, y + 46 * S), radius=23 * S, fill=(255, 255, 255, 20))
    d.text((x + 20 * S, y + 23 * S), text, font=f, fill=SOFT, anchor="lm")


def headline(d: ImageDraw.ImageDraw, title: str, sub: str, width: int, top: int = 196) -> None:
    tf = font("sora", 62, 700)
    y = top * S
    for line in wrap(d, title, tf, width * S):
        d.text((72 * S, y), line, font=tf, fill=WHITE)
        y += 74 * S
    sf = font("jakarta", 28, 600)
    y += 18 * S
    for line in wrap(d, sub, sf, width * S):
        d.text((72 * S, y), line, font=sf, fill=SOFT)
        y += 40 * S


def bar_card(d: ImageDraw.ImageDraw, label: str) -> None:
    """Une carte de match stylisée : la barre 1 / X / 2, sans nom d'équipe ni pourcentage."""
    x0, y0, x1, y1 = 806 * S, 196 * S, 1128 * S, 430 * S
    d.rounded_rectangle((x0, y0, x1, y1), radius=28 * S, fill=NIGHT_2, outline=(42, 74, 120), width=2 * S)
    lf = font("jakarta", 19, 700)
    d.text((x0 + 26 * S, y0 + 34 * S), label, font=lf, fill=MUTED, anchor="lm")
    # Deux blasons ronds
    for cx in (x0 + 74 * S, x1 - 74 * S):
        d.ellipse((cx - 30 * S, y0 + 66 * S, cx + 30 * S, y0 + 126 * S), fill=(255, 255, 255, 34))
    d.text(((x0 + x1) // 2, y0 + 96 * S), "–", font=font("sora", 30, 700), fill=MUTED, anchor="mm")
    # Barre 1 / X / 2
    by = y0 + 158 * S
    parts = ((0.47, GREEN), (0.27, (125, 139, 161)), (0.26, (59, 82, 117)))
    x = x0 + 26 * S
    span = (x1 - x0) - 52 * S - 2 * 3 * S
    for i, (p, c) in enumerate(parts):
        w = span * p
        d.rounded_rectangle((x, by, x + w, by + 18 * S), radius=9 * S, fill=c)
        d.text((x + w / 2, by + 44 * S), "1X2"[i], font=font("sora", 20, 700), fill=SOFT, anchor="mm")
        x += w + 3 * S


def gift_card(d: ImageDraw.ImageDraw, label: str) -> None:
    x0, y0 = 860 * S, 196 * S
    size = 232 * S
    d.rounded_rectangle((x0, y0, x0 + size, y0 + size), radius=48 * S, fill=GOLD)
    # Paquet cadeau (traits épais, couleur foncée)
    ink = GOLD_INK
    k = size / 24
    ox, oy = x0, y0 + 6 * S
    lw = int(1.9 * k)
    d.rounded_rectangle((ox + 5 * k, oy + 10 * k, ox + 19 * k, oy + 19.5 * k), radius=int(1.5 * k), outline=ink, width=lw)
    d.rounded_rectangle((ox + 4 * k, oy + 7 * k, ox + 20 * k, oy + 10.5 * k), radius=int(1.2 * k), outline=ink, width=lw)
    d.line((ox + 12 * k, oy + 7 * k, ox + 12 * k, oy + 19.5 * k), fill=ink, width=lw)
    d.ellipse((ox + 7.6 * k, oy + 3.4 * k, ox + 12 * k, oy + 7 * k), outline=ink, width=lw)
    d.ellipse((ox + 12 * k, oy + 3.4 * k, ox + 16.4 * k, oy + 7 * k), outline=ink, width=lw)
    f = font("jakarta", 22, 800)
    d.text((x0 + size / 2, y0 + size + 34 * S), label, font=f, fill=GOLD, anchor="mm")


def save(img: Image.Image, name: str) -> None:
    OUT.mkdir(exist_ok=True)
    img.resize((1200, 630), Image.LANCZOS).save(OUT / name, optimize=True)


def main() -> None:
    for lang, t in TEXT.items():
        img, d = base()
        headline(d, *t["home"], width=680)
        bar_card(d, t["bar"])
        chip(d, t["chip"], 72 * S, 530 * S)
        save(img, f"probalis-{lang}.png")

        img, d = base()
        headline(d, *t["invite"], width=720)
        gift_card(d, t["gift"])
        chip(d, t["chip"], 72 * S, 530 * S)
        save(img, f"invite-{lang}.png")
    print("Images de partage :", ", ".join(sorted(p.name for p in OUT.glob("*.png"))))


if __name__ == "__main__":
    main()
