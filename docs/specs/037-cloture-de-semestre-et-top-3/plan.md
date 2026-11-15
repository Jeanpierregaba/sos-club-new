# 037 — Plan technique

## Approche

La clôture **photographie** le classement national des élèves du semestre dans deux tables dédiées, sur le modèle
de la clôture d'année de la spec 034 (`ClassementAnnuel`) : le registre `mouvement_points` reste la seule source
des points (ADR-0004), et la photo n'en est qu'une copie datée, jamais une source de points. Le palmarès public
lit la photo, pas le registre : il ne bouge plus une fois publié, même si l'élève change de pseudonyme ou de club.

Le calcul réutilise la base de classement de la spec 036 (`_base_eleves` : comptes actifs, hors anciens élèves,
totaux positifs), avec deux colonnes en plus : le **rang brut** (`rank()`, égalités partagées) et le **rang
départagé** (`row_number()` sur points décroissants, puis date d'atteinte du total croissante, puis pseudonyme).
La date d'atteinte est la date de la **dernière ligne** de l'élève dans le semestre : c'est elle qui a fixé son
total final. Cette règle est déterministe, se calcule en SQL et s'explique en une phrase.

Les transitions (gel, écart, validation, annulation de validation, publication) sont des routes POST qui verrouillent
la clôture (`SELECT … FOR UPDATE`) et vérifient l'état attendu : deux admins simultanés obtiennent un conflit 409,
jamais un état mixte. Le Top 3 n'est pas stocké tant que la clôture est gelée : il se déduit de la photo et des
écarts. La validation écrit la **place** (1, 2, 3) sur les trois candidats retenus ; l'annulation de la validation
l'efface.

Aucune tâche planifiée : le gel est un clic de l'admin après la date de fin. Aucun point n'est écrit au registre.

## Fichiers touchés

### Backend

- `backend/app/points/models.py` : modèles `ClotureSemestre` et `CandidatCloture`, énumération `EtatCloture`.
- `backend/app/points/classements.py` : une fonction `classement_a_figer(db, semestre, limite)` qui renvoie les
  lignes à photographier (rangs brut et départagé, date d'atteinte), à partir de `_base_eleves`.
- `backend/app/points/clotures.py` (nouveau) : `lister`, `detail`, `geler`, `ecarter`, `reintegrer`, `valider`,
  `annuler_validation`, `publier`, `palmares_public`, `distinctions_de` ; journal et notifications.
- `backend/app/points/schemas.py` : schémas admin (`ClotureResume`, `ClotureDetail`, `CandidatAdmin`, `EcartPoints`,
  `MotifCloture`) et publics fermés (`PalmaresPublic`, `LaureatPublic`, `Distinction`).
- `backend/app/points/router.py` : routes admin des clôtures, route publique `/palmares`, champ `distinctions` de
  `/classements/moi`.
- `backend/alembic/versions/<nouvelle>_clotures_de_semestre.py` : création des deux tables (non destructive).
- `backend/tests/test_clotures.py` (nouveau) : règles et calcul. `backend/tests/test_clotures_routes.py` (nouveau) :
  droits, schémas publics, notifications, concurrence.

### Site

- `src/routes/_connecte/admin/points.tsx` : onglet **Clôtures** (national seulement).
- `src/routes/_connecte/admin/points.clotures.index.tsx` (nouveau) : liste des semestres et de leur état.
- `src/routes/_connecte/admin/points.clotures.$semestreId.tsx` (nouveau) : photo, Top 3 proposé, écarts, actions et
  dialogues motivés, écart avec le classement actuel, historique des étapes.
- `src/routes/hall-of-fame.tsx` : section **Palmarès des semestres** (ancre `#palmares`), règle des ex æquo.
- `src/components/classements/Palmares.tsx` (nouveau) : cartes des lauréats, état vide.
- `src/components/espace/MesClassements.tsx` : bloc **Mes distinctions** dans `RangsPersonnels`.
- `src/lib/api/client.ts` : types et fonctions ; `src/lib/admin.ts` : libellés des nouvelles actions du journal.
- `src/lib/api/schema.gen.ts`, `backend/openapi.json` : régénérés.

## Données

Nouvelle table `cloture_semestre` (une ligne par semestre gelé au moins une fois) :

| Colonne                   | Type                             | Rôle                                                               |
| ------------------------- | -------------------------------- | ------------------------------------------------------------------ |
| `semestre_id`             | UUID, PK, FK `semestre` RESTRICT | Une seule clôture par semestre (deux gels simultanés → une ligne). |
| `etat`                    | `gele` / `valide` / `publie`     | Contrainte de vérification sur les trois valeurs.                  |
| `gele_le`, `gele_par`     | horodatage UTC, FK utilisateur   | Dernier gel (regel compris).                                       |
| `valide_le`, `valide_par` | nullables                        | Remplis à l'état `valide` et `publie`, vidés à l'annulation.       |
| `publie_le`, `publie_par` | nullables                        | Remplis une seule fois.                                            |
| `libelle`, `debut`, `fin` | copie du semestre au gel         | Le palmarès garde le libellé même si le semestre est renommé.      |
| `version`                 | entier (`Suivi`)                 | Verrou optimiste en plus du verrou de ligne.                       |

Contraintes : cohérence état ↔ colonnes (`valide` ⇒ `valide_le` non nul ; `publie` ⇒ `publie_le` non nul).

Nouvelle table `candidat_cloture` (au plus 50 lignes par clôture) :

| Colonne                                  | Rôle                                                                      |
| ---------------------------------------- | ------------------------------------------------------------------------- |
| `id`                                     | UUID v7.                                                                  |
| `semestre_id`                            | FK `cloture_semestre` CASCADE, indexée.                                   |
| `utilisateur_id`                         | FK `utilisateur` CASCADE (comme `classement_annuel`).                     |
| `rang`, `rang_brut`                      | Rang départagé (unique par clôture) et rang avec égalités.                |
| `pseudonyme`, `club`, `dre`, `points`    | Copie au gel ; jamais de nom complet.                                     |
| `atteint_le`                             | Date de la dernière ligne du semestre, critère d'ex æquo.                 |
| `ecarte_le`, `ecarte_par`, `motif_ecart` | Écart motivé (10 à 500 caractères), nul si le candidat est retenu.        |
| `place`                                  | 1, 2 ou 3 à la validation ; nulle sinon. Unique par clôture si non nulle. |

Contraintes : `UNIQUE (semestre_id, utilisateur_id)`, `UNIQUE (semestre_id, rang)`, `place BETWEEN 1 AND 3`,
`UNIQUE (semestre_id, place)` partiel, cohérence des trois colonnes d'écart.

Un **regel** supprime puis réécrit les candidats dans la même transaction et **reporte les écarts** sur les élèves
toujours présents (même `utilisateur_id`) : l'admin ne perd pas son contrôle. Le regel n'est possible qu'à l'état
`gele`.

Migration non destructive : deux créations de tables, retour arrière par suppression des deux tables. Aucune
donnée existante n'est touchée.

## API / interfaces

Routes admin, préfixe `/api/admin/points/clotures` :

| Méthode et chemin                                              | Droit                        | Effet                                                                                         |
| -------------------------------------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------- |
| `GET /`                                                        | `points:consulter`, national | Semestres terminés ou en cours avec l'état de clôture.                                        |
| `GET /{semestre_id}`                                           | idem                         | Photo, Top 3 proposé ou validé, écarts, étapes, écart avec le classement actuel.              |
| `POST /{semestre_id}/gel`                                      | `points:modifier`, national  | Gel ou regel ; 409 si le semestre n'est pas terminé ou si la clôture n'est pas à l'état gelé. |
| `POST /{semestre_id}/candidats/{utilisateur_id}/ecart`         | idem, corps `{motif}`        | Écarte un candidat ; 409 hors état gelé.                                                      |
| `POST /{semestre_id}/candidats/{utilisateur_id}/reintegration` | idem                         | Réintègre ; 409 hors état gelé.                                                               |
| `POST /{semestre_id}/validation`                               | idem                         | Fige les places ; 422 sans candidat retenu.                                                   |
| `POST /{semestre_id}/annulation-validation`                    | idem, corps `{motif}`        | Revient à l'état gelé ; 409 si publiée.                                                       |
| `POST /{semestre_id}/publication`                              | idem                         | Publie et notifie ; 409 hors état validé ; 422 si un lauréat n'est plus actif.                |

Tous ces droits sont sensibles : la double authentification est exigée par `exiger_permission` (spec 036). Chaque
transition est journalisée : `semestre_gele`, `semestre_regele`, `candidat_ecarte`, `candidat_reintegre`,
`cloture_validee`, `validation_annulee`, `palmares_publie`.

L'**écart avec le classement actuel** est calculé à la lecture du détail : on recalcule le classement à figer et on
renvoie les candidats dont les points ont changé, les élèves qui entreraient dans le Top 3 proposé, et un booléen
`top3_different`.

Routes publiques et personnelles :

- `GET /api/palmares` : semestres publiés, du plus récent au plus ancien, avec leurs lauréats (place, distinction,
  pseudonyme, club, DRE, points). Schéma fermé (`extra="forbid"`), sans identifiant utilisateur.
- `GET /api/classements/moi` : nouveau champ `distinctions` (semestre, place, distinction, points), vide pour qui
  n'en a pas.

Notification à la publication : type `distinction_semestre`, titre « Tu es Grand Champion du semestre S1 2026 »,
lien `/hall-of-fame#palmares`. Écrite dans la même transaction que la publication.

## Dépendances

Aucune nouvelle dépendance.

## Sécurité

- **Données des mineurs** (`docs/RULES.md`) : le palmarès public ne contient que pseudonyme, club, DRE, points et
  distinction. Les candidats écartés, leurs motifs et les identifiants ne sortent que par les routes admin.
- **Droits** (ADR-0003, `docs/SECURITY.md`) : vérifiés sur chaque route, périmètre national, double
  authentification ; un collaborateur de DRE est refusé ; tests de refus pour chaque route.
- **Intégrité** : verrou de ligne et vérification d'état à chaque transition ; une clôture publiée n'a aucune route
  de modification ni de suppression ; la FK `semestre` en RESTRICT empêche de supprimer un semestre clôturé.
- **Traçabilité** : journal d'audit pour chaque étape, avec l'auteur, le semestre et le motif le cas échéant.

## Tests

Parties critiques en TDD (`docs/TESTING.md` : points et classements) : les tests de `test_clotures.py` précèdent le
code.

- Calcul : photo des 50 premiers, exclusions (suspendus, anciens, totaux nuls ou négatifs), rangs brut et
  départagé, ex æquo par date d'atteinte puis pseudonyme, débordement d'égalité à la 3e place.
- Cycle : gel refusé avant la fin, regel qui reporte les écarts, écart et réintégration, validation avec moins de
  trois candidats, validation refusée sans candidat, annulation de validation motivée, publication refusée hors
  état validé ou avec un lauréat suspendu, aucune modification après publication.
- Concurrence : deux gels simultanés (une seule clôture), validation et publication concurrentes (un 409).
- Public : clés exactes de `/palmares`, absence des écartés et des non publiés, valeurs figées après un changement
  de pseudonyme ou de club.
- Espace : `distinctions` dans `/classements/moi`, notification à la publication, aucune ligne de registre écrite.
- Droits : sans droit, sans double authentification, collaborateur de DRE, visiteur ; journal de chaque étape.
- Site : composant `Palmares` (lauréats, état vide), bloc « Mes distinctions », écran admin (actions selon l'état).

## Risques

- **Date d'atteinte et lignes tardives** : une annulation de la spec 036 visant le semestre clos devient la
  « dernière ligne » de l'élève et repousse sa date d'atteinte. C'est voulu (son total final date de là), et le
  regel le montre ; la règle publiée le dit en clair.
- **Semestre renommé après publication** : le palmarès garde la copie du libellé prise au gel.
- **Suppression d'un compte lauréat** : la cascade retire sa ligne du palmarès (droit à l'effacement) ; la place
  reste vide plutôt que d'être réattribuée. À confirmer avec le porteur si cela arrive.
- **Volume** : 50 candidats par semestre, quelques semestres par an : aucun enjeu de performance.
- **Question ouverte de la spec 036** (club affiché sans choix de l'élève) : le palmarès copie le club au gel ; si
  une préférence est ajoutée plus tard, la photo devra la respecter au moment du gel.
