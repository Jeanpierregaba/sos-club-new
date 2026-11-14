# 036 — Classements et tableaux de bord (R13)

Source : `docs/PRD.md`, sections « Classements » et « Gamification », Q20 et Q21 ; `docs/cdc/admin.md`, § 8 ;
`docs/ROADMAP.md`, R13 ; specs 017, 021, 022, 033 et 034 ; ADR-0004, ADR-0011 et ADR-0012.

Décisions du porteur du projet (2026-11-14) :

- les classements **publics** sont limités aux niveaux **DRE** et **national**, pour les élèves, les encadreurs et
  les clubs ; le classement interne d'un club reste privé ;
- le classement interne est visible des **membres affiliés**, des **encadreurs rattachés**, du **président** et de
  l'**admin** ;
- chaque classement montre le **semestre en cours** et le **total historique** ; les compteurs annuels de la spec
  034 restent une information distincte et ne sont pas fusionnés avec le semestre ;
- le **gel**, le contrôle, les ex æquo, le Top 3 et les récompenses restent R14 ; R13 ne fait que les classements
  courants et l'historique ;
- le score d'un club est la **somme de `demi_points_club` divisée par 2**, affichée avec sa décimale ; seuls les
  clubs **en service** comptent ;
- les corrections manuelles sont **motivées**, **journalisées**, à **double authentification** et réservées au
  **périmètre national** ;
- aucun classement public n'expose de **nom complet**, d'**e-mail**, de **téléphone** ni d'**identifiant
  utilisateur** : un élève apparaît par son **pseudonyme** et, s'il en a un, son **club**.

Choix de mise en œuvre proposés avec le plan :

- la page publique est `/hall-of-fame` (et non `/classements`), avec une entrée **Classements** dans le menu ;
- un encadreur est affiché par son prénom et l'initiale de son nom, comme les signatures d'articles ;
- une correction manuelle ne crédite aucune part de club ; la part se retire en annulant la ligne d'origine ;
- le registre et les corrections sont nationaux et exigent la double authentification, y compris pour la lecture.

## Objectif

Donner à chaque élève, encadreur et club une place lisible dans le réseau : sa position dans son club, sa DRE et
le pays, pour le semestre en cours et depuis le début. Donner aussi à l'équipe un registre des points consultable
et un moyen de corriger une erreur sans jamais réécrire l'historique.

Cette spec branche les classements sur les points réellement écrits par les specs précédentes (quiz, certification,
articles, commentaires, question du jour, etc.) et sur la part du club de la spec 034. Elle ne crédite plus de
lignes `club.*` : la règle « le club reçoit la moitié » remplace le barème collectif de la spec 022 partout où il
divergue.

## Comportement attendu

### 1. Page publique « Hall of Fame » (`/hall-of-fame`)

1. Depuis le menu **Gamification → Classements**, tout visiteur ouvre `/hall-of-fame`.
2. La page présente trois catégories : **Élèves**, **Encadreurs**, **Clubs**.
3. Pour chaque catégorie, l'utilisateur choisit :
   - le **niveau** : **National** ou une **DRE** (la DRE est obligatoire pour un classement de DRE) ;
   - la **période** : **Semestre en cours** (par défaut) ou **Total historique**.
4. Le tableau affiche le **rang**, le **nom public**, le **club** (pour les élèves et les encadreurs), la **DRE**
   et les **points**. Pour les clubs : le nom du club, son établissement, sa DRE et ses points (avec décimale).
5. Les trois premiers sont mis en avant ; le reste suit dans l'ordre du classement, paginé par 50.
6. Un élève est affiché par son **pseudonyme** et le nom de son club. Un encadreur est affiché par son **prénom**
   suivi de l'**initiale de son nom** et de son club, comme les signatures d'articles. Un club est affiché par son
   nom public et son établissement.
7. Les points d'un élève ou d'un encadreur sont des entiers ; ceux d'un club peuvent avoir une décimale
   (« 2,5 »). Aucun point n'est arrondi.
8. La page indique le libellé et les dates du semestre en cours. Sans semestre en cours, elle affiche un état vide
   explicite (« Aucun semestre en cours ») et laisse le **Total historique** consultable.
9. Un lien renvoie vers le Hall of Fame historique du Génie Imhotep (`/genie-imhotep/hall-of-fame`) ; les deux
   pages ne se confondent pas : l'une classe les Clubs Santé, l'autre raconte les éditions du championnat.
10. Un classement vide affiche un message, jamais une liste inventée ni un zéro de remplissage.

### 2. Classement interne d'un club

1. Dans **Mon espace** (`/mon-espace`), un élève voit un bloc **Classement de mon club** avec deux onglets :
   **Élèves** et **Encadreurs**.
2. Un encadreur rattaché voit le même bloc dans **Mon Club Santé** ; le président le voit dans son espace de club.
3. Le bloc montre le rang, le nom public et les points, pour le **semestre en cours** et le **total historique**.
4. Seuls les **membres affiliés actifs**, les **encadreurs rattachés actifs**, le **président** et l'**admin**
   peuvent lire ce classement. Un autre compte reçoit un refus explicite.
5. Le classement interne ne révèle jamais le nom complet, l'e-mail, le téléphone ni l'identifiant d'un élève ; il
   n'est jamais public et n'apparaît pas dans la page `/hall-of-fame`.
6. La ligne de l'utilisateur courant est mise en évidence (« Toi »).

### 3. Tableau de bord de l'élève et de l'encadreur

1. L'espace d'un élève et celui d'un encadreur montrent, en plus de leurs points :
   - leur **rang dans leur club**, dans leur **DRE** et au **national**, pour le semestre en cours ;
   - les mêmes rangs pour le **total historique**.
2. Ces rangs sont ceux du classement public pour la DRE et le national, et du classement interne pour le club.
3. Le tableau annuel de la spec 034 (rang régional annuel, place dans le club) reste affiché, mais il est
   clairement étiqueté **Année académique** : ce n'est ni le semestre ni le total historique.
4. Un élève sans club n'a pas de rang de club ; il garde ses rangs DRE et national. Un élève sans point n'est pas
   classé et voit « Pas encore classé ».
5. Un visiteur ne voit aucun classement personnel : les classements restent réservés aux élèves et aux encadreurs.

### 4. Admin — registre des points (`/admin/points/registre`)

1. L'admin ouvre l'onglet **Registre** du module **Points et classements**.
2. Le registre liste les lignes de `mouvement_points`, de la plus récente à la plus ancienne : date, bénéficiaire,
   rôle, action, montant, semestre, année, club crédité, auteur du crédit, clé d'idempotence, motif et lien vers
   la ligne annulée s'il y en a un.
3. Il peut filtrer par **période** (semestre, année, dates), **action**, **type de bénéficiaire** (élève,
   encadreur), **club**, **correction** (oui/non) et **recherche** (pseudonyme, identifiant, prénom ou nom).
4. Le registre est paginé par 50, avec le nombre total de lignes.
5. Le registre est **en lecture seule** : aucune ligne ne se modifie ni ne se supprime. Une correction est une
   nouvelle ligne.
6. Le registre montre aussi les lignes négatives d'annulation et de correction, avec leur motif.

### 5. Admin — correction manuelle et annulation

1. Depuis le registre, l'admin peut **annuler une ligne** avec un motif obligatoire. L'annulation écrit une ligne
   négative liée à la ligne d'origine (`annule_id`), copie son montant, son club, sa part de club et son semestre
   d'origine, et ne change jamais la ligne d'origine. Le classement du semestre visé est ainsi corrigé, pas celui
   du semestre où l'annulation est saisie.
2. Depuis le registre ou depuis une fiche de bénéficiaire, l'admin peut **corriger un score** : il choisit un élève
   ou un encadreur, saisit un montant **positif ou négatif** (jamais zéro) et un **motif** obligatoire.
3. La correction écrit une **nouvelle ligne** `admin.correction` avec le montant, le motif, l'auteur, le semestre
   et l'année en cours. Elle ne crédite **aucune part de club** : pour retirer une part de club, l'admin annule la
   ligne d'origine, qui porte déjà cette part.
4. Une correction ne peut pas viser un admin, un visiteur ou un joueur sans compte. Elle peut viser un compte
   suspendu ou un ancien élève, mais la ligne reste alors hors de tout nouveau gain d'élève.
5. Le montant est borné à **±10 000** points. Le motif fait entre **10 et 500 caractères**.
6. Chaque correction et chaque annulation est écrite au journal d'audit avec le bénéficiaire, le montant, le motif,
   le semestre, l'année et le club crédité.
7. Une correction ou une annulation exige le droit `points:modifier`, le **périmètre national** et la **double
   authentification** (droit sensible). Un collaborateur de DRE ne peut ni corriger ni annuler.
8. Une correction envoyée deux fois avec la même clé d'idempotence ne crée qu'une ligne ; la seconde réponse
   renvoie la ligne existante ou un conflit explicite, jamais un doublon.
9. Les corrections et annulations sont refusées si l'action rendrait le total d'un bénéficiaire négatif ? **Non** :
   un total négatif est possible et s'affiche ; le registre explique la correction. Cette règle évite de bloquer
   une correction légitime sur un compte sans point.

### 6. Admin — classements (`/admin/points/classements`)

1. L'admin consulte les mêmes classements que le public, avec les mêmes filtres, dans un onglet **Classements**.
2. Il peut ouvrir le **classement interne d'un club** choisi dans une liste, y compris un club suspendu ou en
   régularisation ; le classement indique alors le statut du club.
3. Les tableaux admin peuvent montrer l'identifiant du bénéficiaire pour permettre une correction ; les tableaux
   publics ne le montrent jamais.
4. L'admin n'a pas de bouton pour geler, publier un Top 3 ou attribuer une récompense : c'est R14.

## Critères d'acceptation

### Classements publics

- [ ] Étant donné des élèves de deux DRE avec des points, quand un visiteur ouvre `/hall-of-fame` en
      **National / Semestre en cours**, alors il voit les élèves classés par points décroissants, avec leur
      pseudonyme, leur club, leur DRE et leurs points.
- [ ] Étant donné la même situation, quand il choisit une **DRE**, alors seuls les élèves dont l'établissement
      actuel est dans cette DRE apparaissent, classés entre eux.
- [ ] Étant donné des encadreurs avec des points, quand il ouvre la catégorie **Encadreurs**, alors les
      classements sont séparés de ceux des élèves et chaque encadreur est affiché par son prénom, l'initiale de son
      nom et son club.
- [ ] Étant donné des clubs en service avec des parts de points, quand il ouvre la catégorie **Clubs**, alors les
      clubs sont classés par score décroissant, avec leur score décimal, leur établissement et leur DRE.
- [ ] Étant donné un club suspendu, en attente ou en constitution, alors il n'apparaît dans aucun classement de
      clubs.
- [ ] Étant donné un club en régularisation dans le délai, alors il apparaît dans le classement de clubs.
- [ ] Étant donné des élèves à égalité de points, alors ils partagent le même rang et l'ordre d'affichage est
      stable (nom public puis club).
- [ ] Étant donné un élève ou un encadreur sans point, alors il n'apparaît pas dans le classement.
- [ ] Étant donné un compte suspendu, alors il n'apparaît pas dans les classements publics.
- [ ] Étant donné un ancien élève, alors il n'apparaît pas dans le classement du semestre en cours ; il peut
      apparaître dans le total historique s'il a des points.
- [ ] Étant donné le **Total historique**, alors les points de tous les semestres et hors semestre sont additionnés,
      sans remise à zéro.
- [ ] Étant donné l'absence de semestre en cours, alors l'onglet Semestre affiche « Aucun semestre en cours » et le
      Total historique reste consultable.
- [ ] Étant donné un classement de plus de 50 lignes, alors la page 1 en montre 50, la page 2 la suite, et le
      total est annoncé.
- [ ] La réponse publique ne contient ni nom complet, ni e-mail, ni téléphone, ni identifiant utilisateur ; elle ne
      contient que le rang, le nom public, le club, la DRE et les points (et l'identifiant public du club pour la
      catégorie Clubs).

### Classement interne

- [ ] Étant donné un élève affilié actif, quand il ouvre son espace, alors il voit le classement des élèves de son
      club pour le semestre et le total historique, avec sa ligne mise en évidence.
- [ ] Étant donné un encadreur rattaché actif, quand il ouvre Mon Club Santé, alors il voit les classements des
      élèves et des encadreurs de son club.
- [ ] Étant donné un président, alors il voit le classement des élèves de son club.
- [ ] Étant donné un compte qui n'appartient pas au club, quand il demande ce classement, alors l'API refuse.
- [ ] Le classement interne ne contient aucun nom complet d'élève, aucune adresse, aucun téléphone et aucun
      identifiant utilisateur.
- [ ] Le classement interne n'est accessible par aucune route publique.

### Tableaux de bord

- [ ] L'espace d'un élève affiche ses rangs club, DRE et national pour le semestre et pour l'historique.
- [ ] L'espace d'un encadreur affiche les mêmes rangs.
- [ ] Le rang régional annuel et la place dans le club de la spec 034 restent visibles et étiquetés « Année
      académique ».
- [ ] Un élève sans club n'a pas de rang de club et garde ses rangs DRE et national.
- [ ] Un élève sans point voit « Pas encore classé » au lieu d'un rang inventé.
- [ ] Un visiteur ne voit aucun classement personnel.

### Admin — registre

- [ ] Le registre liste les lignes avec leur bénéficiaire, action, montant, semestre, année, club, auteur, clé,
      motif et annulation éventuelle.
- [ ] Les filtres par période, action, type de bénéficiaire, club, correction et recherche fonctionnent ensemble.
- [ ] Le registre est paginé et annonce le total.
- [ ] Aucune route du registre ne permet de modifier ou de supprimer une ligne.
- [ ] Le registre exige `points:consulter`, le périmètre national et la double authentification.

### Admin — correction et annulation

- [ ] Étant donné une ligne de +100, quand l'admin l'annule avec un motif, alors une ligne de -100 liée à
      l'originale est écrite, la part du club est retirée, et la ligne d'origine reste intacte.
- [ ] Étant donné un élève, quand l'admin saisit une correction de +25 avec un motif, alors une ligne
      `admin.correction` de +25 est écrite, sans part de club.
- [ ] Étant donné une correction de -10, alors le total de l'élève baisse de 10 et le club ne bouge pas.
- [ ] Étant donné un montant nul, un montant au-delà de ±10 000 ou un motif de moins de 10 caractères, alors la
      correction est refusée.
- [ ] Étant donné une correction visant un admin, un visiteur ou un joueur sans compte, alors elle est refusée.
- [ ] Étant donné une correction sans droit `points:modifier`, sans périmètre national ou sans double
      authentification, alors elle est refusée.
- [ ] Étant donné une correction réussie, alors le journal d'audit contient le bénéficiaire, le montant, le motif,
      le semestre, l'année et le club.
- [ ] Étant donné la même clé d'idempotence envoyée deux fois, alors une seule ligne est écrite.
- [ ] Étant donné une correction annulée, alors l'annulation retire exactement la correction et laisse une trace.
- [ ] Le total historique d'un bénéficiaire peut devenir négatif après une correction ; il s'affiche sans erreur.

## Cas limites et erreurs

- **Aucun semestre en cours** : le classement du semestre est vide avec un message ; l'historique fonctionne ; une
  correction est écrite sans semestre et ne compte que dans l'historique.
- **Aucune année académique en cours** : même règle pour l'année ; la correction reste dans l'historique.
- **DRE inconnue ou inactive** : la route répond 422/404 avec un message compréhensible ; aucune liste vide
  trompeuse.
- **Niveau `club` demandé sur la route publique** : refusé ; le niveau club n'existe que sur la route authentifiée
  du club.
- **Page hors limites** : renvoie une liste vide avec le total, jamais une erreur 500.
- **Élève qui change d'établissement** : il est classé dans la DRE de son établissement actuel ; les points déjà
  gagnés ne sont pas déplacés. Le classement historique utilise la région actuelle, pas une photographie
  historique ; R14 figera les palmarès.
- **Club qui change de statut** : un club suspendu disparaît des classements publics ; son historique reste dans le
  registre. Un club qui revient en service réapparaît.
- **Élève qui change de club** : la part de club déjà créditée reste à l'ancien club ; le classement interne du
  nouveau club ne reprend pas les points de l'ancien.
- **Annulation d'une ligne dont le club n'existe plus ou est suspendu** : la part négative est quand même écrite,
  car elle corrige un crédit passé ; le club n'apparaît simplement plus dans les classements s'il n'est pas en
  service.
- **Correction d'un élève suspendu ou ancien** : autorisée pour l'archive, sans part de club ; le total peut
  devenir négatif.
- **Double clic sur une correction** : la clé d'idempotence empêche le doublon ; le bouton se désactive pendant
  l'envoi.
- **Recherche admin sans résultat** : message vide, pas d'erreur.
- **Filtre de DRE sur un collaborateur de DRE** : le registre et la correction étant nationaux, un collaborateur de
  DRE reçoit un refus ; les classements publics restent lisibles par tous.
- **Charge** : les classements sont calculés à la demande ; si les pages deviennent lentes, une vue matérialisée
  pourra être ajoutée sans changer le registre (ADR-0004).
- **Perte de réseau** : le site affiche l'erreur de l'API et un bouton « Réessayer » ; aucun classement n'est
  calculé dans le navigateur.

## Hors périmètre

- Le gel du classement, le contrôle antifraude, la résolution des ex æquo, le Top 3, les récompenses et les
  distinctions : R14.
- La clôture et les archives annuelles de la spec 034 : déjà livrées, non modifiées.
- Une correction directe du score d'un club : on annule les lignes d'élèves qui portent la part du club.
- Les classements publics au niveau du club : interdits par la Q20 et `docs/RULES.md`.
- L'export CSV ou PDF des classements et du registre.
- Le partage d'un visuel de classement : R17.
- La détection d'anomalies et l'analyse comparative : R22.
- Les distinctions des encadreurs et les prix : R14.
- Les classements par matière, par axe ou par quiz : non demandés.

## Questions ouvertes

Aucune. Les choix de mise en œuvre sont proposés dans l'introduction et détaillés dans `plan.md` ; ils restent à
valider avec le plan avant l'implémentation.
