# Catalogue des marchés de paris

Référence pour les moteurs d'analyse. Sources, consultées le 19/11/2026 :

- Règlement officiel betPawa Cameroun : https://www.betpawa.cm/rules
- Règlement officiel 1xBet (PDF « sportsbook rules ») : https://a.1xbet.com/web-api/rulespdf

Un règlement liste les marchés qu'un bookmaker *peut* proposer. Tous ne sont pas ouverts sur chaque match.

---

## 1. Le principe : peu de moteurs, des centaines de marchés

On ne programme pas un calcul différent pour chaque pari. Chaque **moteur** calcule une distribution de probabilités, par exemple « la probabilité de chaque score possible, par mi-temps ». Chaque marché se lit ensuite directement dans cette distribution.

| Moteur | Ce qu'il calcule | Exemples de marchés produits |
|---|---|---|
| **A. Score** | Probabilité de chaque score (match, 1re et 2e mi-temps) | 1X2, double chance, plus/moins, handicaps, BTTS, score exact, mi-temps/fin, pair/impair, marge de victoire, combos du même match |
| **B. Temps** | Quand les buts tombent (minute par minute) | Prochain but, 1er/dernier à marquer, intervalles 10/15 min, 1UP/2UP, « reste du match » |
| **C. Corners** | Nombre de corners par équipe et par mi-temps | Total corners, corners équipe, handicap corners, 1X2 corners, 1er/dernier corner |
| **D. Discipline** | Cartons, penaltys, expulsions (arbitre + équipes) | Total cartons, équipe la plus avertie, penalty oui/non, expulsion |
| **E. Joueurs** | Part de chaque joueur dans les tirs/buts de son équipe, minutes jouées | Buteur (1er, dernier, à tout moment), passeur, tirs, tirs cadrés, arrêts du gardien, carton joueur |
| **F. Statistiques** | Tirs, fautes, hors-jeu, xG d'équipe | Totaux de tirs, de fautes, de hors-jeu, marchés xG |
| **G. Compétition** | Simulation de tournois et de prolongations | Qualification, vainqueur final, vainqueur de groupe, prolongation, tirs au but |

---

## 2. Couverture du football betPawa

Le règlement betPawa liste **121 marchés football**. Répartition par moteur :

| Moteur | Nb de marchés betPawa | Phase |
|---|---|---|
| A. Score | 58 | Lancement |
| B. Temps | 11 | Lancement |
| C. Corners | 8 | Lancement |
| D. Discipline | 6 | Lancement |
| G. Compétition | 15 | Lancement |
| E. Joueurs | 23 | Phase 2 (il faut les compositions et les stats par joueur) |

- **Au lancement : 98 / 121 marchés, soit 81 %.** C'est au-dessus de l'objectif des 70 %.
- **Avec le moteur Joueurs : 121 / 121, soit 100 %.**

Le détail du moteur A couvre notamment : 1X2 (match, 1re, 2e mi-temps), plus/moins (match, mi-temps, par équipe), handicaps 2 et 3 issues, double chance, BTTS, clean sheet, gagner sans encaisser, score exact (match et mi-temps), mi-temps/fin de match, MT/FT + totaux, pair/impair, nombre exact de buts, multibuts, multiscores, mi-temps la plus prolifique, gagner les deux mi-temps / au moins une, marquer dans les deux mi-temps, marge de victoire, et tous les combos (1X2 + plus/moins, 1X2 + BTTS, double chance + BTTS, double chance + plus/moins, plus/moins + BTTS, « domicile ou plus de X », etc.).

---

## 3. Couverture du football 1xBet

1xBet propose beaucoup plus de lignes par match, souvent plusieurs centaines. Elles se rangent dans les mêmes familles.

**Couvert par nos moteurs :**
- Tout ce qui est listé chez betPawa.
- Handicap asiatique et total asiatique, y compris les lignes en quart (par ex. −1,25 ou 2,75) — moteur A.
- Totaux individuels (« total équipe 1 / équipe 2 ») — moteur A.
- « Événements rapides » : total, handicap ou résultat dans un intervalle de minutes — moteur B.
- Premier but et équipe qui gagne avec tel score, course à X buts — moteurs A et B.
- Points cartons (jaune = 10, rouge = 25), cartons jaunes/rouges « YRC » — moteur D.
- « Bet Constructor » (comparer des équipes de matchs différents) — moteur A.
- Tirs, tirs cadrés, fautes, hors-jeu, marchés xG — moteur F, phase 2.

**Volontairement non couvert :** touches, six mètres, poteaux/transversales, recours à la VAR, « premier contact après le premier corner », distance parcourue, « qui a le ballon au coup de sifflet final », entraîneurs et transferts.

Raisons : les données fiables n'existent pas ou ces événements sont du pur hasard. Ce sont aussi les marchés où la marge du bookmaker est la plus élevée.

---

## 4. « Les plus rapporteurs » : attention au piège

Une grosse cote ne veut pas dire un pari rentable. Plus un marché est exotique, plus le bookmaker prend de marge. Un pari est intéressant quand **notre probabilité × la cote > 1**. C'est ce qu'on appelle la valeur, ou espérance positive.

L'appli classera donc les marchés en trois catégories :

| Catégorie | Marchés | Rôle dans l'appli |
|---|---|---|
| **Socle** | 1X2, double chance, plus/moins 1,5 / 2,5 / 3,5, BTTS, remboursé si nul, handicap asiatique | Les plus joués. Notre modèle y est le plus solide. |
| **Valeur** | Corners, cartons, totaux par équipe, marchés de 1re mi-temps, lignes asiatiques des petits championnats, combos du même match | Le bookmaker y est moins précis. C'est là qu'on trouve le plus souvent de la valeur. |
| **Gros coup** | Score exact, mi-temps/fin de match, 1er buteur, marge de victoire, gros combinés | Grosses cotes, faible probabilité, forte marge. Affichés **seulement** quand notre calcul montre une valeur positive. |

Pour chaque marché, on calcule la vraie marge du bookmaker à partir de ses cotes, au lieu de la supposer.

---

## 5. Les combinés

### Combiné de plusieurs matchs
Les marges se multiplient. Exemple : 5 sélections avec 5 % de marge chacune. La cote totale vaut alors la « cote juste » divisée par 1,05⁵ = 1,276. **Le bookmaker garde environ 22 %** de la mise en moyenne, contre 5 % sur un pari simple.

Règle de l'appli : on ne combine que des sélections qui ont chacune une valeur positive, et on recommande 2 à 4 sélections au maximum.

### Combo d'un même match (bet builder, « Match combos »)
Les événements d'un même match sont liés. Par exemple, « victoire du favori à domicile » et « plus de 2,5 buts » vont souvent ensemble. Notre matrice de scores calcule la **probabilité exacte** de la combinaison. Les bookmakers évaluent parfois mal ces liens, ce qui peut créer de la valeur.

Attention : betPawa refuse les sélections dépendantes dans un combiné classique (par ex. « gagne la 1re mi-temps » + « gagne le match »), sauf si une cote spéciale de combo existe.

### Types de tickets
- **betPawa** : simple, combiné jusqu'à 60 sélections, « Match combos ».
- **1xBet** : simple, combiné, système, chaîne, Advancebet, Multibet, conditionnel, anti-combiné, Lucky, Patent.

### Fonction prévue : le constructeur de ticket
L'utilisateur ajoute ses sélections. L'appli calcule :
- la vraie probabilité que le ticket passe ;
- l'espérance de gain ;
- la comparaison entre combiné et système (par ex. 2/3, 3/4) ;
- une alerte si deux sélections sont liées.

---

## 6. Autres sports (moteurs construits dès maintenant, lancés plus tard)

### Basketball
- **Modèle** : efficacité offensive et défensive pour 100 possessions, rythme, domicile, repos (matchs consécutifs), blessures. On simule les points par quart-temps.
- **Marchés** : vainqueur (prolongation incluse), 1X2 mi-temps/quart-temps, handicap (match, mi-temps, quart-temps), total (match, mi-temps, quart-temps, par équipe), vainqueur + total, pair/impair, mi-temps/fin de match, course à X points, marge de victoire, quart-temps le plus prolifique, prolongation oui/non, gagner les deux mi-temps. En phase 2 : stats joueurs (points, rebonds, passes, 3 points).

### Hockey sur glace
- **Modèle** : buts par période (xG, qualité du gardien titulaire, supériorité numérique), puis prolongation et tirs au but, et effet « cage vide » en fin de match.
- **Marchés** : 1X2 temps réglementaire, vainqueur avec prolongation/TAB, puck line et handicaps, total et total équipe, marchés par période, période la plus prolifique, prochain but, course à X buts, marquer en premier et gagner, vainqueur + total, but dans un intervalle, but en cage vide, buts en supériorité, minutes de pénalité, tirs cadrés, prolongation oui/non. En phase 2 : joueurs (buts, points, tirs).
- Note : le règlement betPawa Cameroun ne contient aucun marché hockey.

### Tennis
- **Modèle** : Elo par surface et probabilité de gagner un point au service et au retour. On simule ensuite le match point par point (point → jeu → set → match). Tout découle de ces chiffres.
- **Marchés** : vainqueur, vainqueur de chaque set, score exact en sets, nombre de sets, handicap jeux (match et set), total jeux (match, set, par joueur), pair/impair, tie-break dans le match ou un set, gagner au moins un set, set gagné 6-0, perdre le 1er set et gagner, nombre de breaks, vainqueur d'un jeu précis, score du tie-break.

---

## 7. Ce que l'appli affiche pour chaque marché

| Champ | Exemple |
|---|---|
| Notre probabilité | 61 % |
| Cote juste (1 / probabilité) | 1,64 |
| Meilleure cote bookmaker | 1,80 (1xBet) |
| Marge du bookmaker sur ce marché | 6,2 % |
| Valeur (probabilité × cote − 1) | +9,8 % |
| Indice de confiance | Élevé / Moyen / Faible (qualité des données, taille de l'échantillon) |
| Explication | « Les deux équipes concèdent beaucoup d'occasions, 4 des 5 derniers face-à-face ont dépassé 2,5 buts… » |
