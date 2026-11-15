# 038 — Plan technique

## Approche

Les trois modèles de rapport sont **trois types du moteur de modération** (ADR-0009) : `rapport_activite`,
`rapport_mensuel` et `bilan_semestriel`. Le moteur fournit déjà ce que la spec demande : brouillon, version soumise
figée, versions successives, décisions motivées sous verrou avec 409, file filtrée par DRE, auteur qui ne décide
jamais de son propre contenu, notifications et journal dans la même transaction. Un rapport « approuvé » est, pour
le moteur, un contenu dont la version est validée. Il n'a **ni adresse publique, ni dépublication, ni révision**
après approbation, comme la proposition de fiche du club (spec 026). Aucune route publique ne lit ces types.

Le moteur ne connaît pas ce qui est propre aux rapports. Une table d'**en-tête de rapport** (`rapport`, une ligne
par contenu) porte donc :

- la référence ;
- le club ;
- la date, le mois ou le semestre ;
- le lien de doublon.

Ces champs sont filtrés, joints ou rendus uniques par la base, donc ils vivent en colonnes. Les textes (contexte,
déroulement, synthèse…) restent en JSONB dans la version, validés par un schéma Pydantic par modèle.

**Points.** Trois crédits sont écrits à l'approbation :

- l'auteur encadreur, par `actions_auteur` du type ;
- le club, par le crochet `a_la_publication`, qui écrit aussi les notifications des encadreurs ;
- aucun pour un doublon : `points_permis` répond « non » quand le rapport est lié à un original.

**Clés du registre.** Les clés font la règle « une fois », et la base tranche, même sous concurrence :

| Crédit                      | Clé                                       |
| --------------------------- | ----------------------------------------- |
| Rapport d'activité, auteur  | `rapport_activite:<contenu>`              |
| Rapport d'activité, club    | `club.rapport_activite:<contenu>`         |
| Rapport mensuel             | `rapport_mensuel:<encadreur>:<AAAA-MM>`   |
| Bilan semestriel, encadreur | `bilan_semestriel:<encadreur>:<semestre>` |
| Bilan semestriel, club      | `club.bilan_semestriel:<club>:<semestre>` |

**Compte collectif du club** (amende l'ADR-0012). Aujourd'hui, chaque ligne du registre porte une personne, et la
part d'un club est la moitié du gain d'un élève. Une ligne **de club** n'a pas de personne :

- `utilisateur_id` vaut NULL ;
- `club_id` est renseigné ;
- `montant` est le gain du club ;
- `demi_points_club` vaut `2 × montant`.

Une contrainte réserve ce cas aux actions `club.*`. Le score d'un club reste la somme de ses demi-points divisée
par 2, sans requête nouvelle, et aucun total personnel ne bouge : les classements personnels joignent ou groupent
par compte, et une ligne sans compte n'y entre pas. C'est plus sûr qu'une ligne à 0 point portée par l'auteur :
une ligne à 0 changerait la date d'atteinte des ex æquo (spec 037) et ferait apparaître le président dans le
registre. Une nouvelle fonction `crediter_club(db, action, club_id, cle)` écrit ces lignes. Elle ne crédite rien
si le club n'est pas en service (règle de la spec 033).

**Justificatifs.** Les **photos** réutilisent les tables `photo` et `version_photo` de la spec 024 : réencodage,
métadonnées retirées, attestation copiée, purge 90 jours après un refus. Elles ne sont jamais servies par la route
publique, qui ne lit que les types publics. Les **documents** (PDF, Word) ont leur table `piece_rapport`, sur le
même stockage privé (ADR-0005). Le PDF passe par le contrôle existant (`fichiers/pdf.py`). Le Word `.docx` passe
par un contrôle nouveau, en bibliothèque standard (`zipfile`) :

- archive ZIP valide, avec `[Content_Types].xml` et `word/document.xml` ;
- aucune macro (`vbaProject.bin`, type `macroEnabled`) ni contenu actif ;
- taille décompressée bornée (bombe ZIP).

Les **liens YouTube** sont des champs de la version, validés par le contrôle d'adresse des vidéos (ADR-0005).

**« Reçu / consulté ».** Une table `lecture_rapport` (rapport, encadreur, consulté le) est remplie à la première
ouverture d'un rapport par un encadreur du club. « Reçu » se déduit : tout encadreur du club au moment de la
soumission l'a reçu.

**Export PDF** d'un rapport approuvé avec `reportlab`, déjà utilisé pour le certificat (spec 029). L'export
**CSV** de l'archive admin suit le modèle des exports existants.

## Fichiers touchés

### Backend

- `backend/app/points/models.py` : `MouvementPoints.utilisateur_id` devient nullable ; contraintes `ligne_de_club`
  et `part_du_club` revues ; `montant_signe` accepte l'annulation d'une ligne de club.
- `backend/app/points/service.py` : `crediter_club` ; `annuler` copie une ligne de club telle quelle.
- `backend/app/points/registre.py` et `schemas.py` : le registre admin (spec 036) affiche le bénéficiaire
  « Club : <nom> » d'une ligne de club, filtrable par club ; une correction motivée peut viser un club.
- `backend/app/points/bareme.py` : `en_service=True` pour les cinq actions des rapports.
- `backend/app/rapports/` (nouveau domaine) :
  - `models.py` : `Rapport`, `PieceRapport`, `LectureRapport`, `TypeActivite`, `ModeleRapport` ;
  - `schemas.py` : schémas des trois modèles (écriture, lecture auteur, lecture club, examen, archive) ;
  - `types.py` : enregistrement des trois types au registre du moteur, avec leurs crochets ;
  - `service.py` : brouillon, modification, soumission, suppression, référence, doublons, droits de lecture,
    « consulté » ;
  - `pieces.py` : ajout, retrait et lecture des documents ; contrôle Word ;
  - `export.py` : PDF d'un rapport, CSV de l'archive ;
  - `router.py` : routes de l'encadreur et du président ; `router_admin.py` : archive, examen, doublon.
- `backend/app/fichiers/docx.py` : contrôle d'un `.docx`.
- `backend/app/moderation/models.py` : contraintes `adresse_si_publie` et `contenu_du_club` élargies aux types
  de rapport.
- `backend/app/moderation/decisions.py` :
  - l'aperçu et la file savent montrer un rapport (titre, club, alerte de doublon) ;
  - le titre de la notification d'approbation vient du type (« approuvé » au lieu de « publié ») ;
  - `approuver` reçoit un `doublon_de` facultatif, enregistré sous le même verrou que la décision.
- `backend/app/moderation/types.py` : champ `avis_approbation` (texte de la notification d'approbation).
- `backend/app/referentiel/` : types d'activité, liste modifiable par l'admin (module `referentiel`, comme les
  axes).
- `backend/app/main.py` : routeurs.
- `backend/alembic/versions/<rev>_rapports_d_activite.py` : migration non destructive (tables, colonnes nullable,
  contraintes, types d'activité de départ).

### Site

- `src/lib/api/client.ts` : types et appels.
- `src/components/rapports/` :
  - `FormulaireRapport.tsx` : un formulaire par modèle, avec rappel « aucun nom d'élève » ;
  - `PiecesRapport.tsx` : photos avec attestation, documents, liens YouTube ;
  - `ListeRapports.tsx` : état, référence, points, « reçu / consulté » ;
  - `DetailRapport.tsx` : lecture, historique des décisions, export PDF.
- Espace de l'encadreur :
  - `src/routes/_connecte/mes-rapports.index.tsx` : mes rapports et rapports du club ;
  - `mes-rapports.nouveau.tsx` : choix du modèle ;
  - `mes-rapports.$id.tsx` : brouillon ou lecture ;
  - l'accueil de l'encadreur gagne les blocs « À faire ».
- Espace du président : `src/routes/_connecte/mon-club.rapports.*.tsx`, mêmes composants, rapport d'activité
  seulement.
- Admin :
  - `src/routes/_connecte/admin/moderation.tsx` : aperçu d'un rapport (champs, pièces, alerte et choix du doublon) ;
  - `src/routes/_connecte/admin/rapports.tsx` : archive, filtres et export CSV ;
  - `referentiel.types-activite.tsx` : la liste des types d'activité.
- `src/lib/admin.ts` : libellés du journal.

### Documents

- `docs/decisions/0012-part-du-club-et-annee-academique.md` : note « Lignes du compte collectif (spec 038) ».
- `docs/decisions/0009-moteur-de-moderation.md` : note sur les types sans publication (rapports).
- `docs/PRD.md` (ligne R12), `docs/ROADMAP.md`, `docs/DESIGN.md` (écrans des rapports), `docs/SECURITY.md`
  (fichiers Word, rapports privés), `TASKS.md`.

## Données

```
rapport
  contenu_id     PK, FK contenu CASCADE
  modele         'activite' | 'mensuel' | 'bilan'      (= type du contenu, redondant pour les contraintes)
  reference      texte unique, attribuée à la première soumission (RA-2026-000123), NULL en brouillon
  club_id        FK club RESTRICT, copié de l'auteur à la création
  date_activite  date, activité seulement
  type_activite  FK type_activite RESTRICT, activité seulement
  mois           date (premier jour du mois), mensuel seulement
  semestre_id    FK semestre RESTRICT, bilan seulement
  doublon_de_id  FK rapport NULL, posé à l'approbation « comme doublon »
  CHECK forme selon le modèle ; CHECK doublon_de_id <> contenu_id
  INDEX (club_id, modele, date_activite)        pour la détection des doublons
  INDEX (club_id, modele, mois), (club_id, modele, semestre_id)

piece_rapport
  id, contenu_id FK CASCADE, auteur_id, nom (affiché), type ('pdf' | 'docx'), cle_stockage, octets,
  cree_le, efface_le
version_piece (version_id, piece_id)            comme version_photo : une version soumise garde ses pièces

lecture_rapport
  (contenu_id, utilisateur_id) PK, consulte_le

type_activite
  code PK, libelle, actif, ordre               (causerie, sensibilisation, dépistage, campagne, concours,
                                                 sortie, autre)

reference_rapport
  séquence Postgres par modèle (rapport_activite_seq, …) ; l'année vient de la date de soumission

mouvement_points
  utilisateur_id → nullable
  CHECK ligne_de_club : utilisateur_id IS NOT NULL
        OR (club_id IS NOT NULL AND action LIKE 'club.%' AND demi_points_club = 2 * montant)
  CHECK part_du_club_moitie : demi_points_club IS NULL OR demi_points_club = montant
        OR utilisateur_id IS NULL
```

La migration est non destructive : des tables nouvelles, une colonne qui devient nullable et des contraintes
élargies. Les lignes existantes respectent les nouvelles contraintes. Au retour arrière (downgrade), les lignes de
club sont refusées : la migration descendante échoue s'il en existe, plutôt que de les effacer. C'est la même
règle que pour la migration de la spec 035.

La DRE de la file (`contenu.dre_code`) vient de l'établissement du club, comme pour l'auteur aujourd'hui. Le club
est copié à la création du brouillon. Un encadreur qui change d'établissement garde ses rapports anciens sur leur
club d'origine. La passation de présidence (`transferer_contenus`) ne touche pas les rapports : son filtre se
limite déjà aux actualités et aux fiches, et un test le garde.

## API / interfaces

Côté auteur (encadreur vérifié d'un club en service, ou président de ce club ; 403 sinon) :

| Route                                                           | Rôle                                                                                   |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `GET /api/rapports`                                             | mes rapports ; `?club=1` : rapports du club visibles par moi, avec « reçu / consulté » |
| `POST /api/rapports`                                            | crée un brouillon `{modele}` ; le président ne crée qu'un rapport d'activité           |
| `GET /api/rapports/{id}`                                        | lecture (marque « consulté » pour un encadreur du club autre que l'auteur)             |
| `PUT /api/rapports/{id}`                                        | modifie le brouillon ou la version à corriger                                          |
| `DELETE /api/rapports/{id}`                                     | supprime un brouillon jamais soumis, avec ses fichiers                                 |
| `POST /api/rapports/{id}/soumission`                            | soumet ; renvoie la référence et les doublons probables                                |
| `POST /api/rapports/{id}/photos`, `…/documents`                 | ajoute un justificatif (multipart) ; `DELETE …/{piece}` le retire                      |
| `GET /api/rapports/{id}/photos/{p}/{taille}`, `…/documents/{d}` | lit un justificatif (404 hors des lecteurs autorisés)                                  |
| `GET /api/rapports/{id}/export.pdf`                             | PDF d'un rapport approuvé                                                              |
| `GET /api/rapports/types-activite`                              | la liste active                                                                        |

Côté admin (module `moderation` pour décider, comme les autres contenus ; nouveau module `rapports` pour
l'archive ; périmètre DRE) :

| Route                                                        | Rôle                                                      |
| ------------------------------------------------------------ | --------------------------------------------------------- |
| file et décisions existantes de `/api/admin/moderation`      | les rapports y entrent, avec l'aperçu propre aux rapports |
| `POST /api/admin/moderation/{id}/approbation` + `doublon_de` | approuver comme doublon (rapport approuvé du même club)   |
| `GET /api/admin/rapports`                                    | archive filtrable (modèle, état, club, DRE, axe, période) |
| `GET /api/admin/rapports/export.csv`                         | export de l'archive, sans nom d'élève                     |
| `GET /api/admin/rapports/{id}/export.pdf`                    | PDF d'un rapport                                          |
| `/api/admin/referentiel/types-activite`                      | lister, créer, modifier, désactiver                       |

Le nouveau module `rapports` (consulter, exporter) se range dans le catalogue des droits (ADR-0008). Le rôle de
départ « modérateur » reçoit « consulter ».

## Dépendances

Aucune nouvelle : `reportlab`, `pypdf` et `Pillow` sont déjà là. Le contrôle Word utilise `zipfile` (bibliothèque
standard).

## Sécurité

- **Lecture** : l'API vérifie, sur chaque route, que le demandeur est l'auteur, un encadreur du club, le
  président (rapport d'activité seulement) ou un collaborateur habilité de la bonne DRE. Sinon, réponse 404, pour
  ne rien révéler. Un brouillon n'est lu que par son auteur.
- **Fichiers** :
  - type vérifié par le contenu, jamais par l'extension seule ;
  - photos réencodées ; PDF passé par le contrôle existant ; Word sans macro et à taille décompressée bornée ;
  - taille vérifiée en lisant le flux, sans faire confiance à `Content-Length` ;
  - service en `Content-Disposition: attachment`, avec `X-Content-Type-Options: nosniff` et la politique de
    sécurité stricte des fichiers existants ;
  - clés de stockage aléatoires.
- **Données de mineurs** : aucun champ nominatif ; la répartition des participants est agrégée ; l'export CSV ne
  contient ni nom ni identifiant d'élève ; le PDF ne contient que le rapport.
- **Points** : clés uniques du registre et verrou du moteur ; un rapport ne crédite jamais deux fois, même rejoué
  ou approuvé en parallèle.
- **Journal** : chaque décision (déjà journalisée par le moteur), chaque export CSV et chaque modification des
  types d'activité.
- `docs/SECURITY.md` : ajouter les fichiers Word et les rapports privés à la checklist.

## Tests

Parties critiques en TDD (`docs/TESTING.md` : points, droits, données de mineurs) :

1. **Registre** : une ligne de club ne change aucun total ni rang personnel (élève, encadreur), ni la date
   d'atteinte des ex æquo ; elle compte dans le classement des clubs (spec 036) et apparaît au registre ; son
   annulation la retire ; la contrainte refuse une ligne sans compte pour une action qui n'est pas `club.*`.
2. **Points des rapports** :
   - +100 et +50 une fois, même si l'approbation est rejouée ou lancée deux fois en parallèle ;
   - président auteur : club seulement ; doublon : rien ;
   - mensuel deux fois le même mois, bilans de deux encadreurs le même semestre ;
   - club suspendu : pas de part du club ;
   - aucun point en brouillon, soumis, à corriger ou refusé.
3. **Droits** :
   - tous les cas de lecture et d'écriture de la spec ;
   - un collaborateur de DRE hors de sa région reçoit 404 ;
   - un auteur ne décide pas de son propre rapport ;
   - aucune route publique ne lit un rapport ou une pièce.
4. **Fichiers** : type, taille, nombre ; PDF piégé ; Word avec macro, faux Word, bombe ZIP ; photo sans
   attestation ; lien qui n'est pas YouTube.
5. **Cycle** :
   - version figée et correction en nouvelle version ;
   - référence unique, même pour deux soumissions simultanées ;
   - notifications aux encadreurs du club et au président ;
   - « consulté » ;
   - suppression d'un brouillon avec ses fichiers ;
   - passation sans transfert des rapports ;
   - date future ou trop ancienne ; mensuel ou bilan trop tôt.
6. **Doublons** : alerte à la soumission et dans l'aperçu ; approbation comme doublon refusée vers un rapport
   d'un autre club ou non approuvé.
7. **Exports** : PDF d'un rapport approuvé seulement ; CSV sans nom d'élève et limité au périmètre.
8. **Site** :
   - formulaire par modèle et erreurs ;
   - liste avec états et « reçu / consulté » ;
   - aperçu de modération avec l'alerte de doublon ;
   - mobile vérifié dans le navigateur.

## Risques

- **Ligne de registre sans compte.** Environ 80 endroits lisent `mouvement_points.utilisateur_id`. Une requête
  qui groupe par compte sans le joindre ferait apparaître un groupe « NULL ».
  - Parade : une tâche de revue de chaque requête du registre (classements, années, clôture, registre, jeux,
    certification), et un test de non-régression qui insère une ligne de club puis vérifie chaque total personnel.
  - Si cette revue révèle trop de risques, l'alternative est une table `mouvement_points_club` séparée. Elle
    obligerait à additionner deux sources pour le score d'un club, ce que l'ADR-0004 veut éviter.
- **Moteur de modération pensé pour la publication.** Les rapports en retournent les textes et l'absence
  d'adresse ; le risque est de casser les articles.
  - Parade : la suite existante de la modération sert de filet ; les changements du moteur sont des paramètres du
    type, avec les valeurs actuelles par défaut.
- **Fichiers Word.** C'est un format riche ; on ne l'ouvre jamais côté serveur au-delà du ZIP et on ne l'affiche
  pas : il est seulement téléchargé. Un modérateur qui l'ouvre le fait avec son traitement de texte. Ce risque est
  accepté, et le PDF reste conseillé dans le formulaire.
- **Volume de stockage.** 10 fichiers de 10 Mo par rapport sur le disque du VPS. À suivre avec les sauvegardes
  (phase 5) ; la purge des fichiers des rapports refusés suit celle des photos.
- **Taille de la spec (L).** Le découpage en tâches livre d'abord le rapport d'activité de l'encadreur de bout en
  bout, puis le président, le mensuel et le bilan, puis l'archive et les exports.
- **Auteur qui n'est plus vérifié ou plus actif au moment de l'examen.** Le moteur refuse déjà d'approuver le
  contenu d'un encadreur non vérifié ou d'un compte suspendu (409). Pour un rapport, cette règle est gardée :
  l'équipe refuse avec un motif ou attend. Les points d'un auteur parti ne sont pas versés à un autre. Ce cas est
  ajouté aux cas limites de la spec.
- **Club sans encadreur vérifié** (président seul) : le rapport du président part quand même à l'équipe, et
  personne d'autre n'est notifié. L'écran le dit au président.
