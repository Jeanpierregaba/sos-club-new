# PRD — Product Requirements Document

Source : [cahier des charges](cahier-des-charges.md), noté CDC ci-dessous. Quand le PRD et le CDC
diffèrent, le PRD fait foi. Les écarts sont listés en fin de document, et les hypothèses encore à
confirmer sont les questions Q1 à Q16.

## Nom du projet

Club Santé SOS Docteur TV : plateforme nationale interactive des Clubs Santé du Togo, sous le
parrainage d'AIMES-AFRIQUE.

## Problème résolu

Les clubs santé scolaires sensibilisent les élèves à l'hygiène, à la nutrition, à la santé sexuelle,
aux maladies non transmissibles et à l'environnement. Leurs actions restent locales et peu visibles,
les ressources validées médicalement sont difficiles à trouver, et rien ne valorise durablement
l'engagement des élèves et des enseignants. La plateforme donne un même lieu pour s'informer, publier
les actions de terrain et se mesurer entre clubs.

## Utilisateurs cibles

| Profil    | Qui                                                     | Ce qu'il veut accomplir                                                 | Niveau technique                   |
| --------- | ------------------------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------- |
| Visiteur  | Grand public, parent, partenaire                        | Découvrir les clubs, l'agenda, les vidéos et les magazines              | Variable                           |
| Élève     | Collégien ou lycéen, souvent mineur, membre d'un club   | Apprendre, réussir des quiz, gagner des points et des badges, témoigner | Téléphone, parfois sans email      |
| Encadreur | Enseignant qui anime un club (souvent SVT, civisme)     | Faire vivre son club, publier ses activités, conseiller les élèves      | Bureautique simple, téléphone      |
| Club      | Entité collective d'un établissement (pas une personne) | Avoir un score, une page, des articles et un agenda                     | Sans objet : piloté par encadreurs |
| Admin     | Équipe nationale AIMES-AFRIQUE et SOS DOCTEUR TV        | Modérer, publier les contenus officiels, suivre l'engagement            | Bureautique                        |

## Parcours principaux

1. **Enregistrer un club** : un encadreur déclare le club avec 3 encadreurs (nom, email, téléphone)
   → l'admin valide → les 2 autres encadreurs reçoivent une invitation → le club est actif et
   visible sur la carte.
2. **Rejoindre un club et jouer** : un élève choisit sa région puis son club → crée son compte (+50
   points au club, +20 à son Passeport) → réussit un quiz (+25 pour lui, +10 pour le club, un badge)
   → apparaît au classement.
3. **Publier une activité** : un encadreur rédige un article avec photo et axe de santé → l'admin
   approuve ou rejette avec un motif → l'article est publié (+100 points au club) → les encadreurs
   commentent et le club répond.
4. **S'informer sans compte** : un visiteur consulte la carte, l'agenda, les vidéos par axe, les
   actualités et télécharge un magazine.

## Fonctionnalités du MVP

Chaque ligne deviendra une spec dans `docs/specs/`, dans l'ordre de `TASKS.md`.

- [ ] Un utilisateur se connecte et se déconnecte ; chaque rôle n'accède qu'à ce qui le concerne.
- [ ] Le site public et l'API sont en ligne dans un environnement de préproduction.
- [ ] Un encadreur enregistre un club avec exactement 3 encadreurs différents ; l'admin le valide ou le rejette.
- [ ] Un élève s'inscrit sous un club actif ; le club gagne 50 points et son Passeport démarre à 20 points.
- [ ] Un encadreur retire un faux compte d'élève de son club et réinitialise le mot de passe d'un élève ; les points sont annulés dans le journal.
- [ ] Un élève consulte son Passeport Santé : points, badges, club.
- [ ] Un encadreur soumet une activité classée sous un axe avec photo ; l'admin l'approuve (+100 points) ou la rejette avec un motif ; le club suit l'état de ses articles.
- [ ] Le Magazine affiche les actualités officielles et les activités approuvées.
- [ ] Un élève soumet un témoignage à « Paroles aux Élèves », publié après modération.
- [ ] Un visiteur filtre l'agenda par région, club et type ; un encadreur y ajoute ses événements.
- [ ] Un visiteur regarde les capsules vidéo par axe ; l'admin les ajoute depuis sa console.
- [ ] Un visiteur lit et télécharge les magazines et guides en PDF, avec les 3 derniers magazines à la une.
- [ ] Un élève passe un quiz de 15 questions à 5 secondes par question ; 12 bonnes réponses ou plus donnent les points et le badge, une seule fois par quiz.
- [ ] Le Hall of Fame affiche le Top 3 par région des clubs, des élèves et des encadreurs.
- [ ] La carte du Togo affiche les vrais clubs actifs et leur score par région.
- [ ] Un encadreur commente un article (+10 points, avec plafond quotidien) ; le club reçoit une notification sur le site et répond ; l'admin peut retirer un commentaire.
- [ ] L'admin attribue un badge d'excellence et voit les chiffres clés (clubs, membres, articles en attente).
- [ ] Les pages Club Santé présentent vision, but, mission, objectifs, slogans, mot du promoteur et partenaires.

## Hors scope (pour l'instant)

- **Défis inter-clubs** : le bouton « Défier un autre club », le puzzle, les mots fléchés et le calcul
  mental. C'est un projet à part entière, à spécifier une fois les quiz stabilisés.
- **Rapports de dépistage MNT** et leurs +15 points par fiche : données de santé de mineurs, soumises à
  des exigences légales renforcées (voir Contraintes), et incitation à produire de fausses fiches.
- **Concours national Génie Imhotep** : certificat officiel et lots jusqu'à 1 million FCFA annoncés sur
  le site. Les lots exigent des règles et une protection contre la triche qu'un quiz libre n'a pas.
- **Commentaires des élèves et toute messagerie privée**, pour protéger les mineurs.
- Notifications en temps réel, email ou SMS d'engagement : un simple compteur sur le site suffit.
- Changement de club par l'élève lui-même (l'admin le fait), compte club partagé.
- Statistiques avancées, exports, classements sur plusieurs saisons.
- Application mobile, mode hors ligne, mode sombre, autres langues que le français.

## Vocabulaire du domaine

| Terme              | Définition                                                                                                  |
| ------------------ | ----------------------------------------------------------------------------------------------------------- |
| Club               | Club Santé d'un établissement scolaire. Entité collective, sans mot de passe (Q3).                          |
| Élève              | Membre d'un club, qui a un Passeport. Appartient à un seul club à la fois.                                  |
| Encadreur          | Enseignant qui anime un club, avec son compte personnel. Aussi appelé animateur ou responsable dans le CDC. |
| Admin              | Membre de l'équipe nationale.                                                                               |
| Passeport Santé    | Page personnelle de l'élève : points et badges.                                                             |
| Axe                | Une des 7 thématiques de santé qui classent articles, vidéos et quiz (Q1).                                  |
| Région             | Découpage servant à la carte, aux filtres et aux classements (Q2).                                          |
| Activité           | Article de terrain publié par un club, soumis à modération.                                                 |
| Paroles aux Élèves | Témoignages d'élèves, soumis à modération.                                                                  |
| Modération         | Validation par l'admin avant toute publication d'un article ou témoignage.                                  |
| Point              | Unité de score. Chaque gain est une ligne du journal de points (ADR-0004).                                  |
| Badge              | Distinction gagnée par un quiz réussi ou attribuée par l'admin.                                             |
| Hall of Fame       | Classements Top 3 par région, pour les clubs, les élèves et les encadreurs.                                 |
| Génie Imhotep      | Nom du programme de quiz et du futur concours national.                                                     |
| MNT                | Maladies Non Transmissibles.                                                                                |
| DRE, IESG          | Direction Régionale de l'Éducation et son inspection : découpage scolaire utilisé par la carte du site.     |

### Règles de points du MVP

| Événement                                   | Bénéficiaire  | Points                                               |
| ------------------------------------------- | ------------- | ---------------------------------------------------- |
| Inscription d'un élève                      | Club          | +50, annulés si l'élève est retiré comme faux compte |
| Inscription d'un élève                      | Élève         | +20                                                  |
| Quiz réussi (au moins 12/15), première fois | Élève et club | +25 et +10                                           |
| Commentaire d'un encadreur                  | Encadreur     | +10, au plus 5 par jour, annulés si retiré           |
| Activité approuvée                          | Club          | +100                                                 |

## Critères de succès

Valeurs à confirmer avec AIMES-AFRIQUE, trois mois après l'ouverture :

- 100 clubs actifs, soit environ 12 % des 844 clubs annoncés sur le site.
- 2 000 élèves inscrits, dont la moitié a passé au moins un quiz.
- Modération : un article attend moins de 48 heures, en médiane.
- Aucun incident touchant les données d'un mineur.
- Pages publiques utilisables sur un téléphone d'entrée de gamme en 3G (affichage principal en moins de 4 s).

## Contraintes connues

- **Budget et délai** : non communiqués (Q10, Q14).
- **Mineurs** : la plupart des élèves le sont. Le consentement peut venir de leur représentant légal
  (loi n° 2019-014, art. 4, définition du consentement). Le texte ne fixe pas d'âge (Q8).
- **Formalités** : la mise en service exige un récépissé de l'IPDCP, délivré sous un mois, prorogeable
  une fois (art. 6). Le traitement ne peut pas démarrer avant. Une demande d'avis ou d'autorisation
  peut s'y substituer selon les cas (art. 8 et 9) : à vérifier avec un juriste.
- **Hébergement hors du Togo** : c'est un transfert vers un pays tiers, à signaler d'abord à l'IPDCP,
  qui rend un avis motivé (art. 28 à 30).
- **Données de santé** : interdites par principe, sauf exceptions (art. 21, 22 et 24). Le MVP n'en
  collecte aucune.
- **Droits des personnes** : accès, opposition, rectification, effacement (art. 39 et suivants).
- **Appareils** : surtout des téléphones Android modestes, avec une connexion lente ou coûteuse.
- **Contenus** : les contenus de santé doivent être validés médicalement par l'équipe nationale.
- **Langue** : français, en tutoyant partout.

## Questions ouvertes

Le développement peut avancer sur l'hypothèse retenue. Un changement de réponse plus tard demandera
de reprendre les specs indiquées.

| #   | Question                                                                                                                                                                       | Hypothèse retenue                                                                                                                                                                                  | Impacte       |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| Q1  | Les 7 axes du CDC (Éducation pour la santé, Eau et hygiène…) et les 7 univers du site (Académie Génie Imhotep, TV & Médias…) sont différents. Lesquels classent les contenus ? | Les axes du CDC classent articles, vidéos et quiz. Les univers restent une vitrine sur l'accueil. Liste en base, modifiable sans code.                                                             | 006, 009, 011 |
| Q2  | 6 régions sanitaires dans le CDC, 7 DRE sur la carte du site (Plateaux Est et Ouest). Lequel fait foi ?                                                                        | Les 7 DRE : la carte existe déjà et le découpage est scolaire. Le Top 3 se fait donc sur 7 régions.                                                                                                | 003, 012, 013 |
| Q3  | Le CDC parle d'une console du club, sans dire qui s'y connecte.                                                                                                                | Pas de compte club partagé : les encadreurs du club y accèdent avec leur compte personnel.                                                                                                         | 001, 003      |
| Q4  | Comment un élève sans email se connecte-t-il et récupère-t-il son mot de passe ?                                                                                               | Identifiant choisi et mot de passe, email facultatif. Un encadreur de son club réinitialise le mot de passe.                                                                                       | 001, 004      |
| Q5  | Les 844 clubs affichés sur le site existent-ils vraiment ? Faut-il les importer, ou s'enregistrent-ils eux-mêmes ?                                                             | Ils s'enregistrent eux-mêmes. Les chiffres du site sont provisoires. Un import se traiterait à part.                                                                                               | 003, 013      |
| Q6  | L'admin valide-t-il chaque nouveau club ? Le CDC ne le dit pas.                                                                                                                | Oui, sinon n'importe qui peut créer un club et en gonfler le score.                                                                                                                                | 003           |
| Q7  | L'inscription immédiate à +50 points permet de gonfler un score avec de faux comptes.                                                                                          | Règle du CDC conservée, avec une limite d'inscriptions par adresse réseau et le retrait par l'encadreur, qui annule les points.                                                                    | 004           |
| Q8  | Quel consentement pour un élève mineur et pour les photos d'élèves ?                                                                                                           | Case cochée à l'inscription (l'élève confirme l'accord de son parent ou tuteur) et attestation d'autorisation par l'encadreur pour chaque photo. À faire valider par un juriste avant l'ouverture. | 004, 006      |
| Q9  | Qui est responsable du traitement au sens de la loi, et qui fait la démarche auprès de l'IPDCP ?                                                                               | AIMES-AFRIQUE. Aucune donnée réelle d'élève avant le récépissé.                                                                                                                                    | Ouverture     |
| Q10 | Quel hébergeur et quel budget mensuel ?                                                                                                                                        | Un serveur virtuel unique (site, API, PostgreSQL), à confirmer selon le budget et Q9.                                                                                                              | 002           |
| Q11 | Qui fournit et valide les quiz, les vidéos (chaîne YouTube ?) et les PDF ?                                                                                                     | L'équipe nationale, via la console admin. Les vidéos sont sur YouTube. Contenus de test clairement signalés d'ici là.                                                                              | 009, 010, 011 |
| Q12 | Peut-on repasser un quiz ? 5 secondes suffisent-elles sur un réseau lent ou pour un jeune lecteur ?                                                                            | Reprises libres, points une seule fois. Tolérance réseau de 2 secondes côté serveur, 5 secondes affichées.                                                                                         | 011           |
| Q13 | Les élèves peuvent-ils commenter ?                                                                                                                                             | Non dans le MVP, pour protéger les mineurs.                                                                                                                                                        | 014           |
| Q14 | Y a-t-il une date d'ouverture imposée (rentrée, événement) ?                                                                                                                   | Aucune : l'ordre de `TASKS.md` suit les dépendances puis la valeur.                                                                                                                                | Priorités     |
| Q15 | Le CDC dit que le score du club inclut les points de ses élèves, mais le barème donne déjà +10 et +50 au club.                                                                 | Le score du club est la somme de son seul journal, selon le barème, sans ajouter les points personnels des élèves.                                                                                 | 005, 012      |
| Q16 | Un enseignant peut-il encadrer plusieurs clubs ? Un établissement peut-il avoir plusieurs clubs ?                                                                              | Non aux deux dans le MVP. L'admin arbitre lors de la validation.                                                                                                                                   | 003           |

## Écarts assumés avec le cahier des charges

| CDC                                         | Décision                                                      | Raison                                            |
| ------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------- |
| SPA React 18, état local, Firebase possible | TanStack Start, FastAPI, PostgreSQL (ADR-0001, ADR-0002)      | Choix du porteur du projet ; site existant        |
| Charte émeraude et teal                     | Vert et bleu du logo, charte déjà en place (`docs/DESIGN.md`) | Demande du porteur du projet                      |
| Animations `motion/react`                   | Animations CSS et `SiteMotion` existantes, sans dépendance    | Rendu validé, moins de poids sur les téléphones   |
| Vidéos importées par l'admin                | Lien YouTube enregistré par l'admin (ADR-0005)                | Débit adaptatif et aucun coût de diffusion        |
| Notifications en temps réel                 | Compteur mis à jour au chargement des pages                   | Suffisant pour le MVP                             |
| Points de l'encadreur sans limite           | Plafond de 5 commentaires rémunérés par jour                  | Sinon le classement se gagne en commentant à vide |
