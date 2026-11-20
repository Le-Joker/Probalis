"""QR code en SVG, sans bibliothèque : mode octet, niveau de correction M, versions 1 à 6 (adresses courtes).

Sert au site vitrine : sur ordinateur, on scanne le code avec son téléphone pour ouvrir Probalis.
Fait d'après la norme ISO/IEC 18004 (même découpage que la bibliothèque de référence de Project Nayuki).
"""
from __future__ import annotations

# Niveau M : (codes de correction par bloc, nombre de blocs) pour les versions 1 à 6 ; tous les blocs ont la même taille.
_EC_M = {1: (10, 1), 2: (16, 1), 3: (26, 1), 4: (18, 2), 5: (24, 2), 6: (16, 4)}
_TOTAL = {1: 26, 2: 44, 3: 70, 4: 100, 5: 134, 6: 172}   # mots de code par version
_ALIGN = {1: None, 2: 18, 3: 22, 4: 26, 5: 30, 6: 34}    # centre du motif d'alignement (versions 2 à 6)
_FORMAT_M = 0  # bits du niveau M dans l'information de format


def _gf_mul(x: int, y: int) -> int:
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _rs_divisor(degree: int) -> list[int]:
    result = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(degree):
            result[j] = _gf_mul(result[j], root)
            if j + 1 < degree:
                result[j] ^= result[j + 1]
        root = _gf_mul(root, 0x02)
    return result


def rs_remainder(data: list[int], degree: int) -> list[int]:
    """Codes de correction Reed-Solomon d'un bloc."""
    divisor = _rs_divisor(degree)
    result = [0] * degree
    for b in data:
        factor = b ^ result.pop(0)
        result.append(0)
        for i, coef in enumerate(divisor):
            result[i] ^= _gf_mul(coef, factor)
    return result


def _codewords(text: str) -> tuple[int, list[int]]:
    data = text.encode("utf-8")
    for version in range(1, 7):
        ec, blocks = _EC_M[version]
        n_data = _TOTAL[version] - ec * blocks
        if 4 + 8 + 8 * len(data) <= n_data * 8:
            break
    else:
        raise ValueError("texte trop long pour ce petit générateur de QR code")
    bits: list[int] = []
    put = lambda val, n: bits.extend((val >> i) & 1 for i in reversed(range(n)))  # noqa: E731
    put(0b0100, 4)          # mode octet
    put(len(data), 8)       # longueur (versions 1 à 9)
    for b in data:
        put(b, 8)
    put(0, min(4, n_data * 8 - len(bits)))    # fin
    put(0, (-len(bits)) % 8)                  # compléter l'octet
    words = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad = 0xEC
    while len(words) < n_data:
        words.append(pad)
        pad ^= 0xEC ^ 0x11
    size = n_data // blocks
    data_blocks = [words[i * size:(i + 1) * size] for i in range(blocks)]
    ec_blocks = [rs_remainder(b, ec) for b in data_blocks]
    out = [b[i] for i in range(size) for b in data_blocks] + [b[i] for i in range(ec) for b in ec_blocks]
    return version, out


def _mask_bit(mask: int, x: int, y: int) -> bool:
    return [
        (x + y) % 2 == 0, y % 2 == 0, x % 3 == 0, (x + y) % 3 == 0,
        (x // 3 + y // 2) % 2 == 0, x * y % 2 + x * y % 3 == 0,
        (x * y % 2 + x * y % 3) % 2 == 0, ((x + y) % 2 + x * y % 3) % 2 == 0,
    ][mask]


class _Grid:
    def __init__(self, version: int):
        self.size = version * 4 + 17
        self.dark = [[False] * self.size for _ in range(self.size)]
        self.func = [[False] * self.size for _ in range(self.size)]
        n = self.size
        for i in range(n):  # lignes de synchronisation
            self.set(6, i, i % 2 == 0)
            self.set(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (n - 4, 3), (3, n - 4)):  # repères des coins
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < n and 0 <= y < n:
                        self.set(x, y, max(abs(dx), abs(dy)) not in (2, 4))
        a = _ALIGN[version]
        if a:
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    self.set(a + dx, a + dy, max(abs(dx), abs(dy)) != 1)
        self.format_bits(0)  # réserve la place de l'information de format

    def set(self, x: int, y: int, dark: bool) -> None:
        self.dark[y][x] = dark
        self.func[y][x] = True

    def format_bits(self, mask: int) -> None:
        data = _FORMAT_M << 3 | mask
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = (data << 10 | rem) ^ 0x5412
        bit = lambda i: (bits >> i) & 1 == 1  # noqa: E731
        n = self.size
        for i in range(6):
            self.set(8, i, bit(i))
        self.set(8, 7, bit(6))
        self.set(8, 8, bit(7))
        self.set(7, 8, bit(8))
        for i in range(9, 15):
            self.set(14 - i, 8, bit(i))
        for i in range(8):
            self.set(n - 1 - i, 8, bit(i))
        for i in range(8, 15):
            self.set(8, n - 15 + i, bit(i))
        self.set(8, n - 8, True)  # module toujours sombre

    def place(self, words: list[int]) -> None:
        n, i, total = self.size, 0, len(words) * 8
        right = n - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vert in range(n):
                for j in range(2):
                    x = right - j
                    upward = ((right + 1) & 2) == 0
                    y = n - 1 - vert if upward else vert
                    if not self.func[y][x] and i < total:
                        self.dark[y][x] = (words[i >> 3] >> (7 - (i & 7))) & 1 == 1
                        i += 1
            right -= 2

    def apply_mask(self, mask: int) -> None:
        for y in range(self.size):
            for x in range(self.size):
                if not self.func[y][x] and _mask_bit(mask, x, y):
                    self.dark[y][x] = not self.dark[y][x]

    def penalty(self) -> int:
        n, g, score = self.size, self.dark, 0
        lines = g + [[g[y][x] for y in range(n)] for x in range(n)]
        for line in lines:
            run, prev = 0, None
            for v in line:  # règle 1 : longues suites de même couleur
                run = run + 1 if v == prev else 1
                prev = v
                if run == 5:
                    score += 3
                elif run > 5:
                    score += 1
            s = "".join("1" if v else "0" for v in line)  # règle 3 : motifs qui ressemblent aux repères
            score += 40 * (s.count("10111010000") + s.count("00001011101"))
        for y in range(n - 1):  # règle 2 : carrés 2×2 d'une même couleur
            for x in range(n - 1):
                if g[y][x] == g[y][x + 1] == g[y + 1][x] == g[y + 1][x + 1]:
                    score += 3
        dark = sum(map(sum, g))  # règle 4 : équilibre clair / sombre
        score += 10 * (abs(dark * 20 - n * n * 10) // (n * n))
        return score


def matrix(text: str) -> list[list[bool]]:
    version, words = _codewords(text)
    best, best_score = None, None
    for mask in range(8):
        grid = _Grid(version)
        grid.place(words)
        grid.apply_mask(mask)
        grid.format_bits(mask)
        sc = grid.penalty()
        if best_score is None or sc < best_score:
            best, best_score = grid, sc
    return best.dark


def svg(text: str, label: str = "QR code", quiet: int = 4) -> str:
    m = matrix(text)
    n = len(m)
    path = "".join(f"M{x + quiet} {y + quiet}h1v1h-1z" for y in range(n) for x in range(n) if m[y][x])
    size = n + 2 * quiet
    return (f'<svg class="qr" viewBox="0 0 {size} {size}" role="img" aria-label="{label}" '
            f'shape-rendering="crispEdges" xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="{size}" height="{size}" fill="#fff"/><path d="{path}" fill="#0B1F3A"/></svg>')
