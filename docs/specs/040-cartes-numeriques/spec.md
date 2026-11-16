# 040 — Cartes numériques (R15)

Sources : PRD R15, Q8 et Q30 ; `docs/cdc/eleve.md` § 3 (carte membre) ; `docs/cdc/encadreur.md` § 17 (carte
encadreur) ; `docs/cdc/admin.md` § 10 (cartes et QR codes) ; spec 033 (un encadreur sur un seul club) ; spec 034
(carte de membre de l'espace élève : pseudonyme, club, étoiles, statut Gold).

Décisions du porteur du projet (2026-11-16) :

- la carte porte le **prénom et le nom** de son titulaire ; la page de vérification n'affiche aucun nom ;
- **pas de photo** dans cette spec : la photo de profil, avec consentement et modération (Q8), viendra plus tard ;
- la vérification passe **par le QR code seulement**, avec un code secret impossible à deviner ; pas de saisie du
  numéro ;
- le statut est **déduit** du compte et de l'affiliation ou du rattachement, et l'**équipe** peut aussi suspendre une
  carte pour fraude, avec un motif, puis la réactiver.

## Objectif

L'élève et l'encadreur reçoivent une carte numérique officielle des Clubs Santé SOS Docteur TV, qu'ils peuvent
télécharger pour la garder sur leur téléphone ou l'imprimer. Un responsable d'établissement, un partenaire ou un
organisateur d'événement peut scanner son QR code pour vérifier qu'elle est valide, sans rien apprendre de plus que le
statut, le numéro et le club (Q30).

## Comportement attendu

### 1. Délivrance

1. Un **élève** reçoit sa carte dès la création de son compte. Sans affiliation active, la ligne du club affiche
   « Non affilié » ; elle affiche son club dès que l'affiliation est confirmée.
2. Un **encadreur** reçoit sa carte quand l'équipe le vérifie ; elle n'est valide que s'il est rattaché à un club
   (rattachement actif).
3. Un visiteur ou un collaborateur de l'admin n'a pas de carte.
4. Chaque carte a un **numéro unique**, attribué une fois pour toutes : il ne change pas quand le club change et n'est
   jamais réutilisé, même après la suppression du compte. Un compte n'a qu'une carte.
5. Chaque carte a aussi un **code de vérification** secret, imprimé seulement dans le QR code.
6. Les comptes existants reçoivent leur carte au déploiement, selon les mêmes règles.
7. La carte ne rapporte aucun point (PRD).

### 2. Statut

Une carte est **valide** ou **non valide**. Elle est non valide quand :

- le compte est suspendu ou supprimé ;
- pour un encadreur : il n'est plus vérifié, ou il n'a plus de rattachement actif ;
- l'équipe l'a suspendue.

Une carte redevient valide d'elle-même quand la cause disparaît (compte réactivé, nouveau rattachement), sauf une
suspension par l'équipe, qui doit être levée par l'équipe. Le numéro et le code restent les mêmes.

Pour un élève, la fin de l'affiliation ne rend pas la carte non valide : son club redevient « Non affilié ».

### 3. « Ma carte » dans l'espace

1. L'élève retrouve sa carte sur son tableau de bord (la carte de la spec 034, qui gagne le numéro et le statut) et
   sur une page **Ma carte membre** ; l'encadreur sur une page **Ma carte encadreur** et un raccourci de son tableau
   de bord.
2. La page montre un aperçu de la carte :
   - l'intitulé « Carte membre – Club Santé SOS Docteur TV » ou « Carte encadreur – Club Santé SOS Docteur TV » ;
   - le prénom et le nom ;
   - le rôle : « Membre », « Président du club » ou « Encadreur » ;
   - le numéro de carte ;
   - l'établissement ;
   - le club ou « Non affilié » ;
   - la date de délivrance ;
   - le QR code.
3. Elle affiche le **statut** du moment. Une carte non valide l'indique avec la marche à suivre (« Rapproche-toi de
   ton encadreur » ou « Contacte l'équipe nationale »), sans détailler un motif de fraude.
4. Deux boutons : **Télécharger en PDF** (format carte, pour l'impression) et **Télécharger en image** (PNG, pour le
   téléphone). Le fichier est produit à la demande avec les informations du moment.
5. Un avertissement rappelle que la carte porte ton nom : ne la publie pas sur les réseaux.
6. Une carte non valide ne se télécharge pas.

### 4. Vérification par le QR code

1. Le QR code mène à une page publique `/carte/<code>`, sans connexion.
2. La page affiche seulement :
   - le type de carte (membre ou encadreur) ;
   - le numéro ;
   - le club, ou « Non affilié » ;
   - le statut **Valide** ou **Non valide** ;
   - la date et l'heure de la vérification.
     Aucun nom, pseudonyme, établissement d'élève, coordonnée, date de naissance ni motif.
3. Un code inconnu affiche « Cette carte n'existe pas », avec la même allure qu'une carte non valide.
4. La page n'est pas indexée par les moteurs de recherche, et la réponse n'est pas mise en cache.
5. Le nombre de vérifications par adresse IP est plafonné, pour empêcher de tester des codes en masse.

### 5. Côté admin

1. Dans la fiche d'un élève ou d'un encadreur (module « Inscrits »), l'équipe voit le
   numéro, le statut, sa cause, la date de délivrance et l'historique (délivrance, suspensions, réactivations).
2. Avec le droit de modifier du module, elle peut **suspendre** une carte avec un motif (10 à 200 caractères) et la
   **réactiver** avec un motif. Chaque action est journalisée.
3. Le titulaire reçoit une notification : « Ta carte a été suspendue par l'équipe des Clubs Santé » ou « Ta carte est
   de nouveau valide ». Elle ne nomme pas le collaborateur.

## Critères d'acceptation

### Délivrance et numéro

- [x] Étant donné un nouvel élève, quand son compte est créé, alors il a exactement une carte valide, « Non affilié ».
- [x] Étant donné un élève dont l'affiliation est confirmée, alors sa carte affiche son club, sans nouveau numéro.
- [x] Étant donné un encadreur en attente de vérification ou sans rattachement actif, alors il n'a pas de carte
      valide ; une fois vérifié et rattaché, il en a une.
- [x] Un visiteur ou un collaborateur n'a pas de carte (la page « Ma carte » répond 404).
- [x] Deux cartes n'ont jamais le même numéro ni le même code, même sous créations simultanées.
- [x] Un numéro n'est jamais réattribué, même après suppression du compte.
- [x] Après la migration, chaque élève et chaque encadreur vérifié et rattaché a sa carte.

### Statut

- [x] Un compte suspendu rend la carte non valide ; réactivé, elle redevient valide avec le même numéro.
- [x] Un encadreur dont le rattachement est retiré a une carte non valide ; rattaché de nouveau, elle redevient valide.
- [x] La fin de l'affiliation d'un élève remet « Non affilié » sans rendre la carte non valide.
- [x] Une carte suspendue par l'équipe reste non valide après la réactivation du compte, jusqu'à ce que l'équipe la
      réactive.

### Espace et téléchargement

- [x] L'élève et l'encadreur ne voient que leur propre carte.
- [x] Le PDF et l'image contiennent le prénom, le nom, le numéro, le club et un QR code qui mène à la page de
      vérification de cette carte.
- [x] Une carte non valide ne se télécharge pas (409).

### Vérification

- [x] Étant donné un code valide, la page publique affiche le type, le numéro, le club et « Valide », et la réponse ne
      contient ni nom, ni pseudonyme, ni coordonnée, ni date de naissance.
- [x] Étant donné une carte non valide, la page affiche « Non valide », sans motif.
- [x] Un code inconnu renvoie « Cette carte n'existe pas ».
- [x] La réponse porte `Cache-Control: no-store` et la page `noindex`.
- [x] Au-delà du plafond, les vérifications d'une même adresse IP sont refusées (429).
- [x] Le numéro imprimé ne permet pas de retrouver une carte : la vérification n'accepte que le code.

### Admin

- [x] Avec le droit de modifier, l'équipe suspend puis réactive une carte avec un motif ; chaque action est
      journalisée et notifie le titulaire sans nommer le collaborateur.
- [x] Sans ce droit, ou avec un motif de moins de 10 caractères, c'est refusé.

## Cas limites et erreurs

- **Élève qui change d'établissement ou de club** : la carte suit, même numéro, même code.
- **Président** : sa carte porte « Président du club » tant qu'il l'est ; après une passation, « Membre ».
- **Encadreur vérifié qui perd son seul rattachement** : sa carte devient non valide, sa page « Ma carte » le dit.
- **Encadreur jamais rattaché** : sa carte n'est pas encore valide ; « Ma carte encadreur » explique qu'elle le
  devient avec le rattachement.
- **Compte supprimé** : la carte reste en base, non valide ; le QR affiche « Non valide ».
- **Club suspendu ou fermé** : la carte de l'élève reste valide et affiche le club tant que l'affiliation est active ;
  celle de l'encadreur suit son rattachement.
- **Image partagée publiquement** : le QR n'expose que le statut, le numéro et le club ; l'avertissement de la page
  rappelle que le nom figure sur la carte.
- **Nom avec accents ou très long** : le PDF et l'image restent lisibles (coupure propre, polices avec accents).
- **Code mal formé dans l'adresse** : même réponse qu'un code inconnu.
- **Ancien élève** (clôture de l'année, spec 034) : sa carte « Membre » reste valide, même numéro ; seule une
  suspension du compte ou par l'équipe la rend non valide (décidé le 2026-11-16).
- **Suspension par l'équipe d'une carte déjà non valide** : acceptée et journalisée ; la carte reste non valide après
  le retour de la cause automatique.

## Hors périmètre

- La photo sur la carte (spec à part, avec consentement et modération, Q8).
- La saisie manuelle d'un numéro de carte sur la page de vérification.
- Le renouvellement du code d'une carte (perte, partage) : à prévoir si le besoin apparaît.
- Le partage d'une version publique de la carte (R17).
- L'historique des vérifications et l'alerte sur les QR invalides (R22).
- Le verso de la carte et une période de validité datée : la carte vaut tant que son statut est valide (Q30).
- La mention Gold et les étoiles sur la carte téléchargée : elles restent sur le tableau de bord (spec 034).
- La demande de correction d'une information par l'encadreur : il passe par son profil ou l'équipe.

## Questions ouvertes

Aucune : les quatre questions ont été tranchées le 2026-11-16.
