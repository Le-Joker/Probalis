# Identité visuelle — Probalis

Validée le 19/11/2026.

## Nom et slogan

- **Nom :** Probalis (de « probabilité »). Il se comprend en français comme en anglais.
- **Slogan :** « La science du pari » / *The science of betting*.
- **Ton :** sérieux et honnête. On parle de probabilités et de valeur, jamais de « gain garanti ».

## Nom de domaine (vérifié le 19/11/2026)

- `probalis.com` est déjà réservé par quelqu'un (aucun site ne répond).
- `probalis.net` et `probalis.org` étaient disponibles ce jour-là.
- Au lancement à 0 $, l'appli utilise une adresse gratuite (`….pages.dev`). On achètera un domaine quand l'appli rapportera.

## Le logo

Un « P » dont la boucle est une **jauge de probabilité remplie à 70 %**. La partie verte, c'est la probabilité.

| Fichier | Usage |
|---|---|
| `brand/probalis-icone.svg` | Icône de l'appli (fond bleu nuit, coins arrondis) |
| `brand/probalis-icone-maskable.svg` | Icône Android plein cadre (le système découpe la forme) |
| `brand/probalis-logo-clair.svg` | Logo horizontal sur fond blanc |
| `brand/probalis-logo-sombre.svg` | Logo horizontal sur fond bleu nuit |
| `brand/png/icone-512.png`, `icone-192.png` | Icônes de la PWA |
| `brand/png/icone-maskable-512.png` | Icône Android adaptative |
| `brand/png/apple-touch-icon-180.png` | Icône iPhone (écran d'accueil) |
| `brand/png/favicon-32.png` | Petite icône de l'onglet du navigateur |
| `brand/png/logo-clair-760.png`, `logo-sombre-760.png` | Logos en image (réseaux sociaux, documents) |

À respecter :
- ne jamais déformer le logo ni changer ses couleurs ;
- garder un espace vide autour, au moins la largeur de la barre du « P » ;
- sur une photo ou un fond chargé, utiliser l'icône carrée.

## Couleurs

### Mode clair (par défaut) : blanc, vert, gris

| Rôle | Couleur | Code |
|---|---|---|
| Fond principal | Blanc | `#FFFFFF` |
| Cartes, zones secondaires | Gris très clair | `#F3F4F6` |
| Bordures, séparateurs | Gris clair | `#E5E7EB` |
| Texte principal | Gris anthracite | `#111827` |
| Texte secondaire | Gris moyen | `#6B7280` |
| Accent (barres, boutons, jauge) | Vert Probalis | `#22C55E` |
| Texte vert (lisible sur blanc) | Vert foncé | `#15803D` |
| Fond des étiquettes « Valeur » | Vert très pâle | `#DCFCE7` |

### Mode sombre : bleu nuit

| Rôle | Couleur | Code |
|---|---|---|
| Fond principal | Bleu nuit | `#0B1F3A` |
| Cartes | Bleu nuit clair | `#12294A` |
| Bordures | Bleu ardoise | `#1E3A5F` |
| Texte principal | Blanc cassé | `#F3F4F6` |
| Texte secondaire | Gris bleuté | `#94A3B8` |
| Accent | Vert Probalis | `#22C55E` |
| Texte vert | Vert clair | `#4ADE80` |
| Fond des étiquettes « Valeur » | Vert profond | `#14532D` |

### Lisibilité (contraste vérifié)

- Texte gris `#6B7280` sur blanc : 4,8 pour 1, conforme aux règles d'accessibilité.
- Vert foncé `#15803D` sur blanc : 5 pour 1, conforme.
- Le vert vif `#22C55E` sur blanc n'est **pas** assez lisible pour du petit texte (3,3 pour 1). On le réserve aux formes : barres, boutons, jauge.
- Vert `#22C55E` sur bleu nuit : 7,2 pour 1, très lisible.

### Signification des couleurs dans l'appli

- **Vert** = valeur positive, probabilité de l'équipe favorite, action principale.
- **Gris** = neutre, « pas de valeur », match nul.
- **Rouge** = jamais pour décorer. Seulement pour les erreurs et les pronostics perdus dans l'historique.

## Typographie

- **Inter** (police gratuite de Google Fonts) pour toute l'appli. Ses chiffres ont tous la même largeur, donc les cotes et les pourcentages restent bien alignés en colonnes.
- Deux graisses seulement : normale et semi-grasse.
- Si Inter ne charge pas, l'appli utilise la police du téléphone (Segoe UI, Roboto…).

## Logos des équipes

- On affiche les vrais logos des clubs fournis par les sources de données.
- S'il manque un logo, on affiche un badge rond avec les initiales du club, dans sa couleur principale.
