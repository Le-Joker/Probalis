"""Dessine brand/png/badge-96.png : la marque Probalis en blanc sur fond transparent.

Android ne garde que la forme (le canal alpha) de ce petit badge dans la barre des notifications.
Lancer : python brand/badge.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

SIZE, SS = 96, 8  # dessin 8 fois plus grand, puis réduit (bords lisses)
S = 1.05 * SS     # échelle de la marque (repère 120 × 120)
OX, OY = -15 * SS, -15 * SS


def P(x: float, y: float) -> tuple[float, float]:
    return OX + x * S, OY + y * S


def main() -> Path:
    big = SIZE * SS
    img = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(img)
    w = 12 * S
    # Boucle du P : traits droits, demi-cercle, bouts arrondis
    cx, cy = P(59.5, 50)
    r_out, r_in = (24 + 6) * S, (24 - 6) * S
    d.pieslice([cx - r_out, cy - r_out, cx + r_out, cy + r_out], -90, 90, fill=255)
    d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=0)
    d.line([P(37.5, 26), P(59.5, 26)], fill=255, width=round(w))
    d.line([P(37.5, 74), P(59.5, 74)], fill=255, width=round(w))
    for x, y in ((37.5, 26), (59.5, 26), (37.5, 74), (59.5, 74)):
        px, py = P(x, y)
        d.ellipse([px - w / 2, py - w / 2, px + w / 2, py + w / 2], fill=255)
    # Jambe du P
    x0, y0 = P(30.5, 20)
    x1, y1 = P(44.5, 100)
    d.rounded_rectangle([x0, y0, x1, y1], radius=7 * S, fill=255)
    alpha = img.resize((SIZE, SIZE), Image.LANCZOS)
    out = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 0))
    out.putalpha(alpha)
    path = Path(__file__).parent / "png" / "badge-96.png"
    out.save(path, optimize=True)
    return path


if __name__ == "__main__":
    print(main())
