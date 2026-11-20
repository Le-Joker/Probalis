"""Textes du site vitrine (page d'accueil publique), en français et en anglais.

Règles : tutoiement, mots de parieur, aucun gain promis, jamais « 100 % », bookmakers jamais nommés.
Les clés finissant par « _html » contiennent un peu de HTML écrit ici (jamais de texte venu de l'extérieur).
"""
from __future__ import annotations

SITE = {
    "fr": {
        "title": "Probalis · La vraie chance de chaque pari de foot",
        "description": "Probalis calcule la vraie chance de chaque pari de football sur 19 compétitions et te la dit en mots simples, "
                       "pour la comparer à la cote de ton bookmaker. Gratuit, sans promesse de gain.",
        "og_locale": "fr_FR",
        "skip": "Aller au contenu",
        "nav_label": "Sur cette page",
        "nav_tour": "L'appli", "nav_proof": "Les résultats", "nav_price": "Prix", "nav_install": "Installer",
        "open_app": "Ouvrir l'appli",
        "other_lang_label": "English version", "other_lang_short": "EN",
        "lang_banner": "Probalis is also available in English.", "lang_banner_link": "Read in English",
        "close": "Fermer",

        "hero_kicker": "La science du pari",
        "hero_h1_html": "«&nbsp;8&nbsp;fois sur&nbsp;10&nbsp;», <span>vraiment</span> 8&nbsp;fois sur&nbsp;10.",
        "hero_lead": "Probalis calcule la vraie chance de chaque pari de foot, sur 19 compétitions, et te la dit en mots simples. "
                     "Tu la compares à la cote de ton bookmaker avant de remplir ton coupon.",
        "hero_cta": "Accéder à l'application",
        "hero_cta2": "Voir les paris du jour",
        "hero_trust": "Gratuit avec un compte Google · Android, iPhone et ordinateur · 18+",
        "chip_chance": "Chance calculée", "chip_chance_v": "≈ 8 fois sur 10",
        "chip_weak": "Ticket scanné", "chip_weak_v": "Maillon faible repéré",
        "shot_alt_bets": "L'onglet Paris de Probalis : les paris les plus sûrs du jour, avec leur chance et leur cote juste",
        "shot_alt_match": "L'analyse d'un match dans Probalis : chances de victoire, buts attendus, scores les plus probables",
        "shot_alt_ticket": "Le constructeur de coupons de Probalis : chance du ticket et maillon faible",
        "shot_alt_matches": "L'onglet Matchs de Probalis : les matchs du jour et leurs probabilités",
        "shot_alt_history": "L'historique public de Probalis : les listes enregistrées avant les matchs",

        "proof_h2": "On a vérifié sur une saison entière.",
        "proof_lead": "Saison {season}, {n} matchs de 10 championnats. Chaque semaine, le modèle ne connaissait que les matchs déjà "
                      "joués, exactement comme en vrai. Résultat : ce qu'il annonce, c'est ce qui arrive.",
        "proof_announced": "Annoncé", "proof_real": "Réel",
        "proof_n": "{n} paris", "proof_coupon": "Coupons à cote ≈ 2",
        "proof_note": "Avoir raison sur la chance ne veut pas dire gagner de l'argent : le bookmaker garde une marge sur chaque cote. "
                      "À ses cotes estimées, ces paris auraient perdu entre {lo} et {hi} des mises. On préfère te le dire.",
        "proof_note_link": "Comprendre la marge",
        "proof_caption": "Chance annoncée et réussite réelle, saison {season}",

        "carnet_h2": "La liste du jour est enregistrée avant le premier match.",
        "carnet_lead": "Chaque jour, les paris du jour sont figés, puis réglés tout seuls avec le score final. "
                       "Rien n'est effacé, même les jours perdus.",
        "carnet_title": "Paris du jour",
        "carnet_saved": "Enregistré le",
        "carnet_locked": "Visible avec un compte gratuit",
        "carnet_more": "+ {n} autres paris et {c} coupons dans l'appli",
        "carnet_cta": "Voir les paris du jour",
        "carnet_history": "Voir tout l'historique",
        "carnet_empty": "Pas de liste aujourd'hui : trop peu de matchs fiables. Les paris reviennent dès qu'il y a de quoi faire.",
        "carnet_record": "Historique public depuis le {since} : {won} paris passés sur {n} réglés.",
        "carnet_record_early": "Historique public depuis le {since} : encore trop tôt pour juger, tout s'affichera ici, gagné comme perdu.",
        "res_won": "Gagné", "res_lost": "Perdu", "res_void": "Remboursé", "res_wait": "En attente",

        "tour_h2": "Tout ce qu'il faut savoir avant de remplir un coupon.",
        "tour_note": "Écrans d'exemple : les clubs sont fictifs. Les chiffres des vrais matchs restent dans l'appli.",
        "tour": [
            {"tab": "Onglet Matchs", "shot": "match",
             "h3": "Chaque match, décortiqué",
             "p": "Résultat, double chance, nombre de buts, les deux équipes marquent, score exact… Plus de 90 paris par match, "
                  "chacun avec sa chance en mots simples et sa cote juste."},
            {"tab": "Onglet Paris", "shot": "bets",
             "h3": "Les plus sûrs du jour, en trois niveaux",
             "p": "Prudent, Équilibré ou Audacieux : chaque jour, les 5 paris les plus probables de chaque niveau, sur des marchés "
                  "que tous les bookmakers proposent. Plus trois coupons tout prêts, à cote 2, 3 et 5."},
            {"tab": "Onglet Ticket", "shot": "ticket",
             "h3": "Ton coupon, passé au scanner",
             "p": "Ajoute tes matchs : Probalis calcule la vraie chance que ton ticket passe, repère le maillon faible et te propose "
                  "un remplaçant. Entre la cote de ton bookmaker : tu sais tout de suite si elle vaut le coup."},
            {"tab": "Onglet Historique", "shot": "history",
             "h3": "Nos résultats, sans maquillage",
             "p": "Les listes sont enregistrées avant les matchs et réglées avec le score final. Tu vois les jours gagnés comme les "
                  "jours perdus, et le test complet de la saison passée."},
        ],

        "odds_h2": "Ta cote cache une chance. Tape-la.",
        "odds_lead": "Chaque cote dit combien de fois un pari doit passer pour que tu ne perdes pas d'argent. "
                     "Essaie avec la cote de ton bookmaker.",
        "odds_label": "Cote de ton bookmaker",
        "odds_examples": "Exemples",
        "odds_need": "Pour ne pas perdre d'argent, ce pari doit passer",
        "odds_need_pct": "au moins {p} fois sur 100",
        "odds_times10": "≈ {n} fois sur 10", "odds_times100": "≈ {n} fois sur 100",
        "odds_margin": "Mais le bookmaker garde une marge (environ 5 %) : d'après sa propre cote, la vraie chance tourne plutôt "
                       "autour de {f}. C'est pour ça qu'à long terme, la maison gagne.",
        "odds_cta": "Dans Probalis, compare avec la chance calculée de chaque pari.",
        "odds_cta_link": "Voir les paris du jour",
        "odds_error": "Entre une cote entre 1,01 et 100, par exemple 1,50.",

        "honest_h2": "Ce qu'on ne te promettra jamais.",
        "honest_lead": "Aucun site ne peut te faire gagner à coup sûr. Probalis te donne des chances justes ; le bookmaker, lui, paie un "
                       "peu moins que ce qu'il devrait. Voici le test complet de la saison {season}, à ses cotes estimées "
                       "(cote juste moins 5 %).",
        "honest_caption": "Test sur la saison {season} : chaque pari misé à la cote estimée du bookmaker",
        "th_list": "Liste", "th_announced": "Chance annoncée", "th_real": "Réussite réelle", "th_roi": "Gain ou perte",
        "coupon_row": "Coupon cote ≈ {n}",
        "promises": [
            ("Jamais « 100 % »", "Rien n'est certain dans le foot. Même un pari à 90 % perd 1 fois sur 10."),
            ("Jamais « gain garanti »", "Pas d'étiquette « pari en or », pas de « coup sûr ». Juste des chances, bien calculées."),
            ("Toujours la liste d'avant-match", "Elle est figée avant le premier match, puis réglée avec le score. Gagné ou perdu, elle reste."),
        ],
        "responsible_html": "Le jeu d'argent peut créer une dépendance. Fixe-toi une limite et ne mise jamais l'argent du loyer, de la "
                            "nourriture ou de l'école. <b>Interdit aux moins de 18 ans.</b>",
        "responsible_link": "Jeu responsable",

        "comp_h2": "19 compétitions suivies.",
        "comp_lead": "Les grands championnats, les coupes d'Europe et le football féminin. Les paris du jour gardent seulement les "
                     "matchs les plus fiables : le football féminin a son analyse, mais n'entre pas dans les listes.",

        "price_h2": "Gratuit pour commencer. Premium pour tout voir.",
        "price_cur_label": "Monnaie",
        "free_name": "Gratuit", "free_price": "0", "free_unit": "avec un compte Google",
        "free_items": ["1 analyse complète par jour, sur le match de ton choix", "Le n° 1 de chaque liste du jour",
                       "Ton coupon analysé jusqu'à 3 matchs", "Tout l'historique", "Quelques pubs"],
        "free_cta": "Créer mon compte gratuit",
        "prem_name": "Premium", "prem_from": "Dès", "prem_from_unit": "pour 7 jours",
        "passes_label": "Les 5 durées du pass Premium",
        "pass_names": {"week": "7 jours", "month": "30 jours", "quarter": "3 mois", "half": "6 mois", "year": "1 an"},
        "pass_best": "Le plus avantageux",
        "save_note": "Remises calculées par jour, par rapport au pass 30 jours.",
        "prem_items": ["Tous les matchs, toutes les analyses", "Les 5 paris de chaque niveau et les coupons du jour",
                       "Ton coupon analysé jusqu'à 10 matchs", "Sans pub"],
        "prem_note": "Pass sans abonnement : tu paies une fois, rien ne se renouvelle tout seul. "
                     "Le paiement par mobile money et carte ouvre très bientôt.",
        "prem_cta": "Découvrir Premium",

        "inst_h2": "Installe Probalis en 10 secondes.",
        "inst_lead": "Pas besoin du Play Store ni de l'App Store : l'appli s'installe depuis ton navigateur, prend très peu de place "
                     "et s'ouvre comme les autres, depuis ton écran d'accueil.",
        "inst_prompt_btn": "Installer Probalis",
        "inst_prompt_help": "Une petite fenêtre s'ouvre : touche « Installer ».",
        "inst_android_h": "Sur Android",
        "inst_android": ["Touche le menu ⋮ en haut à droite de Chrome.",
                         "Choisis « Installer l'application » ou « Ajouter à l'écran d'accueil ».",
                         "Probalis apparaît avec tes autres applis."],
        "inst_ios_h": "Sur iPhone",
        "inst_ios": ["Ouvre cette page dans Safari.",
                     "Touche le bouton Partager (le carré avec une flèche vers le haut).",
                     "Choisis « Sur l'écran d'accueil », puis « Ajouter »."],
        "inst_inapp_h": "Ouvre d'abord la page dans ton navigateur",
        "inst_inapp": "Tu es dans le navigateur d'une autre appli (Facebook, Instagram, TikTok…) : il ne peut pas installer Probalis. "
                      "Touche ⋮ ou ··· puis « Ouvrir dans le navigateur ».",
        "inst_copy": "Copier le lien", "inst_copied": "Lien copié : colle-le dans Chrome ou Safari.",
        "inst_desk_h": "Sur ton téléphone",
        "inst_desk": "Scanne ce code avec l'appareil photo de ton téléphone : Probalis s'ouvre, et tu l'installes en deux touches.",
        "inst_desk_install": "Installer aussi sur cet ordinateur",
        "inst_done_h": "C'est fait !",
        "inst_done": "Probalis est sur ton écran d'accueil. Tu peux l'ouvrir comme tes autres applis.",
        "inst_done_open": "Ouvrir maintenant",
        "inst_nothing": "Tu préfères ne rien installer ?",
        "inst_nothing_link": "Utiliser Probalis dans le navigateur",
        "qr_label": "QR code qui ouvre Probalis",

        "faq_h2": "Questions fréquentes",
        "faq": [
            ("Probalis est-il un bookmaker ?",
             "Non. Probalis ne prend aucun pari et ne touche pas à ton argent. Tu joues où tu veux ; on t'aide seulement à choisir "
             "avec de vrais chiffres."),
            ("Est-ce que je vais gagner de l'argent ?",
             "Personne ne peut te le promettre. Nos chances sont justes, mais le bookmaker garde une marge sur chaque cote : à long "
             "terme, parier fait perdre un peu d'argent, même avec de bons chiffres. Probalis t'aide à éviter les mauvais paris et à "
             "miser en connaissant tes vraies chances."),
            ("D'où viennent les chances ?",
             "D'un modèle statistique qui étudie les buts marqués et encaissés par chaque équipe, ajusté sur les cotes moyennes du "
             "marché quand elles existent. Les données viennent de football-data.co.uk et de TheSportsDB."),
            ("Pourquoi jamais 100 % ?",
             "Parce que rien n'est certain dans le foot. Même un pari à 90 % perd 1 fois sur 10 : on préfère te le rappeler."),
            ("C'est quoi, la cote juste ?",
             "C'est la cote qu'un pari mériterait sans marge : 1 divisé par sa chance. Un pari à 80 % a une cote juste de 1,25. "
             "Si ton bookmaker paie moins, c'est sa marge."),
            ("Ça marche avec une petite connexion ?",
             "Oui. L'appli est légère, garde sur ton téléphone les pages déjà vues et les affiche quand le réseau traîne."),
            ("Combien coûte Premium ?",
             "Dès {week} pour 7 jours, {month} pour 30 jours, et jusqu'à {year} pour un an : plus le pass est long, "
             "moins le jour coûte cher. Sans abonnement, et le compte gratuit reste gratuit."),
        ],

        "final_line": "Choisis tes paris avec de vrais chiffres.",
        "foot_tagline": "La science du pari",
        "foot_app": "L'appli", "foot_more": "Probalis", "foot_contact": "Contact",
        "foot_matches": "Matchs du jour", "foot_bets": "Paris du jour", "foot_ticket": "Ticket", "foot_history": "Historique",
        "foot_premium": "Premium",
    },
    "en": {
        "title": "Probalis · The real chance of every football bet",
        "description": "Probalis works out the real chance of every football bet across 19 competitions and says it in plain words, "
                       "so you can compare it with your bookmaker's odds. Free, with no promise of winnings.",
        "og_locale": "en_GB",
        "skip": "Skip to content",
        "nav_label": "On this page",
        "nav_tour": "The app", "nav_proof": "Results", "nav_price": "Pricing", "nav_install": "Install",
        "open_app": "Open the app",
        "other_lang_label": "Version française", "other_lang_short": "FR",
        "lang_banner": "Probalis existe aussi en français.", "lang_banner_link": "Lire en français",
        "close": "Close",

        "hero_kicker": "The science of betting",
        "hero_h1_html": "“8 in 10” that <span>really</span> means 8&nbsp;in&nbsp;10.",
        "hero_lead": "Probalis works out the real chance of every football bet, across 19 competitions, and says it in plain words. "
                     "Compare it with your bookmaker's odds before you fill in your slip.",
        "hero_cta": "Get the app",
        "hero_cta2": "See today's bets",
        "hero_trust": "Free with a Google account · Android, iPhone and computer · 18+",
        "chip_chance": "Calculated chance", "chip_chance_v": "≈ 8 in 10",
        "chip_weak": "Slip scanned", "chip_weak_v": "Weakest link found",
        "shot_alt_bets": "The Probalis Bets tab: today's safest bets, with their chance and fair odds",
        "shot_alt_match": "A match analysis in Probalis: win chances, expected goals, most likely scores",
        "shot_alt_ticket": "The Probalis slip builder: the slip's chance and its weakest link",
        "shot_alt_matches": "The Probalis Matches tab: today's matches and their probabilities",
        "shot_alt_history": "The Probalis public history: lists saved before kick-off",

        "proof_h2": "We checked it over a whole season.",
        "proof_lead": "Season {season}, {n} matches in 10 leagues. Each week, the model only knew the matches already played, "
                      "exactly like in real life. The result: what it announces is what happens.",
        "proof_announced": "Announced", "proof_real": "Actual",
        "proof_n": "{n} bets", "proof_coupon": "Accumulators at odds ≈ 2",
        "proof_note": "Being right about the chance doesn't mean making money: the bookmaker keeps a margin on every price. "
                      "At its estimated odds, these bets would have lost between {lo} and {hi} of the stakes. We'd rather tell you.",
        "proof_note_link": "Understand the margin",
        "proof_caption": "Announced chance and actual hit rate, season {season}",

        "carnet_h2": "Today's list is saved before the first kick-off.",
        "carnet_lead": "Every day, the bets of the day are locked, then settled automatically with the final score. "
                       "Nothing is deleted, not even the losing days.",
        "carnet_title": "Today's bets",
        "carnet_saved": "Saved on",
        "carnet_locked": "Visible with a free account",
        "carnet_more": "+ {n} more bets and {c} accumulators in the app",
        "carnet_cta": "See today's bets",
        "carnet_history": "See the full history",
        "carnet_empty": "No list today: too few reliable matches. Bets come back as soon as there's something worth it.",
        "carnet_record": "Public history since {since}: {won} bets won out of {n} settled.",
        "carnet_record_early": "Public history since {since}: too early to judge yet. Everything will show here, wins and losses.",
        "res_won": "Won", "res_lost": "Lost", "res_void": "Void", "res_wait": "Pending",

        "tour_h2": "Everything you need to know before filling in a slip.",
        "tour_note": "Example screens: the clubs are fictional. Numbers for real matches stay inside the app.",
        "tour": [
            {"tab": "Matches tab", "shot": "match",
             "h3": "Every match, broken down",
             "p": "Result, double chance, total goals, both teams to score, correct score… More than 90 bets per match, each with "
                  "its chance in plain words and its fair odds."},
            {"tab": "Bets tab", "shot": "bets",
             "h3": "Today's safest bets, in three levels",
             "p": "Safe, Balanced or Bold: every day, the 5 most likely bets of each level, on markets every bookmaker offers. "
                  "Plus three ready-made accumulators, at odds 2, 3 and 5."},
            {"tab": "Slip tab", "shot": "ticket",
             "h3": "Your slip, scanned",
             "p": "Add your matches: Probalis works out the real chance your slip wins, finds the weakest link and suggests a "
                  "replacement. Enter your bookmaker's odds: you know at once whether they're worth it."},
            {"tab": "History tab", "shot": "history",
             "h3": "Our results, unvarnished",
             "p": "Lists are saved before kick-off and settled with the final score. You see the winning days and the losing "
                  "days, plus the full test of last season."},
        ],

        "odds_h2": "Your odds hide a chance. Type them in.",
        "odds_lead": "Every price tells you how often a bet must win for you not to lose money. Try it with your bookmaker's odds.",
        "odds_label": "Your bookmaker's odds",
        "odds_examples": "Examples",
        "odds_need": "Not to lose money, this bet must win",
        "odds_need_pct": "at least {p} times out of 100",
        "odds_times10": "≈ {n} in 10", "odds_times100": "≈ {n} in 100",
        "odds_margin": "But the bookmaker keeps a margin (about 5%): going by its own price, the real chance is closer to {f}. "
                       "That's why, in the long run, the house wins.",
        "odds_cta": "In Probalis, compare it with the calculated chance of every bet.",
        "odds_cta_link": "See today's bets",
        "odds_error": "Enter odds between 1.01 and 100, for example 1.50.",

        "honest_h2": "What we'll never promise you.",
        "honest_lead": "No website can make you win for sure. Probalis gives you fair chances; the bookmaker pays a little less than "
                       "it should. Here's the full test of season {season}, at its estimated odds (fair odds minus 5%).",
        "honest_caption": "Test over season {season}: every bet staked at the estimated bookmaker odds",
        "th_list": "List", "th_announced": "Announced chance", "th_real": "Actual hit rate", "th_roi": "Profit or loss",
        "coupon_row": "Accumulator odds ≈ {n}",
        "promises": [
            ("Never “100%”", "Nothing is certain in football. Even a 90% bet loses 1 time in 10."),
            ("Never “guaranteed win”", "No “golden bet” label, no “sure thing”. Just chances, carefully calculated."),
            ("Always the pre-match list", "It's locked before the first kick-off, then settled with the score. Won or lost, it stays."),
        ],
        "responsible_html": "Gambling can be addictive. Set yourself a limit and never stake money meant for rent, food or school. "
                            "<b>Over 18s only.</b>",
        "responsible_link": "Responsible gambling",

        "comp_h2": "19 competitions covered.",
        "comp_lead": "The big leagues, the European cups and women's football. Today's bets only keep the most reliable matches: "
                     "women's football gets its analysis but stays out of the lists.",

        "price_h2": "Free to start. Premium to see everything.",
        "price_cur_label": "Currency",
        "free_name": "Free", "free_price": "0", "free_unit": "with a Google account",
        "free_items": ["1 full analysis a day, on the match of your choice", "The no. 1 of each daily list",
                       "Your slip analysed up to 3 matches", "The full history", "A few ads"],
        "free_cta": "Create my free account",
        "prem_name": "Premium", "prem_from": "From", "prem_from_unit": "for 7 days",
        "passes_label": "The 5 Premium pass lengths",
        "pass_names": {"week": "7 days", "month": "30 days", "quarter": "3 months", "half": "6 months", "year": "1 year"},
        "pass_best": "Best value",
        "save_note": "Discounts worked out per day, compared with the 30-day pass.",
        "prem_items": ["Every match, every analysis", "All 5 bets of each level and today's accumulators",
                       "Your slip analysed up to 10 matches", "No ads"],
        "prem_note": "A pass, not a subscription: you pay once and nothing renews by itself. "
                     "Mobile money and card payments open very soon.",
        "prem_cta": "Discover Premium",

        "inst_h2": "Install Probalis in 10 seconds.",
        "inst_lead": "No Play Store or App Store needed: the app installs from your browser, takes very little space and opens like "
                     "any other, from your home screen.",
        "inst_prompt_btn": "Install Probalis",
        "inst_prompt_help": "A small window opens: tap “Install”.",
        "inst_android_h": "On Android",
        "inst_android": ["Tap the ⋮ menu at the top right of Chrome.",
                         "Choose “Install app” or “Add to Home screen”.",
                         "Probalis shows up with your other apps."],
        "inst_ios_h": "On iPhone",
        "inst_ios": ["Open this page in Safari.",
                     "Tap the Share button (the square with an arrow pointing up).",
                     "Choose “Add to Home Screen”, then “Add”."],
        "inst_inapp_h": "Open the page in your browser first",
        "inst_inapp": "You're in another app's browser (Facebook, Instagram, TikTok…): it can't install Probalis. "
                      "Tap ⋮ or ··· then “Open in browser”.",
        "inst_copy": "Copy the link", "inst_copied": "Link copied: paste it into Chrome or Safari.",
        "inst_desk_h": "On your phone",
        "inst_desk": "Scan this code with your phone's camera: Probalis opens, and you install it in two taps.",
        "inst_desk_install": "Also install on this computer",
        "inst_done_h": "Done!",
        "inst_done": "Probalis is on your home screen. Open it like any other app.",
        "inst_done_open": "Open it now",
        "inst_nothing": "Rather not install anything?",
        "inst_nothing_link": "Use Probalis in the browser",
        "qr_label": "QR code that opens Probalis",

        "faq_h2": "Frequently asked questions",
        "faq": [
            ("Is Probalis a bookmaker?",
             "No. Probalis takes no bets and never touches your money. You play wherever you like; we just help you choose with "
             "real numbers."),
            ("Will I make money?",
             "Nobody can promise you that. Our chances are fair, but the bookmaker keeps a margin on every price: in the long run, "
             "betting loses a little money, even with good numbers. Probalis helps you avoid bad bets and stake knowing your real "
             "chances."),
            ("Where do the chances come from?",
             "From a statistical model that studies the goals each team scores and concedes, adjusted to the average market odds "
             "when they exist. Data comes from football-data.co.uk and TheSportsDB."),
            ("Why never 100%?",
             "Because nothing is certain in football. Even a 90% bet loses 1 time in 10: we'd rather remind you."),
            ("What are fair odds?",
             "The odds a bet would deserve with no margin: 1 divided by its chance. An 80% bet has fair odds of 1.25. If your "
             "bookmaker pays less, that's its margin."),
            ("Does it work on a slow connection?",
             "Yes. The app is light, keeps the pages you've already seen on your phone and shows them when the network drags."),
            ("How much is Premium?",
             "From {week} for 7 days, {month} for 30 days, up to {year} for a year: the longer the pass, the less each "
             "day costs. No subscription, and the free account stays free."),
        ],

        "final_line": "Pick your bets with real numbers.",
        "foot_tagline": "The science of betting",
        "foot_app": "The app", "foot_more": "Probalis", "foot_contact": "Contact",
        "foot_matches": "Today's matches", "foot_bets": "Today's bets", "foot_ticket": "Slip", "foot_history": "History",
        "foot_premium": "Premium",
    },
}

def _fr_typo(x):
    """Espaces insécables du français (avant ? ! : ; et dans « »), pour qu'aucun signe ne reste seul en début de ligne."""
    if isinstance(x, str):
        for a, b in ((" ?", "\u00a0?"), (" !", "\u00a0!"), (" :", "\u00a0:"), (" ;", "\u00a0;"),
                     ("« ", "«\u00a0"), (" »", "\u00a0»")):
            x = x.replace(a, b)
        return x
    if isinstance(x, list):
        return [_fr_typo(v) for v in x]
    if isinstance(x, tuple):
        return tuple(_fr_typo(v) for v in x)
    if isinstance(x, dict):
        return {k: _fr_typo(v) for k, v in x.items()}
    return x


SITE["fr"] = _fr_typo(SITE["fr"])

# Monnaies proposées dans le bloc des prix (la première est celle affichée sans JavaScript)
CURRENCIES = {"fr": ["XAF", "EUR"], "en": ["USD", "NGN", "GHS", "KES"]}
CURRENCY_LABEL = {"XAF": "FCFA", "XOF": "FCFA", "EUR": "€", "USD": "$", "NGN": "₦", "GHS": "GH₵", "KES": "KSh"}
