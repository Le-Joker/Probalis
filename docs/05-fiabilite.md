# 05 · Fiabilité : ce que dit le test sur la saison 2025/26

Test refait le 19 novembre 2026 avec `python -m probalis backtest --season 2526`.

## Méthode

On rejoue la saison passée semaine par semaine, sur 10 championnats (3 276 matchs). Chaque semaine, le modèle n'apprend que sur les matchs d'avant, puis prédit ceux de la semaine. On compare ensuite aux vrais résultats et aux **cotes de clôture**, c'est-à-dire les cotes juste avant le coup d'envoi. Ce sont les plus difficiles à battre.

La mesure principale est la *log-loss* : plus elle est basse, plus les probabilités sont justes.

## Résultats

| Mesure | Notre modèle seul | Cotes du marché |
|---|---|---|
| Résultat 1X2 (log-loss) | 1,0062 | **0,9874** |
| Plus/moins 2,5 buts (log-loss) | 0,6884 | **0,6743** |
| Plus/moins 2,5 déduit des cotes 1X2 | 0,6845 | 0,6743 |

| Stratégie de paris (1 unité par pari, cote de clôture) | Paris | Rendement |
|---|---|---|
| « Value bets » du modèle (mélange 50/50, seuil +5 %) | 1 933 | **−11,9 %** |
| Meilleure cote au-dessus de la cote juste du consensus (+2 %) | 1 072 | **−12,1 %** |

Ce qui ne change rien de notable : le mélange modèle + marché (25 %, 50 %, 75 %), et les réglages d'oubli et de prudence du modèle (grille dans `data/backtest/resultats-2526.json`).

## Ce qu'on en conclut

1. **Le marché est plus précis que notre modèle seul.** C'est normal : les cotes de clôture intègrent les compositions, les blessures et l'argent des parieurs professionnels.
2. **Afficher « Valeur » sur la base de notre modèle tromperait l'utilisateur.** Ces paris auraient perdu environ 12 % sur la saison. On ne les affiche donc plus.
3. **Quand des cotes existent, l'appli se cale dessus.** On calcule les buts attendus qui reproduisent les cotes 1X2 et plus/moins 2,5 (sans la marge), puis on en déduit tous les autres marchés : handicaps, scores exacts, mi-temps, combinés. Ces marchés dérivés sont plus justes que ceux du modèle seul.
4. **Sans cotes, le modèle seul sert de base**, avec l'étiquette « Modèle statistique seul ».

## Ce qui pourrait battre le marché plus tard (à tester, rien de promis)

- Les cotes **tôt dans la semaine**, avant que le marché ne se corrige, plutôt que la clôture.
- Les **petits marchés** des bookmakers grand public (1xBet, betPawa) : buteurs, corners, cartons. Ils sont souvent moins bien réglés que le 1X2.
- Une meilleure façon d'enlever la marge (méthodes « puissance » ou « Shin »), parce que la méthode proportionnelle surestime les outsiders.
- Les compositions d'équipe et les blessures, une heure avant le match.

Chacune de ces pistes devra passer le même test avant d'être affichée dans l'appli.

## Coupes d'Europe (test du 19/11/2026)

Pas de cotes gratuites pour ces matchs : on compare le modèle à un repère simple, qui donne à chaque match
les fréquences moyennes de victoire à domicile, de nul et de victoire à l'extérieur. Le modèle est
réentraîné toutes les deux semaines, uniquement sur les matchs d'avant (`python -m probalis.football.backtest_linked`).

| Période | Matchs | Log-loss modèle | Log-loss repère | Bon pronostic (modèle / repère) | Favoris à 60 % ou plus : chances annoncées / gagnés |
|---|---|---|---|---|---|
| Saison 2025/26 (qualifications comprises) | 652 | 0,965 | 1,032 | 55,4 % / 49,1 % | 72,0 % / 70,4 % (230 matchs) |
| Saison 2026/27 jusqu'au 18/11 | 389 | 0,934 | 1,029 | 59,1 % / 49,4 % | 72,5 % / 72,3 % (112 matchs) |

- Le modèle fait nettement mieux que le repère, et **ses pourcentages sont fiables** : quand il annonce
  environ 72 % pour un favori, celui-ci gagne environ 71-72 % du temps.
- Il n'est pas comparé aux bookmakers (pas de cotes gratuites) : on ne prétend donc pas les battre.

## Football féminin (test du 19/11/2026)

Même méthode (repère = fréquences moyennes), sur la saison 2026/27 jusqu'au 18/11, modèle entraîné sur les
matchs d'avant (`python -m probalis.football.backtest_linked --women`).

| Compétition | Matchs | Log-loss modèle | Log-loss repère | Bon pronostic (modèle / repère) | Favoris à 60 % ou plus : annoncés / gagnés |
|---|---|---|---|---|---|
| Championnats (WSL, Frauen-Bundesliga, Première Ligue, Liga F, Serie A) | 310 | 0,862 | 1,061 | 61,9 % / 44,8 % | 75,4 % / 82,6 % (115 matchs) |
| Ligue des champions féminine | 54 | 0,875 | 1,113 | 61,1 % / 42,6 % | 77,9 % / 69,4 % (36 matchs) |

- En championnat, le modèle est plutôt **prudent** : ses gros favoris gagnent un peu plus souvent qu'annoncé.
  Un réglage plus « audacieux » a été essayé : légèrement meilleur en championnat, moins bon en Ligue des
  champions, donc on garde le réglage prudent.
- Peu de matchs testés (une demi-saison) : ces chiffres seront refaits en fin de saison.

## « Les premiers matchs donnent la tendance du jour » ? (test du 19/11/2026)

Idée testée : si les premiers matchs d'une journée donnent beaucoup de buts, ou si les favoris y perdent,
les matchs suivants du même championnat iraient-ils dans le même sens ?

Méthode (`python -m probalis.football.tendance`) : 10 championnats, 4 saisons (2022/23 à 2025/26), 14 320 matchs.
Pour chaque match, la « surprise » = le résultat réel moins ce que prévoyaient les cotes. On compare la surprise
des premiers matchs du jour à celle des 7 269 matchs qui commencent au moins 2 heures plus tard, donc quand les
premiers résultats sont connus.

| Ce qu'on compare | Corrélation | Intervalle à 95 % |
|---|---|---|
| Buts en plus ou en moins que prévu | −0,005 | −0,028 à +0,018 |
| Plus de 2,5 buts plus ou moins souvent que prévu | −0,022 | −0,043 à 0,000 |
| Favori qui gagne plus ou moins souvent que prévu | −0,006 | −0,031 à +0,018 |

- Quand les premiers matchs ont donné au moins 1 but de plus que prévu, les matchs suivants en ont donné
  **−0,01 but** de plus que prévu (1 774 matchs) : rien.
- Quand les favoris ont été battus dans les premiers matchs, les favoris suivants ont gagné **un peu plus**
  souvent que prévu (+1,6 point, 2 436 matchs), pas moins.

**Conclusion : il n'y a pas de tendance du jour.** Un résultat ne change pas les chances d'un autre match entre
d'autres équipes. Ce que l'appli fait des résultats du jour : ils mettent à jour la force des **deux équipes qui
viennent de jouer**, pour leurs matchs suivants. Les analyses sont recalculées toutes les 2 heures pour intégrer
ces résultats, les changements d'horaire, les reports et les nouvelles cotes dès qu'elles sont publiées.

## Nouveau moteur « fait maison » (test du 21/11/2026)

Commande : `python -m probalis.football.tune --train 2425 --test 2526 --write` (15 championnats avec fichiers
football-data, y compris les 5 nouvelles divisions). Les réglages sont appris sur 2024/25 (5 522 matchs), puis
mesurés sur 2025/26 (5 484 matchs), une saison que le moteur n'a jamais vue, semaine par semaine (le moteur ne
connaît que les matchs déjà joués). Réglages enregistrés dans `probalis/football/engine_params.json`.

Indices combinés : force des équipes sur 3 saisons (buts), buts « mérités » tirés des tirs et tirs cadrés (part 0,185),
forme récente à mémoire courte (part 0,457, mesurée sur les buts mérités), écart entre équipes un peu accentué
(t = 1,313), total de buts presque inchangé (s = 0,992). Avec des cotes : marge retirée par la méthode « puissance »,
puis cotes seules (part apprise : 1,0, le modèle ne fait pas mieux que le marché juste avant le match).

Règle d'adoption : le nouveau moteur ne remplace l'ancien que si son log-loss est au moins aussi bon sur le 1X2 et sur
plus/moins de 2,5 buts, avec et sans cotes (borne haute à 95 % de l'écart, bootstrap par journée, ≤ +0,0005).

| Chemin | Marché | Ancien | Nouveau | Brier ancien → nouveau | Décision |
|---|---|---|---|---|---|
| Modèle seul | 1X2 | 1,01977 | 1,01339 | 0,6111 → 0,6071 | adopté |
| Modèle seul | Plus/moins 2,5 | 0,69088 | 0,68369 | 0,2487 → 0,2454 | adopté |
| Avec cotes | 1X2 | 1,00251 | 1,00144 | 0,5995 → 0,5990 | adopté |
| Avec cotes | Plus/moins 2,5 | 0,67898 | 0,67892 | 0,2431 → 0,2431 | adopté (égalité) |

Corners et cartons (loi binomiale négative, écart propre aux équipes réduit vers la moyenne du championnat :
0,748 pour les corners, 0,65 pour les cartons). Comparés à « la moyenne du championnat pour tout le monde » :

| Marché | Matchs | Lignes : moteur (moyenne) | Décision |
|---|---|---|---|
| Corners | 4 988 | 8,5 : 0,6600 (0,6627) · 9,5 : 0,6905 (0,6921) · 10,5 : 0,6651 (0,6676) | adopté |
| Cartons | 5 484 | 3,5 : 0,6607 (0,6677) · 4,5 : 0,6511 (0,6595) | adopté |

Le gain sur les corners est petit : les corners sont difficiles à prévoir. On le dit dans la fiche (pourcentages modestes).

### Verdicts OUI / NON : annoncé contre réussi (2025/26)

| Verdict | Nombre | Réussis | Annoncés |
|---|---|---|---|
| « Le plus sûr » du match | 5 484 | 82,5 % | 82,3 % |
| Double chance | 5 484 | 77,8 % | 77,9 % |
| Plus de 1,5 but | 5 484 | 75,8 % | 75,6 % |
| Chaque équipe marque | 10 968 | 74,0 % | 72,6 % |
| Plus de 3,5 buts | 5 484 | 71,1 % | 70,4 % |
| Cartons | 5 484 | 67,5 % | 68,8 % |
| Corners | 4 988 | 65,7 % | 66,6 % |
| Victoire du favori | 5 484 | 58,5 % | 59,2 % |
| Plus de 2,5 buts | 5 484 | 56,1 % | 56,9 % |
| Les deux équipes marquent | 5 484 | 55,0 % | 55,2 % |

Les pourcentages annoncés tiennent : l'écart reste sous 1,5 point partout. Le tableau de fiabilité complet (par famille
et par tranche de 5 points) est dans `engine_params.json` (clé `reliability`) ; la fiche d'un match l'utilise pour la
phrase de preuve du verdict « le plus sûr ».

Ce qui n'est pas vérifiable gratuitement : corners et cartons des coupes d'Europe (estimés à partir du championnat de
chaque club ; aucune source gratuite ne publie leurs chiffres). Ligue saoudienne et football féminin : ni corners ni
cartons (pas de données). Ces verdicts n'entrent pas dans les taux de l'historique.

### Simulation des paris du jour avec le nouveau moteur (2025/26, 15 championnats)

`python -m probalis.football.simulation --season 2526` (calée sur les cotes, comme le site). Résultat repris par le site
(`probalis/site/simulation.json`) :

| Liste | Paris | Réussite | Annoncé | Gain ou perte à la cote estimée du bookmaker |
|---|---|---|---|---|
| Prudent | 1 043 | 77,6 % | 78,6 % | −6,0 % |
| Équilibré | 1 045 | 65,6 % | 66,3 % | −5,6 % |
| Audacieux | 1 049 | 49,9 % | 48,9 % | −2,9 % |
| Coupon cote ≈ 2 | 216 | 49,5 % | 43,6 % | +3,0 % |
| Coupon cote ≈ 3 | 216 | 32,9 % | 29,1 % | +2,4 % |
| Coupon cote ≈ 5 | 213 | 18,3 % | 16,7 % | −4,7 % |

Les chances annoncées tiennent (écart d'environ 1 point sur les listes). Le petit gain des coupons à cote 2 et 3 vient
d'un petit nombre de coupons (216) : ce n'est pas un avantage durable, on ne le présente jamais comme tel.
