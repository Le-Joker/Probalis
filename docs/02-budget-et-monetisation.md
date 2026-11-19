# Budget et modèle économique

Estimations établies le 19/11/2026. Les prix des fournisseurs changent : on vérifiera chaque tarif au moment de souscrire.

---

## 1. Les décisions prises

- On construit d'abord les moteurs des 4 sports (football, basketball, hockey, tennis). **On lance uniquement le football.**
- Langues : français et anglais. Marché visé : tous les pays.
- **PWA d'abord** : une application web installable sur l'écran d'accueil, Android comme iPhone. Les stores viendront quand ce sera rentable.
- Claude code, le porteur du projet teste.

### Pourquoi la PWA est un bon choix
- Aucun frais de store au départ. Pas de commission de 15 à 30 % de Google/Apple sur les abonnements.
- Les mises à jour sont instantanées, sans validation des stores.
- Chaque page d'analyse de match peut être **trouvée sur Google** (SEO), ce qui fait du trafic gratuit.
- Plus tard, la même PWA peut être publiée sur Google Play pour peu de travail (technique « Trusted Web Activity »), puis sur l'App Store via une enveloppe native.
- Limite sur iPhone : l'installation est manuelle (Partager → « Sur l'écran d'accueil »), et les notifications ne marchent qu'une fois l'appli installée.

---

## 2. Budget

### Phase 0 : développement des moteurs (maintenant) — **0 €**
- Données historiques gratuites pour construire et tester les modèles : football-data.co.uk fournit des fichiers CSV de résultats, cotes de plusieurs bookmakers, tirs, corners et cartons pour une vingtaine de championnats européens, sur plusieurs saisons.
- Offre gratuite d'API-Football (100 requêtes par jour) pour les essais.
- Tout tourne sur ton PC.

### Phase 1 : lancement de la PWA football — **0 $ possible**
On peut lancer gratuitement, avec quelques limites (12 compétitions, analyses avant-match, cotes rafraîchies une fois par jour). Le détail est dans [03-sources-gratuites.md](03-sources-gratuites.md).

### Phase 1 bis : quand on active la pub ou le Premium — **environ 40 à 80 $ par mois**
| Poste | Estimation | Remarque |
|---|---|---|
| Données foot (API-Football) | 19 à 29 $/mois | Matchs, compositions, blessures, stats, une partie des cotes. Prix trouvés : Pro ≈ 19 $ (7 500 req/jour), Ultra ≈ 29 $ (75 000 req/jour), à confirmer sur le site officiel. |
| Serveur (moteurs + API) | 5 à 20 $/mois | Petit serveur virtuel ou hébergeur Python |
| Site PWA + base de données | 0 à 25 $/mois | Les offres gratuites suffisent au début |
| Nom de domaine | ≈ 10 à 15 $/an | |
| Cotes multi-bookmakers dont 1xBet | à chiffrer | Des fournisseurs le proposent (odds-api.io, OpticOdds, Betstamp…), sur devis. Au début, on peut se limiter aux cotes incluses dans API-Football. |
| Rédaction des analyses par IA | faible, à chiffrer | Fonction optionnelle, activée plus tard |

### Phase 2 : autres sports et stores
- Données basketball et hockey : probablement le même ordre de prix par sport chez le même fournisseur, à vérifier.
- Tennis : bonnes données plus rares et plus chères.
- Google Play : 25 $ une seule fois. App Store : 99 $ par an.

---

## 3. Est-ce que la pub seule sera rentable ?

**Réponse courte : pas au début.**

1. **Google AdSense limite les sites de paris.** Ses règles classent les sites de paris sportifs et les sites d'affiliation qui en font la promotion en contenu « restreint ». Conséquence : beaucoup moins de pubs, et parfois aucune. Les régies qui acceptent ce contenu paient moins et affichent des pubs de moindre qualité.
2. **La pub paie peu en Afrique.** Les estimations trouvées donnent environ 0,50 à 2 $ pour 1 000 pages vues en Afrique, et environ 0,08 $ par clic au Cameroun. Ce sont des estimations de blogs, pas des chiffres officiels.

### Simulation (hypothèses volontairement simples)
Hypothèses :
- 5 pages vues par utilisateur et par jour ;
- pub : 0,30 à 1 $ pour 1 000 pages vues (contenu restreint) ;
- 2 % des utilisateurs prennent un abonnement à environ 4 $/mois ;
- 1 % des utilisateurs deviennent des joueurs actifs parrainés chez un bookmaker, à environ 5 $/mois de commission chacun.

| Utilisateurs actifs par jour | Pub seule | Abonnements | Affiliation | **Total mixte** |
|---|---|---|---|---|
| 1 000 | 45 à 150 $ | 80 $ | 50 $ | **≈ 175 à 280 $/mois** |
| 10 000 | 450 à 1 500 $ | 800 $ | 500 $ | **≈ 1 750 à 2 800 $/mois** |
| 50 000 | 2 250 à 7 500 $ | 4 000 $ | 2 500 $ | **≈ 8 750 à 14 000 $/mois** |

À comparer à des coûts d'environ 40 à 80 $/mois au début, puis 150 à 400 $/mois à grande échelle.

**Conclusion :** à 1 000 utilisateurs par jour, la pub seule couvre à peine les frais. Le vrai cap, c'est **10 000 utilisateurs par jour**. Le **modèle mixte** rapporte environ 2 à 4 fois plus que la pub seule.

---

## 4. Le modèle recommandé : mixte

1. **Gratuit** : analyses de base (1X2, plus/moins, BTTS) pour tous les matchs, avec quelques pubs discrètes.
2. **Premium** : tous les marchés, les value bets, le constructeur de ticket, les combos du jour et les alertes.
   - Afrique : paiement par mobile money (Orange Money, MTN MoMo, Wave…) via des agrégateurs comme CinetPay, NotchPay, Flutterwave ou Paystack. Les forfaits **à la semaine** marchent bien sur ces marchés.
   - Europe et reste du monde : carte bancaire.
   - À vérifier : certains prestataires de paiement refusent les activités liées aux paris.
3. **Affiliation bookmakers**, seulement dans les pays où c'est légal. Exemple : le programme de 1xBet est annoncé autour de 25 à 40 % de partage de revenus, avec un CPA possible sur négociation. Ce sont des chiffres de sites tiers, à confirmer.

### Points d'attention
- **Légalité par pays.** Faire la promotion d'un bookmaker non agréé est interdit dans plusieurs pays (en France, seuls les opérateurs agréés par l'ANJ peuvent être promus, par exemple). L'appli doit adapter les cotes et les liens affichés selon le pays du visiteur.
- **Conflit d'intérêts.** L'affiliation au partage de revenus rapporte quand les joueurs parrainés perdent. Notre force doit rester l'honnêteté : un **historique public et vérifiable** de tous nos pronostics.
- **Majeurs uniquement (18+)**, message de jeu responsable, aucune promesse de gain garanti.

### Comment attirer les utilisateurs
- Pages d'analyse de chaque match indexées par Google.
- Chaînes Telegram et WhatsApp (très efficaces pour les pronostics en Afrique), TikTok.
- L'historique public des résultats : c'est l'argument numéro 1 pour faire passer les gens en Premium.
