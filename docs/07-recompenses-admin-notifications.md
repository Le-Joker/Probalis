# 07 · Récompenses, parrainage, administration, notifications et e-mails par Gmail

Ce guide accompagne la mise à jour « récompenses ». Tu n'as rien à programmer : il faut installer un petit
programme Google (5 minutes), puis enregistrer quelques réglages secrets dans Supabase et GitHub.

> Règle d'or, toujours : **aucun secret dans le code**. Les mots de passe et adresses secrètes vont dans les
> « secrets » de Supabase et de GitHub, et c'est **toi** qui les tapes.

---

## 1. Ce qui change dans l'appli

- **Bouton « Contacter +237 670375810 »** à la place du bouton Payer : il ouvre WhatsApp avec un message déjà
  écrit (formule choisie, prix, nom et e-mail du compte). Le jour où le paiement en ligne sera branché, il suffira
  de mettre la variable `PROBALIS_PAYMENTS` à `online` pour retrouver le bouton Payer.
- **Onglet « Récompenses »** dans Mon compte : les cadeaux et analyses offertes à activer, le lien d'invitation à
  partager (WhatsApp, copier, partager), l'historique.
- **Parrainage** : chaque membre a un lien court `https://probalis.pages.dev/i/CODE`. Le parrain gagne des
  **analyses de match** (jamais du Premium) ; l'ami en reçoit aussi à son arrivée.
- **Cadeaux de l'administrateur** : Premium (une des 5 formules) ou analyses de match. Le membre reçoit un e-mail
  avec le bouton « Activer la récompense », puis active son cadeau dans l'onglet Récompenses.
- **Notifications** (à activer par chaque membre dans Mon compte) : les paris du jour sont prêts (une fois par
  jour au plus), un cadeau ou une récompense est arrivé, ton Premium est activé.
- **Hors connexion**, l'appli affiche un écran « Pas de connexion » au lieu de pages dépassées.
- **Cartes de partage** : un lien Probalis collé dans WhatsApp montre une belle image (accueil ou invitation).

## 2. Le barème du parrainage (réglable dans l'administration)

| Action de l'ami | Le parrain gagne |
|---|---|
| Il crée son compte avec le lien (dans les 7 jours) | **+2** analyses |
| Il utilise Probalis **3 jours** différents | **+3** analyses |
| Il achète un pass Premium | **+4** (7 jours), **+5** (30 jours), **+6** (3 mois), **+8** (6 mois), **+10** (1 an) |

L'ami reçoit **+2** analyses en bienvenue. Un parrain gagne au plus **10** analyses par mois. Un compte ne peut
utiliser qu'un seul code, jamais le sien, et seulement dans ses 3 premiers jours. Une analyse offerte ouvre un match
au choix (en plus de l'analyse gratuite du jour).

## 3. E-mails par Gmail (Google Apps Script)

Le programme `probalis/site/emails/gmail_script.js` envoie les e-mails depuis ton adresse Gmail (environ 100 par
jour, gratuit). Il ne lit pas ta boîte mail.

1. **Invente un long mot de passe** pour Probalis (au moins 24 caractères, lettres et chiffres). Pour en fabriquer
   un, lance dans PowerShell :

   ```powershell
   -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
   ```

   Garde-le pour toi : il sert aux étapes 3 et 6, et dans la partie 4.
2. Connecté au compte Gmail qui enverra les e-mails, ouvre **script.google.com** → **Nouveau projet**. Efface tout
   le contenu, colle tout le fichier `gmail_script.js`, puis **Enregistrer** (nomme le projet « Probalis e-mails »).
3. **Paramètres du projet** (roue dentée à gauche) → **Propriétés du script** → **Ajouter une propriété** :
   nom `SECRET`, valeur = ton mot de passe de l'étape 1 → **Enregistrer**.
4. Reviens à l'éditeur, choisis la fonction **testEnvoi** en haut, puis **Exécuter**. Google demande ton accord
   pour « envoyer des e-mails en ton nom » : accepte (c'est toi qui décides). Tu reçois un e-mail de test.
5. **Déployer** → **Nouveau déploiement** → type **Application Web** :
   - *Exécuter en tant que* : **Moi** ;
   - *Qui a accès* : **Tout le monde** (le mot de passe protège l'envoi) ;
   - **Déployer**, puis copie l'**URL de l'application Web** (elle finit par `/exec`).
6. Tu as maintenant deux valeurs : l'adresse `/exec` (`GMAIL_SCRIPT_URL`) et le mot de passe
   (`GMAIL_SCRIPT_SECRET`). Elles vont dans Supabase et GitHub (parties 4 et 5).

> Si tu changes un jour le programme, fais **Déployer → Gérer les déploiements → Modifier → Nouvelle version** :
> l'adresse `/exec` reste la même.

## 4. Les secrets de Supabase

Dans Supabase : **Edge Functions** → **Secrets** (ou **Project Settings → Edge Functions**), puis **Add new
secret** pour chacun :

| Nom | Valeur |
|---|---|
| `GMAIL_SCRIPT_URL` | l'adresse `/exec` de la partie 3 |
| `GMAIL_SCRIPT_SECRET` | le mot de passe de la partie 3 |
| `ADMIN_EMAILS` | ton adresse Google de connexion à Probalis (plusieurs adresses : séparées par des virgules) |
| `SITE_URL` | `https://probalis.pages.dev` (ou ton futur domaine) |
| `CONTACT_EMAIL` | `probalis-support@googlegroups.com` |

Les clés des notifications sont créées toutes seules au premier usage et gardées dans la base : rien à faire.

## 5. Les secrets de GitHub (e-mails et notification du jour)

Sur GitHub : dépôt Probalis → **Settings** → **Secrets and variables** → **Actions** → **New repository secret** :
`GMAIL_SCRIPT_URL` et `GMAIL_SCRIPT_SECRET`, avec les mêmes valeurs. La tâche « E-mails du jour » envoie alors ses
e-mails par Gmail, puis la notification « Les paris du jour sont prêts ».

## 6. Probalis Office (l'appli de l'administrateur)

Il y a deux applis : **Probalis** pour les membres, et **Probalis Office** pour toi. Office vit à part, à l'adresse
**https://probalis.pages.dev/office/** : aucun lien public n'y mène, les moteurs de recherche ne la voient pas, et
elle a son propre nom et son icône (le P doré au lieu de vert).

1. Une fois `ADMIN_EMAILS` enregistré et la mise à jour en ligne, ouvre **https://probalis.pages.dev/office/** et
   touche **Se connecter avec Google** avec cette adresse. Tu reviens directement dans Office.
   Ensuite, un lien « Ouvrir Probalis Office » apparaît aussi dans ton onglet Mon compte (et chez toi seulement).
   - **Installer Office** : sur Android ou sur ordinateur (Chrome, Edge), le bouton ⬇ en haut d'Office l'installe.
     Sur iPhone : Safari → bouton Partager → **Sur l'écran d'accueil**. L'icône dorée « Office » se range à côté
     de l'icône verte de Probalis.
   - Un compte qui n'est pas dans `ADMIN_EMAILS` voit « Ce compte n'a pas accès » et peut changer de compte.
2. **Tableau de bord** : membres, actifs, Premium, notifications, parrainages, paiements, inscriptions des 14 derniers
   jours. Un clic sur un chiffre ouvre la liste qui va avec.
3. **Membres** : cherche par nom, e-mail ou code. Le bouton **⋮** d'un membre propose :
   - **Offrir le Premium** (7 jours, 30 jours, 3 mois, 6 mois, 1 an) ou **Offrir des analyses** ; un petit mot est
     possible. Si l'e-mail ne part pas, la fenêtre donne le lien du cadeau à envoyer sur WhatsApp ;
   - **Paiement WhatsApp reçu** : choisis la formule, la monnaie et le montant reçu. Le Premium s'active tout de
     suite, le reçu part par e-mail et le parrain reçoit ses analyses ;
   - **Voir la fiche**, **Arrêter le Premium**.
4. **Récompenses** : renvoyer un cadeau (nouveau lien, l'ancien ne marche plus) ou annuler une récompense.
5. **E-mails** : la liste des envois et un bouton pour t'envoyer un e-mail de test.
6. **Journal** : tout ce qui a été fait depuis Office.
7. **Réglages** : le barème du parrainage, et une **annonce** par notification à tous les téléphones abonnés.

> Seules les adresses de `ADMIN_EMAILS` passent : le serveur vérifie à chaque action. La page elle-même ne
> contient aucune donnée.

## 7. Essayer sans rien brancher

Tant que Supabase n'est pas branché sur le site (mode démo), tout s'essaie sur le téléphone : onglet Récompenses
avec un cadeau d'exemple, analyses offertes, et Probalis Office (`/office/`) avec de **faux membres** (rien n'est
envoyé ni enregistré).
