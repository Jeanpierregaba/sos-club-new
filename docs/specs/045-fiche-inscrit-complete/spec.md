# 045 — Fiche d'un inscrit : modification, registre complet et parcours

## Objectif

Donner à l'équipe nationale, depuis la liste des inscrits (`/admin/inscrits`), une fiche complète de chaque élève et
de chaque encadreur. Elle sert au suivi et au support : corriger une faute dans un nom, répondre à « où sont mes
points ? », voir où en est la certification.

La fiche existe déjà (specs 015, 017, 018). Elle montre l'identité, le profil, l'historique du compte et les
50 dernières lignes de points. Elle permet aussi d'imposer un pseudonyme, de suspendre, de réactiver et de
réinitialiser le mot de passe. Cette spec ajoute :

- la **modification de l'identité et du profil** ;
- le **registre complet des points**, paginé ;
- le **parcours** de la personne : quiz validés, toutes les tentatives, certification et contenus.

Décisions du porteur du projet (2026-11-20) :

| Sujet          | Décision                                                                                      |
| -------------- | --------------------------------------------------------------------------------------------- |
| Modifiable     | Identité (prénom, nom, e-mail, téléphone) et profil ; l'établissement reste hors périmètre.   |
| Droits         | Droit « inscrits » : consulter pour lire, modifier pour changer ; collaborateurs nationaux.   |
| Points         | Le registre complet, paginé, filtrable par semestre.                                          |
| Parcours       | Quiz validés, toutes les tentatives, certification et activité de contenu.                     |

## Comportement attendu

### A. Ouvrir la fiche

1. Dans la liste des inscrits, toute la ligne d'un inscrit est cliquable (pas seulement son nom) et ouvre sa fiche.
2. La fiche garde ses sections actuelles. Elle s'organise en onglets :
   - **Profil** : identité, profil d'élève ou d'encadreur, actions du compte ;
   - **Points** ;
   - **Quiz** ;
   - **Certification** ;
   - **Contenus** ;
   - **Historique** du compte.
3. L'onglet choisi se retrouve dans l'adresse (`?onglet=quiz`), pour revenir au même endroit.
4. Un collaborateur (rôle admin) n'a pas de fiche d'inscrit : il se gère depuis l'écran des collaborateurs.

### B. Modifier l'identité et le profil

1. Un collaborateur national qui a le droit `inscrits:modifier` choisit « Modifier » dans l'onglet Profil.
2. Il peut changer :
   - pour tous : le **prénom**, le **nom**, l'**e-mail** et le **téléphone** ;
   - pour un élève : la **classe** ;
   - pour un encadreur : la **fonction** (et sa précision si « autre »), la **discipline** et la **commune**.
3. Il saisit un **motif** (10 à 500 caractères) et enregistre.
4. Les mêmes règles qu'à l'inscription s'appliquent :
   - prénom et nom obligatoires ;
   - e-mail valide et unique, obligatoire pour un encadreur, facultatif pour un élève ;
   - téléphone au format accepté, obligatoire pour un encadreur ;
   - commune obligatoire pour un encadreur.
5. La modification est journalisée : qui, quand, le motif et la liste des champs changés. Les anciennes et nouvelles
   valeurs de la classe, de la fonction, de la discipline et de la commune y figurent. L'e-mail, le téléphone, le
   prénom et le nom n'y figurent pas en clair : seul le nom du champ est noté.
6. L'événement apparaît dans l'historique du compte : « Profil modifié par l'équipe ».
7. Si quelqu'un d'autre a modifié le compte entre-temps (l'inscrit lui-même ou un autre collaborateur),
   l'enregistrement est refusé avec « Ce profil a changé entre-temps. Recharge la page. ».

Le pseudonyme garde son action à part (« Imposer un pseudonyme », spec 017). L'établissement ne change pas ici.

### C. Points

1. L'onglet Points montre les totaux (semestre en cours, total) et **toutes** les lignes du registre de la personne,
   les plus récentes d'abord, 50 par page.
2. Chaque ligne porte : la date, le motif (libellé du barème), les points, la part du club, le semestre, le club
   bénéficiaire, et pour une correction ou une annulation son motif et son auteur. Une ligne annulée est marquée.
3. Un filtre choisit un semestre ou « Tout l'historique ».
4. Un lien « Corriger dans le registre » ouvre le registre de l'équipe (spec 036) filtré sur cette seule personne
   (par son identifiant technique, pas par une recherche de texte), pour un collaborateur national qui a
   `points:modifier`.

### D. Quiz

1. En tête, un résumé : nombre de quiz validés (distincts), de tentatives terminées, d'échecs, et de points gagnés
   par les quiz.
2. **Quiz validés** : chaque quiz réussi au moins une fois, avec son titre, son axe, son parcours (jeux ou
   certification), la date de la première réussite, le meilleur score et les points obtenus.
3. **Toutes les tentatives**, 25 par page, les plus récentes d'abord : quiz, parcours, date, score sur le nombre de
   questions, réussie ou non, durée, points, et « essai » pour une tentative d'essai. Une tentative en cours ou
   abandonnée est marquée comme telle.
4. Filtres : parcours (tous, jeux, certification) et résultat (toutes, réussies, échouées).
5. Les questions et les réponses données ne sont pas affichées.

### E. Certification

1. La progression : les 20 places du parcours (spec 029), chacune réussie (avec la date et le quiz) ou non.
2. Les badges obtenus, avec leur nom, leur palier et leur date.
3. Les certificats : numéro, état (valide, révoqué, remplacé), date de délivrance, et le motif d'une révocation.
4. Un lien ouvre le suivi de la certification (spec 043) pour un collaborateur qui en a le droit.

### F. Contenus

1. Les contenus dont la personne est l'auteur, 25 par page, les plus récents d'abord : type (article, actualité,
   événement, rapport, commentaire, partage…), titre ou début du texte, état de modération, date de création et de
   publication.
2. Un filtre par type et par état.
3. Pas de lien vers la file de modération : elle ne s'ouvre pas sur un élément précis. Écart noté à la relecture
   (2026-11-20), à reprendre si la file reçoit un lien direct.

## Critères d'acceptation

### Accès

- [x] **Lecture.** Étant donné un collaborateur national avec `inscrits:consulter`, alors il lit les points, les quiz,
      la certification et les contenus d'un élève ou d'un encadreur.
- [x] **Refus.** Un collaborateur sans `inscrits:consulter`, un collaborateur de DRE, un élève, un encadreur et un
      visiteur non connecté sont refusés sur chaque nouvelle route.
- [x] **Modification réservée.** Un collaborateur avec `inscrits:consulter` mais sans `inscrits:modifier` ne peut
      pas modifier : la route est refusée et le bouton n'apparaît pas.
- [x] **Pas de collaborateur.** La modification d'un compte de collaborateur est refusée.
- [x] **Pas de cache.** Les réponses portent `Cache-Control: no-store`.

### Modification

- [x] **Identité.** Étant donné un élève, quand l'équipe change son prénom, son nom et sa classe avec un motif, alors
      ils sont enregistrés et l'historique montre « Profil modifié par l'équipe » avec le motif.
- [x] **Encadreur.** Étant donné un encadreur, quand l'équipe change sa fonction, sa discipline et sa commune, alors
      elles sont enregistrées.
- [x] **Règles.** Un prénom vide, un e-mail invalide, un e-mail déjà pris par un autre compte, un téléphone invalide,
      un encadreur sans e-mail, sans téléphone ou sans commune, une fonction « autre » sans précision, et un motif de
      moins de 10 caractères sont refusés avec un message clair. Rien n'est enregistré.
- [x] **Champs hors profil.** Une classe envoyée pour un encadreur, ou une fonction pour un élève, est refusée.
- [x] **Rien à changer.** Une modification sans aucun changement est refusée (« Rien n'a changé. ») et n'écrit rien
      au journal.
- [x] **Journal sans donnée en clair.** L'entrée du journal ne contient ni l'e-mail, ni le téléphone, ni le prénom,
      ni le nom, anciens ou nouveaux.
- [x] **Concurrence.** Étant donné une version périmée, alors la modification est refusée (409) et rien n'est écrit.

### Points

- [x] **Registre complet.** Étant donné un élève avec 60 lignes, alors la page 1 en montre 50 et la page 2 en montre
      10, les plus récentes d'abord.
- [x] **Filtre semestre.** Le filtre ne garde que les lignes du semestre choisi.
- [x] **Seulement les siennes.** Aucune ligne d'un autre inscrit ni du compte collectif d'un club n'apparaît.
- [x] **Corrections.** Une correction et une annulation apparaissent avec leur motif ; la ligne annulée est marquée.

### Quiz

- [x] **Quiz validés.** Étant donné un élève qui a échoué puis réussi un quiz, puis réussi un autre, alors la liste
      des quiz validés en compte 2, avec la date de première réussite et le meilleur score.
- [x] **Tentatives.** Toutes les tentatives apparaissent, y compris les échecs, les essais et une tentative en cours,
      chacune marquée.
- [x] **Filtres.** Les filtres par parcours et par résultat s'appliquent.
- [x] **Résumé.** Le nombre de quiz validés, de tentatives, d'échecs et les points des quiz correspondent aux données.
- [x] **Pas de réponses.** Aucune question ni réponse n'est renvoyée.

### Certification

- [x] **Progression.** Étant donné un élève qui a réussi les places 1 à 3, alors les 20 places sont renvoyées, dont 3
      réussies avec leur date.
- [x] **Badges et certificats.** Les badges obtenus et les certificats (valide, révoqué avec son motif) apparaissent.
- [x] **Sans parcours.** Une personne qui n'a rien joué obtient 20 places non réussies, aucun badge, aucun
      certificat.

### Contenus

- [x] **Liste.** Les contenus de la personne apparaissent avec leur type, leur titre et leur état, y compris les
      brouillons et les refusés. Aucun contenu d'un autre auteur.
- [x] **Filtres.** Les filtres par type et par état s'appliquent.

### Liste

- [x] **Ligne cliquable.** Un clic n'importe où sur la ligne d'un inscrit ouvre sa fiche ; le lien du nom reste
      accessible au clavier.

## Cas limites et erreurs

- **Inscrit introuvable** : 404 « Compte introuvable. » sur chaque route.
- **Nom changé après un certificat** : le certificat déjà délivré garde le nom de sa délivrance (spec 029). Pour le
  corriger, l'équipe le révoque et le fait délivrer de nouveau, comme aujourd'hui. L'onglet Certification le rappelle.
- **E-mail retiré d'un élève** : accepté (l'e-mail d'un élève est facultatif). Retiré d'un encadreur : refusé.
- **E-mail changé** : aucun e-mail n'est envoyé ; les sessions de la personne restent ouvertes. L'adresse n'est
  plus considérée comme confirmée (`email_confirme_le` remis à vide). Le journal garde l'empreinte SHA-256 de la
  nouvelle adresse, sans l'adresse en clair : on peut vérifier après coup vers quelle adresse un compte a été dirigé.
- **Visiteur, invité, collaborateur** : pas de fiche d'inscrit modifiable ni d'onglets. La modification d'un visiteur
  ou d'un collaborateur est refusée (409), celle d'un invité est introuvable (404) ; les routes de lecture renvoient
  404 pour eux.
- **Points des quiz** : le résumé et les quiz validés donnent le montant du gain initial ; une annulation ou une
  correction ultérieure apparaît dans l'onglet Points.
- **Compte suspendu ou ancien élève** : la fiche reste lisible et modifiable.
- **Élève sans tentative, sans contenu, sans point** : chaque onglet montre un état vide clair.
- **Quiz supprimé ou archivé** : la tentative garde son titre.
- **Beaucoup de tentatives** (plusieurs centaines) : pagination côté API, jamais toute la liste d'un coup.
- **Espaces autour des valeurs** : retirés, comme à l'inscription.

## Hors périmètre

- Le changement d'établissement par l'équipe (il touche à l'affiliation au club et aux effectifs).
- La modification de l'identifiant de connexion, du rôle ou du pseudonyme (déjà une action à part).
- La correction des points depuis la fiche : elle reste dans le registre (spec 036).
- Le détail des questions et des réponses d'une tentative.
- L'accès des collaborateurs de DRE à ces onglets.
- La modification de la fiche d'adhésion (spec 030), qui garde son droit `fiches_eleves`.

## Questions ouvertes

Aucune : les quatre questions ont été tranchées le 2026-11-20.
