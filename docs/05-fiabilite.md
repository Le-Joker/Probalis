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
