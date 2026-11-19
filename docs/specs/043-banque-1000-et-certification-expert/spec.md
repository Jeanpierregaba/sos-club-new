# 043 — Banque de 1 000 questions, certification de niveau expert et suivi des candidats

## Objectif

La certification Génie Imhotep fonctionne (specs 029 et 034) : 20 places en 5 thématiques de 4 quiz, 10 questions
par quiz, 10/10 exigé. Mais ses 20 places n'ont pas encore de vrais quiz : la base de développement n'a que des quiz
« [Test] ». L'équipe ne voit pas non plus qui suit le parcours.

Cette spec :

1. **complète la banque** : les 78 QCM du document « Quiz Santé – 78 questions » (Clubs Santé SOS Docteur TV,
   15 thématiques) rejoignent les 922 QCM du « Jeu Quiz Santé ». La banque compte alors **1 000 questions** ;
2. **remplit les 20 places** de la certification avec 200 questions puisées dans la banque, **de niveau expert** :
   10 questions par quiz, toutes différentes ;
3. ajoute au back office un **suivi des certifications** : les candidats, leur progression, l'entonnoir des
   20 quiz et les chiffres par DRE.

Sources :

- [spec 029](../029-certification/spec.md) et [spec 034](../034-gamification-eleve-4-niveaux/spec.md) pour les
  règles du parcours ;
- [spec 031](../031-quiz-sante-sans-compte/spec.md) pour la banque des 922 QCM ;
- document « Quiz_sante_78_questions_Clubs_Sante » (2026-11-19) ;
- [RULES](../../RULES.md).

## Comportement attendu

### 1. La banque de 1 000 questions

- Les 78 QCM entrent dans la banque comme un **lot 7**, en 15 quiz, un par thématique du document. Chaque QCM a
  3 propositions ; la bonne réponse est celle que le document met en gras.
- Comme les 922 autres, ces 15 quiz restent **dépubliés** : ils servent de réserve et ne se jouent pas tels quels.
- Chaque thématique est rangée dans un axe :

| Thématiques du document                                                                              | Axe                    |
| ---------------------------------------------------------------------------------------------------- | ---------------------- |
| IST, VIH, VPH, grossesses précoces et non désirées, violences basées sur le genre                    | Santé sexuelle (EVSS)  |
| Drogue, addiction aux écrans, santé mentale, paludisme, nutrition, obésité, vision, audition, bouche | Santé et environnement |
| Accidents de la voie publique                                                                        | Sport et secourisme    |

- Le chargement est **idempotent** : un quiz déjà présent (même titre) n'est ni dupliqué ni modifié.

### 2. Les 20 quiz de certification, niveau expert

- Les 5 thématiques de la certification suivent les axes de la banque, dans l'ordre des badges :

| Places  | Badge                               | Axe de la banque                             |
| ------- | ----------------------------------- | -------------------------------------------- |
| 1 à 4   | Ambassadeur Santé Junior            | AIMES-AFRIQUE et SOS Docteur TV (lot 1)      |
| 5 à 8   | Pair Éducateur Santé et Citoyenneté | Club Santé et Académie Génie Imhotep (lot 2) |
| 9 à 12  | Sentinelle de la Prévention         | Santé et environnement (lots 3 et 5)         |
| 13 à 16 | Champion de la Santé et EVSS        | Santé sexuelle, EVSS (lot 4)                 |
| 17 à 20 | Maître Génie Imhotep                | Sport, secourisme et santé publique (lot 6)  |

- **Niveau expert** : les questions viennent d'abord des réserves des **10 défis Expert** des quiz Jeux (spec 034).
  Exemples : rayonnement panafricain, grand podium national, choléra, Code de l'enfant, mutilations génitales,
  drépanocytose, maladies tropicales négligées, morsures de serpents, pyramide sanitaire, grand défi ultime.
- Quand l'axe n'a pas 40 questions expert, on complète avec le **reste du même lot**. C'est le cas des places 1 à 8,
  qui n'ont qu'un défi Expert chacune (20 questions).
- Chaque quiz a **10 questions**, et les **200 questions sont toutes différentes**.
- La sélection est écrite dans un fichier de données relisible, dans le dépôt, avant d'être chargée.
- Chaque quiz porte le titre de sa place et de sa thématique (par exemple « Génie Imhotep 13 — Champion de la Santé
  et EVSS (1/4) »), l'axe de sa thématique et la mention « Niveau expert ».
- Les quiz sont publiés au nom d'AIMES-AFRIQUE, comme les 100 quiz Jeux : les questions viennent de ses documents
  officiels.
- Une place déjà occupée par un quiz publié qui n'est pas un contenu de test est **laissée telle quelle**. Un quiz
  de test qui occupe une place est dépublié pour laisser la place.
- Les règles du parcours ne changent pas : 10 questions de 20 secondes, 10/10, arrêt à la première erreur, places
  dans l'ordre, sans correction, +50 par place, +500 par badge, +1 000 pour le certificat.
- Les 200 questions **restent aussi dans les quiz Jeux** : s'entraîner aux Jeux, avec correction, prépare la
  certification.

### 3. Le suivi des certifications (back office)

Une page « Suivi » dans Admin > Certification, réservée aux collaborateurs qui ont le droit de consulter les quiz.
Un collaborateur de DRE ne voit que sa DRE.

**Les candidats**

- Un candidat est un élève ou un encadreur qui a commencé au moins une partie de certification.
- La liste montre pour chacun :
  - son nom, son rôle, son club, son établissement et sa DRE ;
  - le nombre de places validées sur 20 et ses badges ;
  - la place en cours, et le nombre de tentatives sur cette place ;
  - le nombre total de tentatives ;
  - la date de début et la dernière activité ;
  - certifié ou non, avec le numéro du certificat.
- Filtres : DRE, club, rôle, état (en cours, inactif depuis 30 jours, certifié). Recherche par nom.
- La liste est paginée et triée par dernière activité.
- Le nom et le prénom d'un élève ne sont montrés, et cherchables, qu'à un collaborateur national dont la double
  authentification est active, comme les autres lectures nominatives sensibles. Les autres voient son pseudonyme,
  comme dans le suivi des clubs. Les encadreurs sont nommés pour tous.
- La même règle et le même périmètre DRE valent pour les listes des certificats et des badges délivrés de
  l'onglet Certification : un collaborateur de DRE n'y voit que sa DRE.
- L'export CSV de la liste est réservé, comme l'export des inscrits, aux collaborateurs nationaux qui ont le droit
  « inscrits : exporter ». Il demande une finalité et il est inscrit au journal.

**L'entonnoir des 20 quiz**

- Pour chaque place : le nombre de candidats qui l'ont tentée et qui l'ont réussie, le taux de réussite des
  tentatives et le nombre moyen de tentatives avant la réussite.

**Les chiffres**

- En tête : candidats, candidats actifs sur les 30 derniers jours, badges délivrés (par badge), certifiés.
- Par DRE : candidats, badges, certifiés.
- Par semaine, sur les 12 dernières semaines : nouveaux candidats et nouveaux certifiés.

## Critères d'acceptation

- [x] Après la migration, la banque compte 1 000 QCM : 922 du Jeu Quiz Santé et 78 du nouveau document, en 15 quiz
      dépubliés du lot 7.
- [x] Chaque QCM du lot 7 a 3 propositions, et sa bonne réponse est celle mise en gras dans le document. Le fichier
      de données en contient exactement 78.
- [x] Relancer la migration sur une base qui a déjà le lot 7 ne crée ni ne modifie rien.
- [x] Les places 1 à 20 ont chacune un quiz de certification publié, de 10 questions.
- [x] Les 200 questions sont toutes différentes. Chacune vient de la banque, et de l'axe de sa thématique.
- [x] Les places 9 à 20 n'ont que des questions des réserves des défis Expert. Les places 1 à 8 en ont 20 par
      thématique, complétées par le même lot.
- [x] Un quiz de test qui occupait une place est dépublié. Un vrai quiz publié sur une place reste en place, et
      cette place n'est pas remplie.
- [x] Un élève joue la place 1, réussit à 10/10 et gagne +50 ; la place 2 s'ouvre.
- [x] Le suivi liste un élève dès sa première partie de certification, avec ses places validées, sa place en
      cours, ses tentatives et sa dernière activité.
- [x] Les filtres (DRE, club, rôle, état) et la recherche réduisent la liste. L'export CSV reprend les mêmes
      colonnes et les mêmes filtres ; il est refusé (403) sans le droit « inscrits : exporter » ou hors du périmètre
      national, et chaque export est journalisé avec sa finalité.
- [x] Un collaborateur de DRE, ou national sans double authentification, voit le pseudonyme des élèves, jamais
      leur nom, ni dans le suivi ni dans les listes des certificats et des badges.
- [x] Un collaborateur de DRE ne voit que les candidats et les chiffres de sa DRE ; sans le droit de consulter
      les quiz, il reçoit un refus 403.
- [x] L'entonnoir donne, pour chaque place, les candidats arrivés, ceux qui ont réussi, le taux de réussite et la
      moyenne de tentatives avant la réussite.
- [x] Les chiffres comptent les candidats, les actifs sur 30 jours, les badges par badge et les certifiés, au
      total, par DRE et par semaine.
- [x] Les joueurs sans compte et les parties d'essai des collaborateurs n'apparaissent pas dans le suivi.
- [ ] Le site : la page « Suivi » est utilisable à 375 px de large.

## Cas limites et erreurs

- **Aucun candidat** : la page le dit (« Personne n'a encore commencé la certification »), et l'entonnoir montre
  des zéros.
- **Place sans quiz publié** (laissée à un vrai quiz dépublié depuis, par exemple) : l'entonnoir l'affiche comme
  « pas de quiz publié ».
- **Encadreur candidat** : il est compté et filtrable par rôle. Sans club, son club et sa DRE sont ceux de son
  rattachement principal, ou « sans club ».
- **Élève qui a changé de club ou d'établissement** : il est rangé sous son club et sa DRE actuels.
- **Ancien élève** : il reste dans la liste, marqué « ancien élève ».
- **Certificat révoqué** : le candidat n'est plus compté parmi les certifiés ; un certificat réémis compte une
  seule fois.
- **Question corrigée par l'équipe dans un quiz Jeux** : la copie dans la certification n'est pas modifiée. Chaque
  quiz a ses propres questions, que l'équipe corrige dans l'éditeur des quiz.
- **Base sans la banque** (celle des tests) : la migration ne crée ni le lot 7 ni les quiz de certification.
- **Grand nombre de candidats** : la liste reste paginée et l'export CSV est limité comme les autres exports du back
  office (`export_lignes_max`).

## Hors périmètre

- Les explications des 78 nouvelles questions : le document n'en donne pas.
- L'usage des 78 nouvelles questions dans de nouveaux quiz Jeux.
- Un tirage aléatoire des questions de certification à chaque tentative : les 10 questions d'une place sont fixes,
  comme aujourd'hui.
- Les questions qui bloquent le plus les candidats (statistiques par question).
- Les relances par e-mail ou notification des candidats inactifs.
- Les fascicules associés à chaque place.

## Questions ouvertes

Aucune. Décisions du 2026-11-19 :

- **Niveau expert** : puiser d'abord dans les lots des 10 défis Expert des Jeux.
- **Thématiques** : une par axe de la banque, dans l'ordre des badges.
- **Recouvrement** : les 200 questions restent dans les quiz Jeux.
- **Suivi** : liste des candidats, entonnoir par quiz et chiffres par DRE (sans les questions bloquantes).
