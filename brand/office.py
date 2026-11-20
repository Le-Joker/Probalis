"""Dessine les icônes de Probalis Office (l'appli de l'administrateur) dans brand/png/office-*.png.

Même marque que Probalis, mais la boucle du P est dorée au lieu de verte :
sur l'écran d'accueil, on ne confond pas les deux applis.
Lancer : python brand/office.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
OUT = HERE / "png"
SS = 8  # dessin 8 fois plus grand, puis réduit (bords lisses)

NAVY = (11, 31, 58, 255)
GOLD = (250, 204, 21, 255)
TRACK = (255, 255, 255, 46)
WHITE = (255, 255, 255, 255)


def mark(size: int, *, scale: float, rounded: bool) -> Image.Image:
    """La marque sur fond nuit. scale : part du carré occupée par le repère 120 × 120 de la marque."""
    big = size * SS
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if rounded:
        d.rounded_rectangle([0, 0, big - 1, big - 1], radius=round(26 / 120 * big), fill=NAVY)
    else:
        d.rectangle([0, 0, big, big], fill=NAVY)
    u = big * scale / 120             # une unité du repère
    o = (big - 120 * u) / 2           # marge pour centrer

    def P(x: float, y: float) -> tuple[float, float]:
        return o + x * u, o + y * u

    def stroke(layer: Image.Image, color, upto_deg: float, straight_end: bool) -> None:
        """Boucle du P : trait du haut, demi-cercle jusqu'à upto_deg, (trait du bas), bouts ronds."""
        dd = ImageDraw.Draw(layer)
        w = 12 * u
        cx, cy = P(59.5, 50)
        r_out, r_in = 30 * u, 18 * u
        dd.pieslice([cx - r_out, cy - r_out, cx + r_out, cy + r_out], -90, upto_deg, fill=color)
        dd.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=(0, 0, 0, 0))
        dd.line([P(37.5, 26), P(59.5, 26)], fill=color, width=round(w))
        caps = [(37.5, 26)]
        if straight_end:
            dd.line([P(37.5, 74), P(59.5, 74)], fill=color, width=round(w))
            caps.append((37.5, 74))
        else:
            a = math.radians(upto_deg)
            caps.append(((59.5 * u + 24 * u * math.cos(a)) / u, (50 * u + 24 * u * math.sin(a)) / u))
        for x, y in caps:
            px, py = P(x, y)
            dd.ellipse([px - w / 2, py - w / 2, px + w / 2, py + w / 2], fill=color)

    track = Image.new("RGBA", img.size, (0, 0, 0, 0))
    stroke(track, TRACK, 90, True)
    img.alpha_composite(track)
    gold = Image.new("RGBA", img.size, (0, 0, 0, 0))
    stroke(gold, GOLD, 57, False)   # même longueur dorée que le vert de l'icône Probalis
    img.alpha_composite(gold)
    x0, y0 = P(30.5, 20)
    x1, y1 = P(44.5, 100)
    d.rounded_rectangle([x0, y0, x1, y1], radius=7 * u, fill=WHITE)
    return img.resize((size, size), Image.LANCZOS)


def main() -> list[Path]:
    files = {
        "office-512.png": mark(512, scale=1.0, rounded=True),
        "office-192.png": mark(192, scale=1.0, rounded=True),
        "office-maskable-512.png": mark(512, scale=0.8, rounded=False),   # zone sûre de 80 %
        "office-apple-180.png": mark(180, scale=0.92, rounded=False),     # iPhone arrondit lui-même
        "office-32.png": mark(32, scale=1.0, rounded=True),
    }
    out = []
    for name, im in files.items():
        p = OUT / name
        im.save(p, optimize=True)
        out.append(p)
    return out


if __name__ == "__main__":
    for p in main():
        print(p.relative_to(HERE.parent))
