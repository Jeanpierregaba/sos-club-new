# PRD — Product Requirements Document

Sources, notées CDC ci-dessous :

- le [cahier des charges initial](cahier-des-charges.md) ;
- les quatre cahiers des charges reçus le 2026-11-04 : [espace administrateur](cdc/admin.md) (CDC admin),
  [compte élève](cdc/eleve.md) (CDC élève), [espace Club Santé et président](cdc/club-president.md)
  (CDC club) et [espace encadreur](cdc/encadreur.md) (CDC encadreur).

Les quatre CDC du 2026-11-04 priment sur le cahier des charges initial. Quand le PRD et un CDC
diffèrent, le PRD fait foi. Les écarts sont listés en fin de document, et les hypothèses encore à
confirmer sont les questions ouvertes. L'ordre de construction est dans la [roadmap](ROADMAP.md).

## Nom du projet

Club Santé SOS Docteur TV : plateforme nationale interactive des Clubs Santé du Togo, sous le
parrainage d'AIMES-AFRIQUE.

## Problème résolu

Les clubs santé scolaires sensibilisent les élèves à l'hygiène, à la nutrition, à la santé sexuelle,
aux maladies non transmissibles et à l'environnement. Leurs actions restent locales et peu visibles,
les ressources validées médicalement sont difficiles à trouver, et rien ne valorise durablement
l'engagement des élèves et des enseignants. La plateforme donne un même lieu pour apprendre, publier
les actions de terrain, documenter l'activité des clubs et se mesurer entre élèves, entre encadreurs et
entre clubs.

Promesse faite à l'élève (CDC élève) : « Apprends. Participe. Partage. Progresse. Fais briller ton Club
Santé ! »

## Utilisateurs cibles

| Profil        | Qui                                                                           | Ce qu'il veut accomplir                                                                                    | Niveau technique                   |
| ------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| Visiteur      | Grand public, parent, partenaire ; avec ou sans compte léger                  | Découvrir les clubs, l'agenda, les vidéos ; jouer aux quiz sans points ; commenter après modération        | Variable                           |
| Élève         | Collégien ou lycéen, souvent mineur, avec ou sans club                        | Apprendre, réussir des quiz, se certifier, publier, gagner des points, faire briller son club              | Téléphone, parfois sans email      |
| Président     | Élève désigné pour gérer l'espace officiel de son club, avec son compte élève | Présenter le club, publier en son nom, proposer des événements, déposer des rapports, inviter les membres  | Téléphone                          |
| Encadreur     | Enseignant ou accompagnateur rattaché à un ou plusieurs clubs                 | Suivre ses clubs et ses élèves, publier, animer des forums, déposer les rapports d'activités, se certifier | Bureautique simple, téléphone      |
| Club          | Entité collective d'un établissement, rattachée à une DRE (pas une personne)  | Avoir un espace officiel, un score collectif et un rang DRE et national                                    | Sans objet : géré par le président |
| Collaborateur | Équipe nationale AIMES-AFRIQUE et SOS DOCTEUR TV, avec des droits ciblés      | Valider les comptes, clubs et contenus, piloter les quiz, les points et les récompenses                    | Bureautique                        |

## Parcours principaux

1. **Rejoindre la plateforme** : un élève crée son compte (pseudonyme, classe, établissement,
   consentement) → +100 points de bienvenue et une carte membre « Non affilié » → il demande à rejoindre
   le club de son établissement → l'affiliation est validée → sa carte affiche son club.
2. **Ouvrir l'espace d'un club** : un élève désigné président demande la création de l'espace (nom,
   établissement, DRE, encadreurs associés) → l'admin vérifie le président, l'établissement et
   l'absence de doublon → le club est actif, visible sur la carte, et le président le gère.
3. **Publier** : un élève, un encadreur ou le président (au nom du club) rédige un article avec photos
   → il attend dans la file de modération → l'admin l'approuve (+50 à l'auteur, la moitié au club pour un
   élève affilié), demande une correction ou le refuse avec un motif → l'auteur est notifié.
4. **Apprendre et se certifier** : l'élève réussit un quiz (+50 à +200 selon son niveau, la moitié au club, une seule fois par quiz)
   → il suit le parcours Génie Imhotep (fascicules et 20 quiz obligatoires, à 10/10) → certificat, 5 badges,
   +1 000 points et la moitié au club (spec 034).
5. **Documenter une activité** : l'encadreur ou le président dépose un rapport avec ses justificatifs
   → l'admin l'examine → validé, il crédite le club une seule fois (+50), même si l'autre l'a aussi déposé.
6. **Se mesurer** : chacun voit son rang du semestre et son total historique, au niveau du club, de la
   DRE et national → en fin de semestre, l'admin gèle, contrôle et publie le Top 3 des élèves.
7. **S'informer sans compte** : un visiteur consulte la carte, l'agenda, les vidéos par axe, les
   articles publiés et les ressources.

## Fonctionnalités du MVP

Le MVP correspond au jalon « Ouverture » de la [roadmap](ROADMAP.md) : tout le P0 du CDC admin. Chaque
groupe deviendra une ou plusieurs specs dans `docs/specs/`.

**Déjà livré**

- [x] Un utilisateur se connecte et se déconnecte ; chaque rôle n'accède qu'à ce qui le concerne (spec 001).
- [x] L'espace admin a ses comptes collaborateurs avec droits par module, la double authentification,
      le journal d'audit, l'annuaire et les exports tracés (spec 015, lot 1).

**Socle**

- [ ] Le site public et l'API sont en ligne dans un environnement de préproduction.
- [ ] Les DRE, établissements et axes sont en base et modifiables depuis l'espace admin.
- [ ] Chaque point est une ligne du registre, avec son semestre ; le barème se règle depuis l'espace admin.

**Comptes et clubs**

- [ ] Un élève crée son compte, reçoit une seule fois 100 points de bienvenue et utilise les fonctions
      individuelles sans club.
- [ ] Un encadreur crée son compte ; il n'accède aux données de ses élèves qu'après validation de son
      compte et de son rattachement.
- [ ] Un élève demande la création de l'espace de son club ; l'admin le valide ou le refuse ; un seul
      président actif par club, et la passation conserve tout l'historique.
- [ ] Un élève demande à rejoindre un club ; seule une affiliation validée rapporte des points au club.
- [ ] Un encadreur peut être rattaché à plusieurs clubs ; ses vues sont filtrées club par club.

**Modération et publications**

- [ ] Aucun contenu d'un élève, d'un président ou d'un encadreur n'est visible par un autre utilisateur,
      une API publique, une recherche ou une notification avant son approbation.
- [ ] L'admin approuve, refuse avec motif, demande une correction ou dépublie depuis une file centrale ;
      un auteur ne valide jamais son propre contenu.
- [ ] Une modification d'un contenu publié reste masquée jusqu'à sa validation ; la version approuvée
      reste en ligne d'ici là.
- [ ] Les points de publication et de commentaire ne sont crédités qu'à l'approbation, une seule fois.
- [ ] Chaque utilisateur reçoit sur le site les décisions qui le concernent, avec leur motif.
- [ ] Le président modifie la fiche du club et publie des actualités en son nom, après validation ; les
      membres voient l'espace du club en lecture seule.

**Quiz et certification**

- [ ] Un élève ou un encadreur passe un quiz chronométré par le serveur ; seule la première réussite
      rapporte des points.
- [ ] Aucun encadreur, président ou élève ne peut créer ni modifier un quiz, même par l'API.
- [ ] Le parcours Génie Imhotep compte 20 quiz obligatoires en 5 thématiques, réussis à 10/10, et des
      fascicules ; sa réussite donne un certificat vérifiable, 5 badges et le bonus de certification, une
      seule fois (spec 034).

**Rapports d'activités**

- [ ] L'encadreur et le président déposent un rapport avec ses justificatifs ; seul un rapport validé
      crédite des points, une seule fois par activité.
- [ ] Un rapport validé reste privé ; la publication de son résumé est une décision distincte.

**Classements**

- [x] Élèves et encadreurs ont des classements séparés au niveau du club (privé), de la DRE et national ;
      les clubs ont un classement DRE et national ; chacun montre le semestre en cours et le total historique
      (R13, spec 036 : les classements DRE et national sont publics, celui du club reste réservé à ses membres).
- [ ] En fin de semestre, l'admin gèle le classement, le contrôle, tranche les ex æquo et publie le Top 3
      des élèves ; le semestre suivant repart de zéro (R14).
- [x] L'admin corrige un score par une ligne motivée et journalisée, jamais en modifiant l'historique
      (R13, spec 036 : registre national, correction à double authentification, annulation liée à la ligne d'origine).

## Après l'ouverture (P1 et P2 du CDC admin)

- Cartes numériques de l'élève et de l'encadreur avec QR code de vérification.
- Agenda : propositions d'événements, invitations des membres et réponses.
- Partage du classement en visuel, republication et partage d'articles avec preuve vérifiée.
- Forums prémodérés et co-animation entre encadreurs.
- Comptes visiteurs légers : avancés et livrés par la spec 030 (quiz « jeux » sans points), commentaires restant à faire.
- Capsules vidéo, campagnes, pages institutionnelles.
- Détection avancée des anomalies, analyses comparatives, relances, chatbot SOS.

## Hors scope (pour l'instant)

- **Défis inter-clubs** : le bouton « Défier un autre club », le puzzle, les mots fléchés et le calcul
  mental. C'est un projet à part entière, à spécifier une fois les quiz stabilisés.
- **Rapports de dépistage MNT** et leurs +15 points par fiche : données de santé de mineurs, soumises à
  des exigences légales renforcées (voir Contraintes), et incitation à produire de fausses fiches.
- **Gestion des lots en argent** de la certification (« jusqu'à 1 million FCFA ») et des dotations du
  Top 3 : elles relèvent d'un règlement distinct, hors de la plateforme. La plateforme ne gère que des
  points virtuels, des certificats et des palmarès.
- **Messagerie privée** et tout échange direct entre utilisateurs. Les invitations passent par des
  notifications internes, sans coordonnées.
- **Notifications par email ou SMS aux élèves**, et notifications en temps réel : un centre de
  notifications sur le site suffit.
- Application mobile, mode hors ligne, mode sombre, autres langues que le français.

## Vocabulaire du domaine

| Terme                       | Définition                                                                                                                                                           |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Club                        | Club Santé d'un établissement, rattaché à une DRE. Entité collective, sans mot de passe, avec un espace officiel.                                                    |
| Espace du club              | Espace officiel du club : consulté par ses membres, géré par son président, validé par l'admin.                                                                      |
| Élève                       | Titulaire d'un compte élève. Peut être sans club ; membre d'un seul club à la fois.                                                                                  |
| Président                   | Élève qui gère l'espace de son club avec son compte élève. Un seul président actif par club, nommé ou remplacé par l'admin.                                          |
| Affiliation                 | Lien entre un élève et le club de son établissement, confirmé par un encadreur du club ou l'équipe (spec 033). Seul un élève affilié rapporte des points à son club. |
| Encadreur                   | Enseignant ou accompagnateur, avec son compte et son espace propres. Ne gère pas l'espace du club.                                                                   |
| Rattachement                | Lien entre un encadreur vérifié et le club de son établissement, posé automatiquement. Un seul club par encadreur (spec 033).                                        |
| Statut du club              | En constitution, actif (3 encadreurs + 21 élèves), en régularisation (15 jours sous le seuil) ou suspendu. Calculé par l'API (ADR-0011).                             |
| Visiteur                    | Personne sans compte, ou avec un compte léger : ni points, ni carte, ni certification.                                                                               |
| Collaborateur               | Membre de l'équipe nationale avec un profil dans l'espace admin et des droits ciblés (ADR-0008).                                                                     |
| Responsable DRE             | Collaborateur dont les droits sont limités aux clubs d'une DRE.                                                                                                      |
| Pseudonyme                  | Nom public d'un élève. Seule identité affichée hors de l'espace admin.                                                                                               |
| Carte membre                | Carte numérique de l'élève : numéro d'adhérent unique, club ou « Non affilié », statut. La carte encadreur est son équivalent.                                       |
| Axe                         | Un des 7 axes d'intervention des Clubs Santé (page `/les-7-axes`) ; ils classent articles, vidéos, quiz, forums, événements et rapports (Q1).                        |
| DRE, IESG                   | Direction régionale de l'éducation et son inspection : découpage qui sert à la carte, aux filtres et aux classements (Q2).                                           |
| Modération                  | Validation d'un contenu par un collaborateur habilité avant toute visibilité. États : brouillon, en attente, à corriger, refusé, publié, dépublié.                   |
| Article                     | Publication (texte et photos) d'un élève, d'un encadreur ou du président au nom du club, publiée après modération.                                                   |
| Rapport d'activité          | Compte rendu d'une activité du club avec ses justificatifs. Validé pour les points, privé par défaut. Existe aussi en rapport mensuel et bilan semestriel.           |
| Point                       | Unité de score. Chaque gain ou retrait est une ligne du registre `mouvement_points`, avec son semestre (ADR-0004).                                                   |
| Semestre                    | Période de classement. Le classement du semestre repart de zéro ; le total historique est conservé.                                                                  |
| Badge                       | Distinction : les 5 badges de la certification, ou une distinction attribuée par l'admin.                                                                            |
| Certification Génie Imhotep | Parcours de 20 quiz obligatoires en 5 thématiques et de fascicules, sanctionné par un certificat vérifiable.                                                         |
| Top 3 semestriel            | Grand Champion, Vice-Champion et Jeune Talent du semestre : les 3 élèves qui ont le plus de points, au niveau national.                                              |
| Hall of Fame                | Page des classements et des palmarès, dont celui des compétitions Génie Imhotep passées.                                                                             |
| MNT                         | Maladies non transmissibles.                                                                                                                                         |

### Barème des points

Cahier des charges « Espace Élève — Gamification et récompenses » du 2026-11-10 ([spec 034](specs/034-gamification-eleve-4-niveaux/spec.md),
ADR-0012), qui remplace la spec 022 pour l'élève et le club. Les montants sont réglés dans l'espace admin, à partir
de ces valeurs. Un point n'est crédité qu'une fois l'action validée, une seule fois par action.

**Règle du club** : pour chaque gain d'un élève, son Club Santé reçoit exactement la moitié (+5 → +2,5, sans
arrondi), dans la même écriture, si l'affiliation est active et le club en service au moment du crédit. Un
changement d'établissement ne transfère pas les points déjà acquis.

| Parcours de l'élève | Action validée                                         | Élève                           |
| ------------------- | ------------------------------------------------------ | ------------------------------- |
| Certification       | Quiz de certification validé (10/10)                   | +50                             |
| Certification       | Badge (un par thématique, 5)                           | +500                            |
| Certification       | Certificat final                                       | +1 000                          |
| Jeux — quiz         | Quiz Débutant / Intermédiaire / Avancé / Expert réussi | +50 / +100 / +150 / +200        |
| Jeux — étoiles      | Niveau validé : étoile 1 / 2 / 3 / 4                   | +500 / +1 000 / +1 500 / +3 000 |
| Vie du site         | Compte créé et validé                                  | +100                            |
| Vie du site         | Commentaire approuvé                                   | +5                              |
| Vie du site         | Republication vérifiée, par article et réseau          | +10                             |
| Vie du site         | Article personnel approuvé et publié                   | +50                             |
| Vie du site         | Partage vérifié de son article, par réseau             | +50                             |
| Vie du site         | Bonne réponse à la question du jour                    | +20                             |

Les actions des encadreurs gardent le barème de la spec 022 (montants « proposés », Q22) :

| Action validée                               | Encadreur        |
| -------------------------------------------- | ---------------- |
| Compte validé                                | +100 (proposé)   |
| Commentaire approuvé                         | +5 (proposé)     |
| Republication d'un article du site, vérifiée | +10 (proposé)    |
| Article personnel approuvé                   | +50 (proposé)    |
| Partage de son article, par réseau, vérifié  | +50 (proposé)    |
| Quiz réussi, première fois                   | 0 (proposé)      |
| Certification Génie Imhotep                  | +1 000 (proposé) |
| Sujet de forum validé                        | +30 (proposé)    |
| Discussion animée et attestée                | +50 (proposé)    |
| Réponse utile validée à un élève             | +10 (proposé)    |
| Événement approuvé dans l'agenda             | +30 (proposé)    |
| Rapport d'activité validé                    | +100 (proposé)   |
| Rapport mensuel validé                       | +75 (proposé)    |
| Bilan semestriel validé                      | +200 (proposé)   |
| Projet d'élèves accompagné et réalisé        | +150 (proposé)   |
| Élève accompagné jusqu'à la certification    | +50 (proposé)    |
| Mobilisation vérifiée de 10 participants     | +50 (proposé)    |

Le compte collectif du club garde ses propres actions, hors de la règle des 50 % : rapport d'activité validé (+50,
proposé), bilan semestriel validé (+100, proposé). « Quel axe est fait pour toi ? » ne rapporte rien : 7 questions,
3 participations par élève sur la vie du compte (spec 032). Restent à valider (spec 034, section 9) : les intitulés
des 5 thématiques, les paramètres des quiz Jeux, le renouvellement annuel, les plafonds et la preuve des partages.

Ne rapportent aucun point : la carte membre, une invitation, le partage d'un classement, un contenu en
attente, refusé ou dépublié pour infraction. Le score d'un club est la somme de ses seules lignes, sans
y ajouter les points personnels de ses membres. Les points personnels du président restent ceux de son
compte élève.

## Critères de succès

Valeurs à confirmer avec AIMES-AFRIQUE, trois mois après l'ouverture :

- 100 clubs actifs, soit environ 12 % des 844 clubs annoncés sur le site.
- 2 000 élèves inscrits, dont la moitié a passé au moins un quiz.
- Modération : un contenu attend moins de 48 heures, en médiane.
- Aucun incident touchant les données d'un mineur, et aucun contenu non approuvé visible publiquement.
- Pages publiques utilisables sur un téléphone d'entrée de gamme en 3G (affichage principal en moins de 4 s).

## Contraintes connues

- **Budget et délai** : non communiqués (Q10, Q14).
- **Mineurs** : la plupart des élèves le sont, et un président l'est aussi. Le consentement peut venir
  de leur représentant légal (loi n° 2019-014, art. 4, définition du consentement). Le texte ne fixe pas
  d'âge (Q8).
- **Formalités** : la mise en service exige un récépissé de l'IPDCP, délivré sous un mois, prorogeable
  une fois (art. 6). Le traitement ne peut pas démarrer avant. Une demande d'avis ou d'autorisation
  peut s'y substituer selon les cas (art. 8 et 9) : à vérifier avec un juriste.
- **Hébergement hors du Togo** : c'est un transfert vers un pays tiers, à signaler d'abord à l'IPDCP,
  qui rend un avis motivé (art. 28 à 30).
- **Données de santé** : interdites par principe, sauf exceptions (art. 21, 22 et 24). Le MVP n'en
  collecte aucune ; les forums orientent les échanges sensibles vers un professionnel.
- **Droits des personnes** : accès, opposition, rectification, effacement (art. 39 et suivants).
- **Appareils** : surtout des téléphones Android modestes, avec une connexion lente ou coûteuse.
- **Contenus** : les contenus de santé doivent être validés médicalement par l'équipe nationale.
- **Langue** : français, en tutoyant partout.

## Questions ouvertes

Le développement peut avancer sur l'hypothèse retenue. Un changement de réponse plus tard demandera
de reprendre les specs indiquées (codes de la [roadmap](ROADMAP.md)). Les questions tranchées par les
CDC du 2026-11-04 sont gardées pour mémoire.

| #   | Question                                                                                                     | Hypothèse retenue                                                                                                                                                                                                                                                                                                                                                                                                                   | Impacte          |
| --- | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| Q1  | Les 7 axes du CDC et les 7 univers du site sont différents. Lesquels classent les contenus ?                 | **Validé (2026-11-04)** : Les 7 axes d'intervention de la page `/les-7-axes` classent articles, vidéos, quiz, forums, événements et rapports ; ils remplacent les axes de santé publique du CDC initial. Les univers restent une vitrine. Liste en base, modifiable sans code (spec 016).                                                                                                                                           | R1, R6, R9, R20  |
| Q2  | Quelle liste de DRE fait foi, et comment les établissements y sont-ils rattachés ?                           | Les 7 DRE de la carte du site, dans une structure configurable (CDC admin § 4.2). La DRE d'un club vient de son établissement, jamais d'un champ libre.                                                                                                                                                                                                                                                                             | R1, R13          |
| Q3  | Qui se connecte à l'espace d'un club ?                                                                       | **Tranché (CDC club)** : le président, avec son compte élève. Aucun compte partagé.                                                                                                                                                                                                                                                                                                                                                 | R4, R8           |
| Q4  | Comment un élève sans email récupère-t-il son mot de passe ?                                                 | Identifiant choisi et mot de passe, email facultatif. Un encadreur rattaché à son club, ou l'admin, réinitialise le mot de passe ; l'action est journalisée.                                                                                                                                                                                                                                                                        | R2, R5           |
| Q5  | Les 844 clubs affichés sur le site existent-ils vraiment ? Faut-il les importer ?                            | **Remplacé (spec 033, 2026-11-10)** : un club naît seul à la première affiliation sur son établissement et s'active à 3 encadreurs + 21 élèves confirmés. La carte affiche des chiffres réels ; l'équipe marque les clubs « déclarés sur le terrain ».                                                                                                                                                                              | R4               |
| Q6  | L'admin valide-t-il chaque nouveau club ?                                                                    | **Remplacé (spec 033, 2026-11-10)** : non, l'activation est automatique au seuil 3 + 21, calculée par l'API (ADR-0011).                                                                                                                                                                                                                                                                                                             | R4               |
| Q7  | L'inscription à +50 points au club permet de gonfler un score avec de faux comptes.                          | **Tranché à nouveau (spec 034, 2026-11-11)** : le club reçoit la moitié de chaque gain d'un élève, seulement si son affiliation est active et validée au moment du crédit. Le compte est crédité à l'inscription, avant la confirmation de l'affiliation : sa moitié ne va donc à aucun club. Une fois par élève, pas de nouveau bonus après un changement d'école.                                                                 | R13              |
| Q8  | Quel consentement pour un élève mineur et pour les photos d'élèves (articles, carte membre) ?                | Case cochée à l'inscription (l'élève confirme l'accord de son parent ou tuteur), attestation de l'auteur pour chaque photo, contrôle par le modérateur. Photo de carte facultative. À valider par un juriste. Spec 030 : la fiche d'adhésion en ligne nomme un parent ou tuteur responsable (nom et contact), qui remplace la signature de la fiche papier.                                                                         | R2, R6, R15      |
| Q9  | Qui est responsable du traitement au sens de la loi, et qui fait la démarche auprès de l'IPDCP ?             | AIMES-AFRIQUE. Aucune donnée réelle d'élève avant le récépissé.                                                                                                                                                                                                                                                                                                                                                                     | Ouverture        |
| Q10 | Quel fournisseur de VPS, dans quel pays, et quel budget mensuel ?                                            | VPS retenu par le porteur du projet, un seul serveur pour la preprod et la prod (ADR-0007). Fournisseur et pays à confirmer selon le budget et Q9.                                                                                                                                                                                                                                                                                  | Préproduction    |
| Q11 | Qui fournit et valide les quiz, les fascicules, les vidéos et les PDF ?                                      | Les gestionnaires pédagogiques de l'équipe nationale, depuis l'espace admin. Vidéos sur YouTube. Contenus de test clairement signalés d'ici là.                                                                                                                                                                                                                                                                                     | R9, R10, R20     |
| Q12 | Peut-on repasser un quiz ? 5 secondes suffisent-elles sur un réseau lent ?                                   | Reprises libres, points une seule fois. Paramètres réglables par parcours (CDC admin § 7). Jeux : 15 questions, 20 secondes plus 2 de tolérance, réussite à 12/15, 10 parties par jour. Certification (spec 034) : 10 questions de 20 secondes, 10/10, arrêt à la première erreur ou au premier temps dépassé, sans plafond de tentatives.                                                                                          | R9               |
| Q13 | Les élèves peuvent-ils commenter ?                                                                           | **Tranché (CDC élève)** : oui, après modération, +5 points.                                                                                                                                                                                                                                                                                                                                                                         | R7               |
| Q14 | Y a-t-il une date d'ouverture imposée ?                                                                      | Aucune : l'ordre de la roadmap suit les dépendances puis les priorités du CDC admin.                                                                                                                                                                                                                                                                                                                                                | Priorités        |
| Q15 | Le score du club inclut-il les points de ses élèves ?                                                        | **Tranché (CDC club et encadreur)** : non, le score du club est la somme de ses propres lignes.                                                                                                                                                                                                                                                                                                                                     | —                |
| Q16 | Un encadreur peut-il encadrer plusieurs clubs ? Un établissement peut-il avoir plusieurs clubs ?             | **Amendé (spec 033, 2026-11-10)** : un encadreur n'encadre qu'un club, celui de l'établissement de son profil. Établissement : un seul club.                                                                                                                                                                                                                                                                                        | R3, R4, R5       |
| Q17 | Que veut dire « compte validé » pour un élève, condition des 100 points ?                                    | **Validé (2026-11-04)** : Le compte est actif dès l'inscription, une fois la charte et le consentement acceptés ; les 100 points sont crédités à ce moment. L'admin peut suspendre un compte. Seule l'affiliation passe par une validation.                                                                                                                                                                                         | R2               |
| Q18 | Qui valide l'affiliation d'un élève à un club ? L'admin national seul aurait des milliers de demandes.       | **Validé (2026-11-04)** : L'élève demande, le président confirme, un collaborateur valide : le responsable de la DRE s'il existe, sinon l'admin national. Validation en lot possible.                                                                                                                                                                                                                                               | R5               |
| Q19 | Comment l'admin vérifie-t-il qu'un élève est bien le président de son club ? Quelle durée de mandat ?        | **Amendé (spec 033, 2026-11-10)** : un encadreur affilié au club propose le président parmi les élèves confirmés, puis l'admin valide. Mandat sans durée fixe, jusqu'à une passation décidée par l'admin.                                                                                                                                                                                                                           | R4               |
| Q20 | Quelle identité publique pour un élève ?                                                                     | **Validé (2026-11-04)** : Un pseudonyme unique, choisi à l'inscription, que l'admin peut faire changer. Jamais le nom complet. La liste des membres d'un club n'est visible que de ses membres, de ses encadreurs et de l'admin. Reporté dans `docs/RULES.md`.                                                                                                                                                                      | R2, R8, R13      |
| Q21 | Quelles sont les dates des semestres ?                                                                       | Fixées par l'admin dans l'espace admin avant le premier semestre ; aucune date codée en dur.                                                                                                                                                                                                                                                                                                                                        | R2, R13, R14     |
| Q22 | Quels montants « proposés » du barème sont validés, et quels plafonds anti-spam ?                            | Tous les montants sont réglables ; ils partent des valeurs du barème ci-dessus. Plafonds par défaut : 5 commentaires rémunérés par jour et par personne. Le super-administrateur valide avant la production.                                                                                                                                                                                                                        | R2, R7, R12, R16 |
| Q23 | Comment vérifier un partage sur un réseau social ? Le bouton seul ne suffit pas (CDC élève § 5.3).           | L'auteur fournit le lien de sa publication, un modérateur le vérifie. Un même réseau ne rapporte qu'une fois par article. Activé en P1 seulement.                                                                                                                                                                                                                                                                                   | R17              |
| Q24 | Quelles règles pour les 5 badges, la réussite des quiz et l'éligibilité à la certification ?                 | **Tranché (spec 034, 2026-11-11)** : un badge par thématique de 4 quiz, à 4, 8, 12, 16 et 20 quiz réussis, dans l'ordre : Ambassadeur Santé Junior, Pair Éducateur Santé et Citoyenneté, Sentinelle de la Prévention, Champion de la Santé et EVSS, Maître Génie Imhotep. Réussite d'un quiz à 10/10. Les intitulés des thématiques restent à fournir par l'équipe pédagogique ; seuls les noms des badges se règlent dans l'admin. | R9, R11          |
| Q25 | Le Top 3 est-il seulement national ? Y a-t-il des distinctions par DRE ou par club, et pour les encadreurs ? | Top 3 national des élèves seulement. Distinctions des encadreurs plus tard, si les organisateurs les approuvent.                                                                                                                                                                                                                                                                                                                    | R14              |
| Q26 | Les forums et le chatbot font-ils partie de l'ouverture ?                                                    | Non : forums en P1, après un ADR sur les échanges entre élèves ; chatbot en P2, après un ADR.                                                                                                                                                                                                                                                                                                                                       | R18, R23         |
| Q27 | Les comptes visiteurs font-ils partie de l'ouverture ?                                                       | **Décidé (2026-11-09)** : avancés (spec 030). Compte léger confirmé par un code e-mail ; quiz « jeux » sans points, ni badges, ni certificat, ni club. Les commentaires viendront plus tard.                                                                                                                                                                                                                                        | R19              |
| Q28 | D'où vient la liste des établissements ?                                                                     | **Validé (2026-11-04)** : Import de la liste de l'annuaire du site, vérifiée par l'admin. Un établissement absent est proposé à la création du club et validé avec lui.                                                                                                                                                                                                                                                             | R1, R4           |
| Q29 | Quels formats et tailles pour les justificatifs des rapports ? Les vidéos sont-elles acceptées ?             | Photos JPEG, PNG ou WebP et documents PDF ou Word, avec une taille maximale fixée dans la spec ; vidéos par lien YouTube seulement (ADR-0005).                                                                                                                                                                                                                                                                                      | R12              |
| Q30 | Quelle durée de validité pour les cartes, et quels champs sur la page de vérification du QR code ?           | Validité jusqu'à suspension ou fin d'affiliation. La vérification affiche seulement le statut, le numéro de carte et le club.                                                                                                                                                                                                                                                                                                       | R15              |

## Écarts assumés avec les cahiers des charges

| CDC                                                  | Décision                                                          | Raison                                                   |
| ---------------------------------------------------- | ----------------------------------------------------------------- | -------------------------------------------------------- |
| SPA React 18, état local, Firebase possible          | TanStack Start, FastAPI, PostgreSQL (ADR-0001, ADR-0002)          | Choix du porteur du projet ; site existant               |
| Charte émeraude et teal                              | Vert et bleu du logo, charte déjà en place (`docs/DESIGN.md`)     | Demande du porteur du projet                             |
| Animations `motion/react`                            | Animations CSS et `SiteMotion` existantes, sans dépendance        | Rendu validé, moins de poids sur les téléphones          |
| Vidéos importées par l'admin ou jointes aux rapports | Lien YouTube enregistré (ADR-0005)                                | Débit adaptatif et aucun coût de diffusion               |
| Notifications internes et rappels                    | Centre de notifications sur le site, sans email ni SMS aux élèves | Protection des mineurs, coût, suffisant pour le MVP      |
| Lots jusqu'à 1 million FCFA                          | Gérés hors de la plateforme, selon un règlement                   | Points virtuels et dotations ne doivent pas se confondre |
