# Lancement à 0 $ : les sources gratuites

État au 19/11/2026. Les sources marquées « testé » ont été appelées pour de vrai ce jour-là.

---

## 1. Les sources retenues

| Besoin | Source gratuite | Ce qu'on obtient | Limite |
|---|---|---|---|
| Calendrier, résultats, classements, **logos** | **football-data.org** (clé gratuite, inscription par e-mail) | 12 compétitions : Premier League, Championship, Liga, Serie A, Bundesliga, Ligue 1, Eredivisie, Primeira Liga, Brasileirão, Ligue des champions, Euro, Coupe du monde. Chaque équipe a son logo (`crest`). | 10 appels par minute, scores en différé, pas de données joueurs. Testé : sans clé, l'API répond « accès refusé » (normal, il faut la clé gratuite). |
| Historique + statistiques pour les moteurs | **football-data.co.uk** (aucune inscription) | Fichiers CSV par saison : scores (mi-temps et fin), tirs, tirs cadrés, **corners, fautes, cartons, arbitre**, cotes 1X2, plus/moins 2,5 et handicap asiatique (Bet365, Betfair, BetVictor, Betway, Paddy Power, Sky Bet…), cotes d'ouverture et de clôture. | Testé : saison 2026/27 à jour (100 matchs de Premier League au 08/11/2026). Le fichier des matchs à venir n'est mis à jour qu'une ou deux fois par semaine. |
| Logos de secours, couleurs des clubs | **TheSportsDB** (clé publique « 123 ») | Logo, écusson et couleur principale de chaque équipe. Testé : Arsenal → logo et couleur #EF0107. | Très limité en calendrier (1 seul match à venir renvoyé en gratuit). D'après des sites tiers, l'offre gratuite serait réservée à un usage non commercial. |
| Compositions, blessures, stats détaillées | **API-Football**, offre gratuite (inscription) | Tous les championnats du monde, y compris africains, plus les logos. | 100 requêtes par jour, saisons récentes peut-être restreintes (à tester avec la clé). À réserver aux gros matchs. |
| Cotes en direct, **dont 1xBet** | **The Odds API**, offre gratuite (inscription) | 500 crédits par mois. Le site officiel cite 1xBet parmi ses bookmakers européens. | Environ 1 crédit par championnat et par type de marché. Ça suffit pour rafraîchir les grands championnats une fois par jour. À vérifier : 1xBet est-il inclus dans l'offre gratuite ? |
| Cotes betPawa | Aucune API | — | L'utilisateur saisit sa cote dans le constructeur de ticket, et l'appli calcule la valeur. |

### Coupes d'Europe et football féminin (ajoutés le 19/11/2026, testé)

| Compétition | Calendrier et résultats | Comment on calcule les chances |
|---|---|---|
| Ligue des champions, Ligue Europa, Ligue Conférence | **TheSportsDB** (clé « 123 ») : tous les tours, phase de ligue (journées 1 à 8), barrages, 8es, quarts, demies, finale et qualifications, sur 3 saisons. | Un **modèle relié** : chaque club a sa force propre + la force moyenne de son pays. Les championnats nationaux (football-data.co.uk : 11 pays dans les fichiers habituels + Autriche, Suisse, Danemark, Norvège, Suède, Pologne, Roumanie, Irlande, Finlande) mesurent les écarts entre clubs d'un même pays ; les matchs européens mesurent l'écart entre pays. |
| Ligue des champions féminine, WSL, Frauen-Bundesliga, Arkema Première Ligue, Liga F, Serie A féminine | **TheSportsDB** : résultats journée par journée sur 2 saisons. | Même modèle relié : un groupe par championnat, la Ligue des champions féminine relie les championnats entre eux. |

- **Pas de cotes gratuites** pour ces compétitions (football-data.co.uk ne couvre que les championnats masculins). L'analyse vient donc du modèle seul, affichée « Modèle statistique seul », avec une confiance plafonnée à « moyenne ». Pour avoir les cotes des coupes d'Europe, il faudra la clé gratuite de The Odds API.
- **Sources écartées :** ClubElo (son service de calendrier est fermé et son API ne répondait plus le 19/11/2026) ; API-Football gratuit (100 appels par jour et, à vérifier avec une clé, saisons en cours peut-être réservées aux offres payantes).
- **Premier lancement plus long** (environ 30 minutes : TheSportsDB bloque au-delà d'une dizaine d'appels par minute) : il faut télécharger toutes les anciennes journées. Elles sont ensuite gardées en cache pour toujours, les lancements suivants ne demandent que les journées en cours.

**Affichage des équipes :** chaque match montre les deux logos, le nom des équipes et la compétition. Si un logo manque, l'appli affiche un **badge avec les initiales du club dans ses couleurs**, donc jamais d'image cassée.

---

## 2. Héberger et faire tourner l'appli à 0 $

| Élément | Solution gratuite | Pourquoi |
|---|---|---|
| Site PWA | **Cloudflare Pages** | Gratuit, rapide en Afrique comme en Europe, et d'après les comparatifs l'usage commercial est autorisé (à confirmer dans les conditions de Cloudflare). On écarte **Vercel Hobby** : réservé à l'usage non commercial, donc incompatible avec la pub et le Premium. |
| Calcul des analyses | **GitHub Actions** (tâches programmées) | Toutes les 2 heures pendant la journée, les moteurs Python récupèrent les données, recalculent les analyses des 8 prochains jours et remettent le site en ligne (voir partie 5). Pas besoin de serveur. |
| Base de données | Aucune au début | Les analyses sont des fichiers statiques. Une base gratuite (Supabase) viendra avec les comptes et le Premium. |
| Textes d'analyse | Générés par des modèles de phrases | Gratuit. L'IA pourra être ajoutée plus tard. |
| Adresse du site | Sous-domaine gratuit `….pages.dev` | Un vrai nom de domaine coûte environ 10 $ par an, en option. |

---

## 3. Ce qu'on accepte en lançant à 0 $

1. **12 compétitions au départ.** Ce sont celles où se placent la majorité des paris. Les autres championnats arriveront avec un budget, ou via le quota gratuit d'API-Football pour quelques matchs.
2. **Analyses avant-match uniquement**, pas de direct.
3. **Cotes rafraîchies environ une fois par jour**, et pas pour tous les bookmakers.
4. **Compositions et blessures** seulement pour les gros matchs (100 requêtes par jour).
5. **Conditions d'utilisation à vérifier avant de gagner de l'argent.** Les offres gratuites de certaines sources sont peut-être réservées à un usage non commercial. Une bêta gratuite ne pose pas de problème. Au moment d'activer la pub ou le Premium, il faudra peut-être passer une source en payant (environ 9 à 19 $ par mois). On le fera à ce moment-là, payé par les premiers revenus.
6. **Les logos appartiennent aux clubs.** Les afficher pour identifier une équipe est la pratique courante des applis de sport, mais ce n'est pas un droit garanti. Le badge à initiales sert de solution de repli.

---

## 4. Comptes gratuits à créer (par le porteur du projet, le moment venu)

1. GitHub : stockage du code et calculs automatiques.
2. Cloudflare : hébergement du site.
3. football-data.org : calendrier et logos.
4. API-Football : compositions et blessures.
5. The Odds API : cotes.

Les clés d'accès ne seront jamais écrites dans le code. Elles seront rangées dans les « secrets » de GitHub.

### Activer la relance automatique (une fois les comptes GitHub et Cloudflare créés)

1. Mettre le projet dans un dépôt GitHub (Claude peut s'en charger une fois le compte créé). Dépôt privé conseillé.
2. Sur Cloudflare : *My Profile → API Tokens → Create Token*, modèle personnalisé avec le droit
   **Account · Cloudflare Pages · Edit**. Noter aussi l'**Account ID** (affiché dans le tableau de bord).
3. Dans le dépôt GitHub : *Settings → Secrets and variables → Actions*, ajouter deux secrets :
   `CLOUDFLARE_API_TOKEN` et `CLOUDFLARE_ACCOUNT_ID`.
4. Onglet *Actions* → « Analyses et site » → *Run workflow*. Ce premier lancement crée le site (adresse en `….pages.dev`)
   et dure environ 30 minutes (tout l'historique est téléchargé). Ensuite, GitHub relance tout seul.

Sans les secrets Cloudflare, les analyses tournent quand même, mais le site n'est pas mis en ligne.

---

## 5. Rythme des analyses (depuis le 19/11/2026)

- **Fenêtre glissante de 8 jours.** Chaque lancement analyse les matchs d'aujourd'hui jusqu'à J+8 : le 19, du 19
  au 27 ; le 20, du 20 au 28, etc. L'appli avance journée par journée dans le calendrier jusqu'à couvrir les 8 jours,
  même quand un championnat joue trois journées en une semaine (fêtes de fin d'année).
- **Relance toutes les 2 heures pendant la journée** (fichier `.github/workflows/build.yml`) : 8 h 17, 10 h 17…
  22 h 17, puis 0 h 17 pour les résultats du soir (heure UTC, soit 1 heure de plus à Paris en hiver). Aucun match
  de nos compétitions ne se joue entre 1 h et 8 h UTC. GitHub peut décaler un lancement de quelques minutes.
- **À chaque relance :**
  - les matchs déjà commencés ou terminés disparaissent des listes ;
  - les résultats déjà connus, **y compris ceux du jour même**, mettent à jour la force des équipes qui viennent de
    jouer. Les fichiers football-data.co.uk n'étant complétés qu'environ deux fois par semaine, les derniers scores
    sont repris de TheSportsDB (testé : 95 résultats sur 95 identiques au fichier officiel) ;
  - les changements d'horaire et les reports sont pris en compte ;
  - les nouvelles cotes sont reprises dès que football-data.co.uk les publie.
- **Pas de « tendance du jour » :** sur 14 320 matchs, les premiers résultats d'une journée n'annoncent rien pour
  les matchs suivants (voir `docs/05-fiabilite.md`). Un résultat compte seulement pour les deux équipes qui ont joué.
- **Limite des cotes gratuites :** le fichier de cotes de football-data.co.uk n'est mis à jour que le mardi et le
  vendredi. Entre deux, les chances des championnats calés sur les cotes bougent peu. Pour suivre les cotes en
  continu (compositions, blessures de dernière minute), il faudra The Odds API : sa clé gratuite (500 crédits par
  mois) permet environ une mise à jour par jour des grands championnats, pas une toutes les 2 heures. Au-delà, il
  faudra une offre payante.
- **Coût : 0 $.** Un lancement mesuré le 19/11/2026 : 3 minutes de calcul (27 appels à TheSportsDB, limité à un
  appel toutes les 6,5 secondes), soit environ 5 minutes avec l'installation et la mise en ligne. 9 lancements par
  jour font environ 1 400 minutes par mois : sous les 2 000 minutes gratuites d'un dépôt privé (illimité pour un
  dépôt public). Côté Cloudflare, environ 280 mises en ligne par mois, dans les limites de l'offre gratuite
  (à confirmer dans les conditions de Cloudflare).
