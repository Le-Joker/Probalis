"""Icônes SVG en ligne (trait, grille 24 px), utilisées dans les gabarits : {{ icon('ball') }}."""
from __future__ import annotations

from markupsafe import Markup

PATHS = {
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "moon": '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6 6 6M18 18l1.4 1.4M2.5 12h2M19.5 12h2'
           'M4.6 19.4 6 18M18 6l1.4-1.4"/>',
    "ball": '<circle cx="12" cy="12" r="9"/><path d="m12 7.5 3.8 2.8-1.4 4.4H9.6l-1.4-4.4Z"/>'
            '<path d="M12 7.5V3.2M15.8 10.3l4-1.3M14.4 14.7l2.5 3.5M9.6 14.7 7.1 18.2M8.2 10.3l-4-1.3"/>',
    "trend": '<path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/>',
    "ticket": '<path d="M3 9V6.5A1.5 1.5 0 0 1 4.5 5h15A1.5 1.5 0 0 1 21 6.5V9a3 3 0 0 0 0 6v2.5a1.5 1.5 0 0 1-1.5 1.5h-15'
              'A1.5 1.5 0 0 1 3 17.5V15a3 3 0 0 0 0-6Z"/><path d="M14.5 5v2.5M14.5 10.8v2.4M14.5 16.5V19"/>',
    "history": '<path d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1L3.5 8.5"/><path d="M3.5 3.5v5h5"/><path d="M12 7.5V12l3 2"/>',
    "grid": '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/>'
            '<rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/>',
    "calendar": '<rect x="3.5" y="5" width="17" height="15" rx="3"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    "sliders": '<path d="M4 7h8M16 7h4M4 17h4M12 17h8"/><circle cx="14" cy="7" r="2"/><circle cx="10" cy="17" r="2"/>',
    "chev-right": '<path d="m9 6 6 6-6 6"/>',
    "chev-down": '<path d="m6 9 6 6 6-6"/>',
    "arrow-right": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "arrow-left": '<path d="M19 12H5M11 18l-6-6 6-6"/>',
    "star": '<path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2L3 9.6l6.2-.9Z"/>',
    "shield": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6Z"/><path d="m9 12 2 2 4-4"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/>',
    "check": '<path d="m5 12 5 5 9-10"/>',
    "x": '<path d="M6 6l12 12M18 6 6 18"/>',
    "equal": '<path d="M6 9.5h12M6 14.5h12"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "share": '<path d="M12 3v12M7.5 7.5 12 3l4.5 4.5"/><path d="M5 13v5.5A2.5 2.5 0 0 0 7.5 21h9a2.5 2.5 0 0 0 2.5-2.5V13"/>',
    "trophy": '<path d="M8 4h8v5a4 4 0 0 1-8 0Z"/><path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8 20h8M10 17h4"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7.5V12l3 2"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4.5 20.5c1.2-3.6 4.1-5.5 7.5-5.5s6.3 1.9 7.5 5.5"/>',
    "lock": '<rect x="5" y="10.5" width="14" height="10" rx="2.5"/><path d="M8.5 10.5V7.5a3.5 3.5 0 0 1 7 0v3"/>',
    "crown": '<path d="m3.5 8 4.2 3.6L12 5l4.3 6.6L20.5 8l-1.8 10.5H5.3Z"/><path d="M5.5 21h13"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="m4 7.5 8 6 8-6"/>',
    "bell": '<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 2h-15Z"/><path d="M10 21h4"/>',
    "logout": '<path d="M14 4h4.5A1.5 1.5 0 0 1 20 5.5v13a1.5 1.5 0 0 1-1.5 1.5H14"/><path d="M10 16.5 5.5 12 10 7.5M5.5 12H15"/>',
    "trash": '<path d="M4.5 7h15M9.5 7V4.5h5V7M6.5 7l1 13h9l1-13"/><path d="M10 11v5.5M14 11v5.5"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.6 3.8 5.6 3.8 9s-1.2 6.4-3.8 9c-2.6-2.6-3.8-5.6-3.8-9S9.4 5.6 12 3Z"/>',
    "heart": '<path d="M12 20s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.2a4.3 4.3 0 0 1 7.5 2.6C19.5 15.4 12 20 12 20Z"/>',
    "wifi-off": '<path d="M3 3l18 18"/><path d="M8.5 16.5a5 5 0 0 1 7 0M5 12.5a10 10 0 0 1 4-2.4M19 12.5a10 10 0 0 0-2.3-1.7'
                'M2 8.8a14.5 14.5 0 0 1 4.2-2.6M22 8.8a14.6 14.6 0 0 0-10-3.8"/><path d="M12 20h.01"/>',
    "signal": '<path d="M5 19v-3M10 19v-6M15 19V9M20 19V5"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 19.5c.8-3.3 3.4-5 6.5-5s5.7 1.7 6.5 5"/><path d="M15.5 4.8a3.5 3.5 0 0 1 0 6.4M17.5 14.7c2 .6 3.4 2.2 4 4.8"/>',
    "chat": '<path d="M3.5 20.5 4.9 16A8.5 8.5 0 1 1 8.2 19.2Z"/><path d="M9.2 8.6c-.4 0-.8.4-.8 1 0 2.6 2.9 5.4 5.6 5.4.6 0 1-.4 1-.9v-.8l-1.7-.8-.9.8c-1-.4-2.3-1.6-2.7-2.7l.8-.9-.7-1.6Z"/>',
    "dots": '<circle cx="12" cy="5" r=".9"/><circle cx="12" cy="12" r=".9"/><circle cx="12" cy="19" r=".9"/>',
    "refresh": '<path d="M20 11.5A8 8 0 0 0 6.3 6.3L4 8.5"/><path d="M4 4v4.5h4.5"/><path d="M4 12.5a8 8 0 0 0 13.7 5.2l2.3-2.2"/><path d="M20 20v-4.5h-4.5"/>',
    "card": '<rect x="2.5" y="5" width="19" height="14" rx="3"/><path d="M2.5 10h19M6.5 15h4"/>',
    "phone": '<rect x="6.5" y="2.5" width="11" height="19" rx="2.5"/><path d="M11 18.5h2"/>',
    "zap": '<path d="M13 2.5 4.5 13.5H12L11 21.5l8.5-11H12Z"/>',
    "gift": '<rect x="3.5" y="8" width="17" height="4" rx="1"/><path d="M5 12v8.5h14V12M12 8v12.5"/>'
            '<path d="M12 8H8.5a2.25 2.25 0 1 1 0-4.5C11 3.5 12 8 12 8Zm0 0h3.5a2.25 2.25 0 1 0 0-4.5C13 3.5 12 8 12 8Z"/>',
    "external": '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v4.5a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 4 18.5v-11A1.5 1.5 0 0 1 5.5 6H10"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "minus": '<path d="M5 12h14"/>',
    "target": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1"/>',
    "hash": '<path d="M9.5 4 7.5 20M16.5 4l-2 16M4.5 9h15.5M4 15h15.5"/>',
    "pen": '<path d="M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16Z"/><path d="m13.5 6.5 4 4"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "download": '<path d="M12 4v11M7 10.5l5 5 5-5"/><path d="M5 20h14"/>',
    "copy": '<rect x="8.5" y="8.5" width="12" height="12" rx="2.5"/><path d="M15.5 8.5v-3a2 2 0 0 0-2-2h-8a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h3"/>',
    "laptop": '<rect x="4.5" y="5" width="15" height="10.5" rx="1.5"/><path d="M2.5 19h19"/>',
}

# Logo Google officiel (quatre couleurs), pour le bouton « Continuer avec Google »
GOOGLE_G = Markup('<svg class="g-logo" width="20" height="20" viewBox="0 0 48 48" aria-hidden="true" focusable="false">'
                  '<path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>'
                  '<path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>'
                  '<path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>'
                  '<path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>')


def icon(name: str, size: int = 20, stroke: float = 2, cls: str = "") -> Markup:
    klass = f"ic ic-{name}" + (f" {cls}" if cls else "")
    return Markup(f'<svg class="{klass}" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
                  f'stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" '
                  f'aria-hidden="true" focusable="false">{PATHS[name]}</svg>')


def logo_mark(size: int = 36, accent: str = "#22C55E") -> Markup:
    """Le symbole Probalis : carré bleu nuit, jauge verte (dorée pour Probalis Office)."""
    return Markup(f'<svg class="mark" width="{size}" height="{size}" viewBox="0 0 120 120" aria-hidden="true" focusable="false">'
                  '<rect class="mark-bg" width="120" height="120" rx="30"/>'
                  '<path d="M37.5 26 H59.5 A24 24 0 0 1 59.5 74 H37.5" fill="none" stroke="#FFFFFF" stroke-opacity="0.18" '
                  'stroke-width="12" stroke-linecap="round"/>'
                  f'<path d="M37.5 26 H59.5 A24 24 0 0 1 59.5 74 H37.5" fill="none" stroke="{accent}" stroke-width="12" '
                  'stroke-linecap="round" stroke-dasharray="83.6 200"/>'
                  '<rect x="30.5" y="20" width="14" height="80" rx="7" fill="#FFFFFF"/></svg>')
