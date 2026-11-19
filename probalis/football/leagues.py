"""Compétitions couvertes (sources gratuites, voir docs/03-sources-gratuites.md)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class League:
    code: str          # code interne ; pour les championnats masculins, code football-data.co.uk (fichiers CSV)
    tsdb_id: int       # identifiant TheSportsDB (calendrier, résultats, logos)
    name_fr: str
    name_en: str
    country_fr: str
    country_en: str
    slug: str
    # "domestic" : championnat masculin ; "europe" : coupe d'Europe masculine ; "women" : football féminin
    category: str = "domestic"
    cup: bool = False  # compétition entre clubs de pays différents (Ligue des champions, etc.)
    logo_on_dark: bool = False  # logo officiel blanc : à afficher sur un fond foncé


LEAGUES: tuple[League, ...] = (
    League("E0", 4328, "Premier League", "Premier League", "Angleterre", "England", "premier-league"),
    League("SP1", 4335, "LaLiga", "LaLiga", "Espagne", "Spain", "liga"),
    League("I1", 4332, "Serie A", "Serie A", "Italie", "Italy", "serie-a"),
    League("D1", 4331, "Bundesliga", "Bundesliga", "Allemagne", "Germany", "bundesliga"),
    League("F1", 4334, "Ligue 1", "Ligue 1", "France", "France", "ligue-1"),
    League("E1", 4329, "Championship", "Championship", "Angleterre", "England", "championship"),
    League("N1", 4337, "Eredivisie", "Eredivisie", "Pays-Bas", "Netherlands", "eredivisie"),
    League("P1", 4344, "Liga Portugal", "Liga Portugal", "Portugal", "Portugal", "liga-portugal"),
    League("B1", 4338, "Pro League", "Pro League", "Belgique", "Belgium", "pro-league"),
    League("T1", 4339, "Süper Lig", "Süper Lig", "Turquie", "Turkey", "super-lig"),
    # Coupes d'Europe : un modèle commun relie les forces des différents pays (voir football/linked.py)
    League("UCL", 4480, "Ligue des champions", "Champions League", "Europe", "Europe", "ligue-des-champions",
           "europe", True, logo_on_dark=True),
    League("UEL", 4481, "Ligue Europa", "Europa League", "Europe", "Europe", "ligue-europa", "europe", True,
           logo_on_dark=True),
    League("UECL", 5071, "Ligue Conférence", "Conference League", "Europe", "Europe", "ligue-conference",
           "europe", True, logo_on_dark=True),
    # Football féminin : résultats TheSportsDB, un modèle commun à tous ces championnats
    League("UWCL", 4889, "Ligue des champions féminine", "Women's Champions League", "Europe", "Europe",
           "ligue-des-champions-feminine", "women", True),
    League("WSL", 4849, "Women's Super League", "Women's Super League", "Angleterre", "England",
           "womens-super-league", "women"),
    League("FBL", 5204, "Frauen-Bundesliga", "Frauen-Bundesliga", "Allemagne", "Germany", "frauen-bundesliga",
           "women"),
    League("WD1", 5203, "Arkema Première Ligue (D1)", "Arkema Première Ligue (D1)", "France", "France",
           "premiere-ligue", "women"),
    League("LIGAF", 5106, "Liga F", "Liga F", "Espagne", "Spain", "liga-f", "women"),
    League("SAW", 5205, "Serie A féminine", "Serie A Women", "Italie", "Italy", "serie-a-femminile", "women"),
)

BY_CODE = {lg.code: lg for lg in LEAGUES}


def season_codes(start_year: int, n: int) -> list[str]:
    """Codes de saison football-data.co.uk, du plus récent au plus ancien : 2026 -> '2627', '2526', ..."""
    return [f"{(y) % 100:02d}{(y + 1) % 100:02d}" for y in range(start_year, start_year - n, -1)]


def tsdb_seasons(start_year: int, n: int) -> list[str]:
    """Saisons au format TheSportsDB, de la plus récente à la plus ancienne : 2026 -> '2026-2027', ..."""
    return [f"{y}-{y + 1}" for y in range(start_year, start_year - n, -1)]


def current_season_start(today) -> int:
    """Une saison commence en juillet."""
    return today.year if today.month >= 7 else today.year - 1
