# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Parieurs de football d'Afrique francophone (Cameroun, Côte d'Ivoire, Sénégal…), surtout sur téléphone Android, souvent avec une connexion lente ou des données limitées, qui paient en FCFA (mobile money). Ils jouent chez leur bookmaker habituel et veulent savoir quels paris ont vraiment de bonnes chances avant de remplir un coupon. L'anglais sert aux autres pays (Nigeria, Ghana, Kenya…).

## Product Purpose

Probalis calcule la vraie chance de chaque pari de football (plus de 90 marchés par match, 19 compétitions) et la traduit en mots simples (« ≈ 8 fois sur 10 ») et en cote juste, pour que le parieur compare avec la cote de son bookmaker. Réussir, c'est qu'il choisisse ses paris avec des chiffres honnêtes plutôt qu'au hasard, et qu'il ne soit jamais trompé par une promesse de gain.

## Positioning

Des chiffres qui prouvent qu'ils disent vrai : chaque liste du jour est enregistrée avant les matchs et réglée toute seule avec le score final (Historique public), et la simulation sur toute la saison 2025/26 montre que les chances annoncées collent à la réalité. Probalis dit aussi ce que les sites de pronostics cachent : la marge du bookmaker fait perdre un peu d'argent à long terme.

## Operating Context

- Appli web installable (PWA) en français et en anglais, aujourd'hui pensée pour le téléphone ; une interface ordinateur est prévue.
- Onglets : Matchs (analyse complète de chaque match), Paris (les plus sûrs du jour en 3 niveaux : Prudent, Équilibré, Audacieux, plus les coupons du jour), Ticket (constructeur de coupons : Mon coupon, Cote cible, Nb de matchs), Historique, Compte.
- Connexion avec Google. Gratuit avec compte : 1 analyse complète par jour, le n° 1 de chaque liste, l'analyse de « Mon coupon » jusqu'à 3 matchs, tout l'historique, avec quelques pubs. Premium (pass sans abonnement) : tout, sans pub.
- Données : football-data.co.uk et TheSportsDB ; modèle statistique calé sur les cotes moyennes du marché quand elles existent.
- Hébergement gratuit (Cloudflare Pages, probalis.pages.dev) ; pas encore de nom de domaine ni d'e-mails.

## Capabilities and Constraints

- 19 compétitions : Premier League, Championship, LaLiga, Serie A, Bundesliga, Ligue 1, Eredivisie, Liga Portugal, Pro League, Süper Lig, Ligue des champions, Ligue Europa, Ligue Conférence, et 6 compétitions féminines.
- Les paris du jour et les coupons excluent le football féminin et les matchs à faible confiance.
- Cote bookmaker estimée = cote juste moins une marge de 5 % par sélection ; jamais affichée comme une vraie cote.
- Jamais d'étiquette « Valeur » ni de « gain garanti » ; jamais 100 %.
- Paiements (Stripe, Flutterwave/mobile money) prêts en mode démo, pas encore branchés. Formules prévues : semaine, mois, 3 mois, 6 mois, 1 an (pas encore en place).
- Prévu plus tard : interface admin, récompenses, parrainage, e-mails.

## Brand Commitments

- Nom Probalis, slogan « La science du pari » / « The science of betting ».
- Logo : un « P » dont la boucle est une jauge verte remplie à 70 % (`brand/`). Ne jamais le déformer ni changer ses couleurs.
- Couleurs voulues par l'utilisateur : blanc dominant, vert et gris en mode clair ; bleu nuit en mode sombre ; « net comme le logo ». Rouge seulement pour les erreurs et les paris perdus.
- Ton sérieux, honnête, chaleureux, tutoiement en français.
- Les bookmakers ne sont pas nommés sur le site (on dit « ton bookmaker »).

## Evidence on Hand

- Simulation 2025/26 (`probalis/site/simulation.json`) : 3 276 matchs, 10 championnats ; Prudent 79 % réussis pour 78 % annoncés, Équilibré 66 % pour 66 %, Audacieux 47 % pour 49 % ; coupons cote ≈ 2 : 48 % pour 44 % ; et une perte de 4 à 7 % à la cote estimée du bookmaker.
- Historique réel public depuis le 20 novembre 2026 (`/data/history.json`), encore trop récent pour juger.
- L'appli elle-même, pour de vraies captures d'écran.
- Aucun témoignage, aucun avis, aucun chiffre d'utilisateurs : ne rien inventer.

## Product Principles

- L'honnêteté d'abord : chaque chiffre affiché doit pouvoir être vérifié, et les limites sont dites clairement.
- Parler comme un parieur, pas comme un statisticien : « ≈ 8 fois sur 10 » avant « 78 % ».
- Léger et rapide sur un petit téléphone Android et une connexion lente.
- Jeu responsable : 18 ans et plus, ne jamais pousser à miser plus.

## Accessibility & Inclusion

Lisible en plein soleil sur un téléphone d'entrée de gamme : contrastes conformes, textes courts, cibles tactiles larges, animations coupées si l'appareil demande moins de mouvement, page utilisable même avec une connexion 2G/3G.
