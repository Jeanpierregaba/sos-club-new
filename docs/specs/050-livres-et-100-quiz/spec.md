# 050 — Livres Génie Imhotep, 100 quiz Jeux et badges nommés

## Objectif

Trois retouches demandées le 2026-11-23, avant l'ouverture au public :

1. Publier dans la bibliothèque les 4 livres de l'Académie Génie Imhotep fournis par AIMES-AFRIQUE, à lire et
   télécharger librement.
2. Revenir au principe d'avant la spec 049 : les Jeux couvrent les 1 000 questions de la banque officielle, en 100 quiz,
   et la certification réutilise des questions très difficiles qui figurent aussi dans les Jeux (au lieu du partage
   800 / 200 de la spec 049).
3. Sur la page publique de la certification, les cartes des 20 quiz obligatoires portent le nom de leur badge, et non
   « Thématique 1 », « Thématique 2 »…

## Comportement attendu

**Livres.** Au déploiement, les 4 livres sont publiés dans la bibliothèque, catégorie « Fascicule », axe Génie Imhotep,
avec leur couverture (la première page), leur nombre de pages et le validateur « AIMES-AFRIQUE — Clubs Santé SOS
Docteur TV », qualité « Document officiel de l'Académie Génie Imhotep » :

| Fichier                                                   | Titre                                                  |
| --------------------------------------------------------- | ------------------------------------------------------ |
| `Livre_Academie_Genie_Imhotep_College.pdf` (148 p.)        | Génie Imhotep — Questionnaire du jeu, Collège          |
| `Livre_Academie_Genie_Imhotep_Lycee.pdf` (177 p.)          | Génie Imhotep — Questionnaire du jeu, Lycée            |
| `Livre_Academie_Genie_Imhotep_EVSS.pdf` (80 p.)            | Génie Imhotep — Éducation aux valeurs et santé sexuelle (EVSS) |
| `Livre_Emission_Genie_Imhotep_SOS_Docteur_TV_Saison1.pdf` (115 p.) | Génie Imhotep — L'émission sur SOS Docteur TV, saison 1 |

Chaque carte de la bibliothèque propose déjà « Lire » et « Télécharger ».

**100 quiz Jeux.** Les 80 quiz Jeux de la spec 049 sont dépubliés (rien n'est effacé : parties et points restent) et
100 nouveaux quiz de 10 questions les remplacent, numérotés de 1 à 100 :

- 60 quiz « moyennement difficiles » (600 questions) : 40 Débutant puis 20 Intermédiaire ;
- 40 quiz « très difficiles » (400 questions, dont les 200 de la certification) : 10 Intermédiaire, 20 Avancé,
  10 Expert ;
- chaque quiz puise dans une seule partie du document, les parties alternant d'un quiz à l'autre ;
- réussite à 8/10, comme depuis la spec 049.

Les 20 quiz de la certification ne changent pas : la progression déjà faite y reste.

**Badges.** Section « Les 20 quiz obligatoires » de `/certification` : chaque carte titre le nom de son badge
(« Ambassadeur Santé Junior », …, « Maître Génie Imhotep ») ; la section des badges affiche « Badge 01 », sans
« Thématique 1 ». Dans l'espace connecté, le parcours titre chaque groupe de 4 quiz par le nom de son badge.

## Critères d'acceptation

- [ ] Après la migration, 100 quiz Jeux publiés, numéros 1 à 100, 40/30/20/10 par niveau, 10 questions chacun, et les
      1 000 énoncés de la banque y figurent chacun une fois.
- [ ] Les 200 questions des 20 quiz de certification figurent aussi dans les quiz Jeux, et seulement dans les niveaux
      Intermédiaire à Expert.
- [ ] Les 80 quiz de la spec 049 sont dépubliés avec un motif, leurs tentatives et les points restent.
- [ ] Les 20 quiz de certification publiés sont les mêmes avant et après.
- [ ] Rejouer la migration ou la lancer sur une base sans la banque officielle ne change rien.
- [ ] Le chargement des livres publie 4 ressources « Fascicule » téléchargeables, avec fichier, couverture et pages ;
      relancé, il n'en ajoute aucune.
- [ ] La page Jeux affiche 100 quiz (40/30/20/10) et le barème des étoiles en tient compte.
- [ ] `/certification` n'affiche plus « Thématique N » sur les cartes des badges ni des 20 quiz.

## Cas limites et erreurs

- Un livre déjà présent sous le même titre, même dépublié par l'équipe : on ne le recrée pas et on n'y touche pas.
- Un PDF refusé par le contrôle de la bibliothèque : le chargement s'arrête avec un message clair, la migration reste
  appliquée.
- Un élève qui a déjà gagné une étoile avec les 80 quiz la garde (rien ne s'efface) ; sa progression vers les étoiles
  suivantes repart sur les 100 nouveaux quiz.
- Une tentative en cours sur un des 80 quiz dépubliés : elle se clôt comme pour la spec 049.
- Retour arrière de la migration : refusé si un des 100 quiz a déjà été joué.

## Hors périmètre

- Relier les livres aux places de la certification (« Lire le fascicule »).
- Nouvelle remise à zéro des points.

## Questions ouvertes

Aucune : chargement au déploiement et recomposition des 100 quiz tranchés le 2026-11-23.
