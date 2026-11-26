# 044 — Partages : carte de classement et partages d'articles vérifiés (R17)

## Objectif

Couvrir R17 du PRD (« Partage du classement en visuel, republication et partage d'articles avec preuve vérifiée »),
avec la décision Q23 : un partage ne rapporte des points qu'après vérification par un modérateur.

- L'élève et l'encadreur font connaître leur rang sur les réseaux sociaux avec une carte image, sans donnée
  sensible (CDC élève § 7, CDC encadreur § 11).
- Ils relaient les articles publiés du site et partagent les leurs. Le partage rapporte des points une fois
  vérifié, jamais sur un simple clic (CDC élève § 5.3).

Décisions du porteur du projet (2026-11-19) :

| Sujet      | Décision                                                                                  |
| ---------- | ----------------------------------------------------------------------------------------- |
| Preuve     | Le lien de la publication, vérifié par un modérateur dans la file de modération.          |
| Plafonds   | Règles du CDC, et 3 déclarations par jour au plus.                                        |
| Encadreurs | Mêmes règles et mêmes points que les élèves (barème « proposé » de la grille).            |
| Carte      | Contenu du CDC ; le club seulement si la personne le choisit ; aussi pour les encadreurs. |

## Comportement attendu

### A. Partager mon classement

1. Depuis « Mon espace » ou `/hall-of-fame`, l'élève ou l'encadreur classé choisit « Partager mon classement ».
2. Il choisit la vue :
   - **national** ou **DRE**, dans tous les cas ;
   - **club**, s'il a un club ;
   - et, pour chaque vue, le **semestre en cours** ou l'**historique**.
3. Il coche ou non « Afficher mon club ». La case est décochée par défaut.
4. L'aperçu montre la carte. Elle porte :
   - le **nom affiché** : le pseudonyme de l'élève, le prénom et l'initiale du nom de l'encadreur ;
   - le **rang** dans la vue, le **nombre de classés** et les **points de la période** ;
   - le **niveau** (Club, DRE et son nom, National) et la **période** (libellé du semestre ou « Depuis le début ») ;
   - la mention « Clubs Santé SOS Docteur TV » et le logo ;
   - le **nom du club**, seulement si la case est cochée.
5. Un semestre en cours est marqué « Classement provisoire au <date> ». Seul un palmarès publié par la clôture
   (spec 037) est présenté comme officiel.
6. Il télécharge l'image (PNG), ou la partage avec le partage natif du téléphone quand le navigateur le permet.
7. Le partage du classement ne rapporte aucun point (PRD, barème).

### B. Partager un article vérifié

Deux actions, sur la page d'un article publié (`/articles/<adresse>`), réservées aux élèves et aux encadreurs
actifs :

- **Republier un article du site** : un article publié dont la personne n'est pas l'auteur. +10, une seule fois
  par article et par personne, quel que soit le réseau.
- **Partager mon article** : un article personnel publié dont la personne est l'auteur. +50 par réseau distinct,
  une seule fois par réseau et par article. Les réseaux sont Facebook, Instagram, TikTok et LinkedIn.

Le parcours :

1. La personne publie l'article sur son réseau, avec les boutons de partage de la page ou à la main.
2. Elle revient sur la page et choisit « J'ai partagé cet article ». Elle choisit le réseau et colle le lien de
   sa publication.
3. La déclaration entre dans la file de modération, au type « Partage ». Le modérateur voit :
   - l'article ;
   - le réseau ;
   - le lien, qu'il ouvre lui-même ;
   - l'auteur, comme pour les autres contenus.
4. Le modérateur approuve, ou refuse avec un motif. Pas de « demander une correction » : une preuve fausse se
   redéclare.
5. À l'approbation, les points sont crédités au registre (`eleve.republication`, `eleve.partage`,
   `encadreur.republication`, `encadreur.partage`). La part du club suit la règle des demi-points (ADR-0012). La
   personne est notifiée.
6. Au refus, la personne lit le motif. Aucun point. Le réseau ou l'article reste disponible pour une nouvelle
   déclaration.
7. « Mes partages », dans « Mon espace », liste ses déclarations avec leur état : en attente, approuvée, refusée et
   son motif.

### C. Admin

- La file de modération reçoit le type « Partage ». Le filtre par type le montre.
- Le droit de décider suit le moteur (ADR-0009) :
  - un nouveau droit de domaine `partages:approuver` ;
  - le périmètre DRE du collaborateur s'applique.
- Les points de partage apparaissent au registre comme les autres. Une correction motivée reste possible
  (spec 036).

## Critères d'acceptation

### Carte de classement

- [x] **Contenu de la carte.** Étant donné un élève classé, quand il demande la carte de la vue nationale du
      semestre, alors l'image porte son pseudonyme, son rang, le nombre de classés, ses points du semestre, « National »,
      le libellé du semestre et la mention du programme. Elle ne porte ni son nom, ni son prénom, ni son établissement,
      ni son identifiant, ni ses coordonnées.
- [x] **Club en option.** Étant donné la case « Afficher mon club » décochée, alors le nom du club n'apparaît pas.
      Cochée, il apparaît.
- [x] **Encadreur.** Étant donné un encadreur classé, alors sa carte porte son prénom et l'initiale de son nom,
      jamais son nom complet.
- [x] **Semestre en cours.** Étant donné le semestre en cours, alors la carte porte « Classement provisoire ». La
      vue historique porte « Depuis le début ».
- [x] **Personne non classée.** Étant donné un élève sans point dans la vue choisie, alors la carte est refusée avec
      un message clair. Aucune image d'un rang inexistant n'est produite.
- [x] **Vue club sans club.** Étant donné un élève sans club, alors la vue « club » est refusée.
- [x] **Accès.** Étant donné une personne connectée, alors elle n'obtient que sa propre carte. Un visiteur, un
      admin ou une personne non connectée sont refusés.
- [x] **Aucun point.** Le partage d'une carte ne crée aucune ligne au registre.

### Partages d'articles

- [x] **Republication.** Étant donné un élève actif et un article publié dont il n'est pas l'auteur, quand il
      déclare une republication avec un lien valide, alors une déclaration « en attente » entre dans la file. Aucun point
      n'est crédité avant la décision.
- [x] **Approbation.** Étant donné une déclaration de republication approuvée, alors l'élève reçoit +10 au
      registre, avec la part de son club, et une notification.
- [x] **Son article.** Étant donné l'auteur d'un article publié, quand ses partages sur Facebook puis sur Instagram
      sont approuvés, alors il reçoit deux fois +50.
- [x] **Une fois par réseau.** Une deuxième déclaration sur Facebook pour le même article est refusée tant que la
      première est en attente ou approuvée.
- [x] **Une fois par article.** Une deuxième republication du même article est refusée tant que la première est en
      attente ou approuvée.
- [x] **Après un refus.** Étant donné une déclaration refusée, alors la personne peut en déclarer une nouvelle pour
      le même réseau ou le même article. La déclaration refusée ne rapporte rien.
- [x] **Plafond quotidien.** Étant donné 3 déclarations le même jour (heure de Lomé), alors la 4ᵉ est refusée avec
      un message clair. Les déclarations refusées comptent dans le plafond.
- [x] **Encadreur.** Étant donné un encadreur actif, alors les mêmes règles s'appliquent, avec
      `encadreur.republication` (+10) et `encadreur.partage` (+50).
- [x] **Article non publié.** Étant donné un article en attente, refusé, dépublié ou un brouillon, alors la
      déclaration est refusée. Un article dépublié entre la déclaration et la décision rend l'approbation impossible ;
      le modérateur refuse.
- [x] **Lien invalide.** Un lien qui n'est pas en `https`, ou dont le domaine ne correspond pas au réseau choisi,
      est refusé. Exemple : un lien `tiktok.com` déclaré pour Facebook.
- [x] **Lien déjà utilisé.** Un lien déjà déclaré dans une déclaration en attente ou approuvée, par la même
      personne ou par une autre, est refusé. Un lien refusé peut être déclaré de nouveau.
- [x] **Confidentialité du lien.** Le lien n'apparaît que dans la file de modération et dans « Mes partages » de son
      auteur, jamais sur une page publique.
- [x] **Droits.** Un visiteur, un élève ou un encadreur suspendu, un encadreur non vérifié ou une personne non
      connectée ne peuvent pas déclarer de partage. Un collaborateur sans `partages:approuver` ne décide pas. Un
      collaborateur de DRE ne voit que les déclarations des auteurs de sa DRE.
- [x] **Concurrence.** Deux décisions simultanées sur la même déclaration ne créditent les points qu'une fois.

## Cas limites et erreurs

- **Article dépublié après l'approbation du partage.** Les points restent acquis, comme pour les articles
  (spec 023). Une annulation passe par une correction motivée au registre.
- **Compte suspendu entre la déclaration et la décision.** Comme pour tout contenu du moteur, l'approbation est
  refusée tant que le compte est suspendu ; le modérateur attend ou refuse.
- **Élève qui change de club.** La part du club va au club du moment de l'approbation (ADR-0012).
- **Lien qui ne s'ouvre plus** (publication supprimée, compte privé). Le modérateur refuse avec un motif.
- **Plafond des déclarations en attente.** Comme pour tout contenu du moteur, 3 déclarations au plus attendent leur
  vérification à la fois : au-delà, la personne attend une décision, même un autre jour. La page de l'article le dit.
- **Même publication sous une autre écriture.** `www.` ou `m.`, « / » final, ancre ou paramètres de suivi (`utm_…`,
  `fbclid`…) ne changent pas la publication : le contrôle du lien déjà utilisé compare le lien ainsi réduit. Un lien
  court (`fb.watch`, `vm.tiktok.com`, `lnkd.in`) et le lien long d'une même publication restent distincts : le
  modérateur en est le dernier contrôle.
- **Lien d'un bouton de partage** (`facebook.com/sharer…`, `linkedin.com/sharing…`) ou page d'accueil d'un réseau :
  refusé, ce n'est pas une publication.
- **Lien très long, ou avec des paramètres de suivi.** 500 caractères au plus. Le lien est gardé tel que saisi,
  sans espaces autour.
- **Navigateur sans partage natif.** Seul le téléchargement de l'image est proposé.
- **Semestre clos sans semestre en cours.** La vue « semestre » est refusée ; seule l'historique est proposée.
- **Rang à égalité.** La carte affiche le rang partagé, comme `/hall-of-fame`.

## Hors périmètre

- Une vérification automatique des publications : aucune API des réseaux sociaux, aucune visite automatique des liens.
- Les points du partage de classement : aucun bonus n'est fixé.
- Le partage des actualités de club, des événements et des ressources de la bibliothèque : seuls les articles
  (spec 023) entrent dans R17.
- D'autres réseaux que Facebook, Instagram, TikTok et LinkedIn. WhatsApp, X et YouTube pourront être ajoutés par
  une petite tâche si l'équipe le demande.
- Le partage de la carte numérique de membre (R15) et celui du certificat (spec 029).
- La détection des partages suspects (R22).

## Questions ouvertes

Aucune : les quatre questions ont été tranchées le 2026-11-19. Les montants restent ceux de la grille ; ceux des
encadreurs sont « proposés » et réglables dans l'admin (barème).
