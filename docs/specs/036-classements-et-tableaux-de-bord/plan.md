# 036 — Plan technique

<!-- Le COMMENT. Validé par l'utilisateur avant de découper en tâches. -->

## Approche

Les classements sont **calculés à la demande** depuis `mouvement_points`, sans table de classement : c'est le même
principe que les totaux actuels (un score est une somme, ADR-0004). R14 fige les palmarès ; R13 n'a donc pas à
matérialiser un classement courant. Des index adaptés et la pagination suffisent pour le volume attendu ; si les
pages deviennent lentes, une vue matérialisée pourra être ajoutée sans toucher au registre.

Le registre reste la seule source des points. Une correction est une **nouvelle ligne** `admin.correction`, jamais
une modification. Une annulation est une ligne négative liée à l'originale (`annule_id`), comme la révocation de
certificat de la spec 029. Le minimum de schéma est ajouté : un motif, une action technique et des contraintes qui
autorisent les montants négatifs motivés.

Le site ne calcule aucun rang : l'API renvoie les rangs, le site les affiche. Les charges publiques sont des schémas
fermés (aucun identifiant utilisateur, aucun nom complet, aucun contact).

## Fichiers touchés

### Backend

- `backend/app/points/models.py` : `motif` sur `MouvementPoints`, contraintes `montant_signe` et `motif_correction`,
  index de classement.
- `backend/app/points/bareme.py` : action technique `admin.correction`, bénéficiaire `admin`.
- `backend/app/points/classements.py` (nouveau) : requêtes et schémas des classements publics, du classement
  interne et de la vue admin.
- `backend/app/points/registre.py` (nouveau) : registre admin, recherche de bénéficiaire, correction et annulation.
- `backend/app/points/service.py` : `annuler` accepte un motif et, pour l'admin, un mode qui copie le semestre
  d'origine ; `corriger` écrit la ligne motivée.
- `backend/app/points/router.py` : routes publiques `/classements`, authentifiées `/classements/moi` et
  `/classements/mon-club`, admin `/admin/points/registre`, `/beneficiaires`, `/corrections`,
  `/lignes/{id}/annulation`, `/classements`.
- `backend/app/points/schemas.py` : schémas admin du registre et de la correction.
- `backend/app/admin/catalogue.py` : `points:consulter` devient sensible (le registre montre des noms) ; la ligne
  `admin.correction` reste hors du barème modifiable.
- `backend/alembic/versions/<nouvelle>_classements_et_corrections.py` : migration des données.
- `backend/tests/test_classements.py` (nouveau), `backend/tests/test_points_registre.py` (nouveau),
  `backend/tests/test_points_correction.py` (nouveau) ; `backend/tests/test_clubs_podium.py` mis à jour pour
  utiliser de vraies lignes de registre au lieu d'un monkeypatch.

### Site

- `src/routes/hall-of-fame.tsx` (nouveau) : page publique, filtres dans l'URL.
- `src/components/classements/*` (nouveau) : filtres, tableau, podium, états vides et erreurs.
- `src/components/espace/ClassementDuClub.tsx` (nouveau) : bloc privé des espaces élève, encadreur et président.
- `src/components/espace/commun.tsx` : remplace « Les classements arrivent bientôt » par les rangs personnels.
- `src/components/espace/TableauAnnuel.tsx` : distingue clairement l'année académique du semestre et de
  l'historique.
- `src/routes/_connecte/mon-espace.tsx` et `src/components/espace/EspaceEncadreur.tsx` : chargent les rangs et le
  classement du club.
- `src/routes/_connecte/mon-club-sante.tsx` et `src/routes/_connecte/mon-club.index.tsx` : ajoutent le classement
  interne pour l'encadreur et pour le président.
- `src/routes/_connecte/admin/points.tsx` : onglets **Registre** et **Classements**.
- `src/routes/_connecte/admin/points.registre.tsx` (nouveau) : registre filtrable, correction et annulation.
- `src/routes/_connecte/admin/points.classements.tsx` (nouveau) : classements et classement interne d'un club.
- `src/components/admin/CorrectionPoints.tsx` (nouveau) : dialogue de correction motivée.
- `src/components/SiteHeader.tsx` : entrée **Classements** dans Gamification.
- `src/lib/api/client.ts` : types et fonctions des nouvelles routes.
- `src/lib/api/schema.gen.ts` : régénéré depuis OpenAPI.
- `src/lib/classements.test.ts` (nouveau) : mise en forme des rangs et des scores décimaux.

### Documentation

- `docs/decisions/0013-classements-publics-et-correction-des-points.md` (nouveau) : décisions de R13, lien depuis
  ADR-0004.
- `docs/PRD.md` : cocher les deux exigences de classement couvertes par R13 (le Top 3 reste à R14).
- `docs/ROADMAP.md` : mettre à jour la note de R13 ; la part du club est déjà livrée par la spec 034.
- `docs/specs/034-gamification-eleve-4-niveaux/spec.md` : renvoyer vers R13/036 pour les classements.
- `docs/DESIGN.md` : préciser `/hall-of-fame` et les états de la page.
- `docs/SECURITY.md` : classements publics par pseudonyme, registre national à double authentification, correction
  journalisée.
- `docs/TESTING.md` : classements et corrections dans les tests critiques.
- `TASKS.md` : R13 en cours puis terminé, avec le lien vers la spec.

## Données

Migration **non destructive**, aller-retour testé sur la base locale :

1. `mouvement_points.motif` : `VARCHAR(500)` nullable. Un motif est obligatoire pour une correction et facultatif
   pour une annulation ; il reste nul sur un gain ordinaire.
2. Contrainte `ck_mouvement_points_montant_signe` remplacée :
   ```
   (annule_id IS NOT NULL AND montant < 0)
   OR (annule_id IS NULL AND (
        montant > 0
        OR (action = 'admin.correction' AND motif IS NOT NULL)
   ))
   ```
   Les lignes existantes (gains positifs et annulations négatives liées) restent valides.
3. Contrainte `ck_mouvement_points_motif_correction` :
   ```
   (action <> 'admin.correction' OR motif IS NOT NULL)
   AND (motif IS NULL OR action = 'admin.correction' OR annule_id IS NOT NULL)
   ```
4. `bareme.beneficiaire` accepte la valeur `admin` : `ck_bareme_beneficiaire` est recréée.
5. Ligne `admin.correction` : bénéficiaire `admin`, libellé « Correction manuelle du score », montant 0,
   `actif = false`, `en_service = true`, `propose = false`. La ligne est **technique** : `lister_bareme` la masque
   et `modifier_bareme` la refuse, pour qu'elle ne devienne jamais un gain automatique.
6. Index : `(semestre_id, utilisateur_id)`, `(semestre_id, club_id)` partiel sur `club_id IS NOT NULL`, et
   `(cree_le)` pour le registre. L'index existant `(utilisateur_id, semestre_id)` reste.

Aucune table nouvelle. Aucun point existant n'est modifié ou supprimé. Une correction ne crédite aucune part de
club (`club_id` et `demi_points_club` nuls) ; une annulation copie la part de club et le semestre de la ligne
d'origine.

## API / interfaces

### Classements publics

`GET /api/classements` — sans authentification.

| Paramètre   | Valeurs                         | Défaut     |
| ----------- | ------------------------------- | ---------- |
| `categorie` | `eleves`, `encadreurs`, `clubs` | `eleves`   |
| `niveau`    | `national`, `dre`               | `national` |
| `dre`       | code de DRE, exigé si `dre`     | —          |
| `periode`   | `semestre`, `historique`        | `semestre` |
| `page`      | entier ≥ 1                      | 1          |
| `par_page`  | 1 à 100                         | 50         |

Réponse `ClassementPublic` : `categorie`, `niveau`, `dre` (`code`, `nom`), `periode`, `semestre`
(`libelle`, `debut`, `fin`), `page`, `par_page`, `total`, `lignes`.

Chaque ligne publique :

- élève : `rang`, `nom` (pseudonyme), `club`, `dre`, `points` ;
- encadreur : `rang`, `nom` (prénom + initiale), `club`, `dre`, `points` ;
- club : `rang`, `club_id` (identifiant public), `nom`, `etablissement`, `dre`, `points` (décimal).

Aucune ligne ne porte `utilisateur_id`, `prenom`, `nom` complet, `email`, `telephone` ni `identifiant`.

Un `niveau=dre` sans `dre` répond 422 ; une DRE inconnue ou inactive répond 404 ; `niveau=club` répond 422.

### Classement de l'utilisateur

`GET /api/classements/moi` — authentifié élève ou encadreur.

Réponse : `categorie`, `club` (`id`, `nom`), `semestre` et `historique`, chacun avec `rang_club`, `rang_dre`,
`rang_national`, `points` et `classe` (booléen). Un visiteur ou un admin reçoit 403 ; un élève sans club garde
`rang_club = null`.

### Classement interne du club

`GET /api/classements/mon-club` — authentifié.

Paramètres : `categorie` (`eleves` par défaut, ou `encadreurs`), `periode`, `page`, `par_page`.

Réponse : `club` (`id`, `nom`), `categorie`, `periode`, `semestre`, `page`, `total`, `lignes` avec `rang`, `nom`,
`points`, `est_moi`. Aucun identifiant utilisateur, aucun nom complet d'élève.

Accès : adhésion active, rattachement actif, présidence (adhésion active) ; sinon 404 « Tu n'es rattaché à aucun
club. » ou 403. L'admin passe par la route admin, pas par celle-ci.

### Admin — registre

`GET /api/admin/points/registre` — `points:consulter`, national, double authentification.

Filtres : `semestre_id`, `annee_id`, `du`, `au`, `action`, `beneficiaire` (`eleve`, `encadreur`), `club_id`,
`correction` (booléen), `recherche`, `page`, `par_page`.

Réponse `PageRegistre` : `total`, `page`, `par_page`, `lignes` avec `id`, `cree_le`, `utilisateur_id`, `role`,
`identifiant`, `prenom`, `nom`, `pseudonyme`, `action`, `action_libelle`, `montant`, `semestre`, `annee`, `club`
(`id`, `nom`), `cle`, `valide_par` (nom et identifiant), `motif`, `annule_id`, `est_annulation`,
`est_correction`.

Le registre ne propose ni modification ni suppression. Les lignes négatives et les motifs sont visibles.

`GET /api/admin/points/beneficiaires?q=...` — `points:modifier`, national, double authentification.

Recherche de 2 à 100 caractères sur le pseudonyme et l'identifiant d'un élève, le prénom, le nom et l'identifiant
d'un encadreur. Réponse : au plus 20 bénéficiaires avec `id`, `role`, `nom_public`, `identifiant`, `club`,
`points_total`. Sert au formulaire de correction.

### Admin — correction et annulation

`POST /api/admin/points/corrections` — `points:modifier`, national, double authentification.

Corps : `utilisateur_id` (UUID), `montant` (entier, -10 000 à +10 000, sauf 0), `motif` (10 à 500 caractères),
`cle` (UUID fourni par le site pour l'idempotence).

Effet : une ligne `admin.correction` avec le montant, le motif, l'auteur, le semestre et l'année en cours, sans
part de club. La clé `correction:<cle>` empêche le doublon ; une seconde requête renvoie la ligne existante
(200) au lieu d'en créer une autre (201). Le total du bénéficiaire peut devenir négatif.

Erreurs : 404 bénéficiaire inconnu ; 422 rôle non autorisé, montant nul ou hors bornes, motif trop court ou trop
long.

`POST /api/admin/points/lignes/{id}/annulation` — `points:modifier`, national, double authentification.

Corps : `motif` (10 à 500 caractères).

Effet : une ligne négative avec `annule_id`, le montant, le club, la part de club et le semestre d'origine. La
ligne d'origine reste intacte. Une ligne déjà annulée répond 409.

Les deux routes écrivent au journal d'audit : bénéficiaire, montant, motif, semestre, année, club, ligne liée.

### Admin — classements

`GET /api/admin/points/classements` — `points:consulter`, national, double authentification.

Mêmes filtres que le public, plus `club_id` pour le classement interne d'un club choisi. Les lignes admin portent
`utilisateur_id` et `club_id` pour permettre la correction ; elles ne sont jamais servies par la route publique.
Un club suspendu peut être consulté par l'admin, avec son statut.

### Client du site

- `chargerClassementPublic(filtres)` : page `/hall-of-fame`.
- `chargerMonClassement()` : rangs personnels des espaces.
- `chargerClassementMonClub(filtres)` : bloc privé.
- `adminListerRegistre(filtres)`, `adminChercherBeneficiaires(q)`, `adminCorrigerPoints(entree)`,
  `adminAnnulerLigne(id, motif)`, `adminClassements(filtres)`.
- Types ajoutés à `src/lib/api/client.ts`, puis `npm run api:types` après `uv run python -m app.export_openapi`.

## Dépendances

Aucune nouvelle bibliothèque. L'idempotence de la correction utilise `crypto.randomUUID()` du navigateur et la clé
unique du registre. Les graphiques et tableaux restent en React et Tailwind, sans librairie de tableau.

## Sécurité

- **Données publiques** : schémas Pydantic fermés, aucun identifiant utilisateur ni contact. Des tests vérifient
  l'ensemble exact des clés de chaque ligne publique.
- **Classement interne** : vérification de l'appartenance au club à chaque requête, jamais côté site seulement ;
  aucun nom complet d'élève.
- **Admin** : registre, recherche, correction et annulation en périmètre national et double authentification.
  `points:consulter` rejoint les droits sensibles, car le registre montre des noms.
- **Journal** : chaque correction et annulation laisse une entrée avec le motif ; le journal ne reçoit ni mot de
  passe, ni jeton, ni code.
- **CSRF et origine** : les nouvelles routes POST passent par le contrôle d'origine existant ; aucune exception.
- **Injection** : requêtes SQLAlchemy paramétrées ; la recherche admin borne la longueur et n'interpole jamais de
  SQL.
- **XSS** : les noms, motifs et libellés sont rendus comme du texte React, jamais comme du HTML.
- **Mineurs** : aucun classement public de club (Q20/RULES) ; les élèves restent pseudonymes ; aucune liste de
  membres publique.
- `docs/SECURITY.md` est mis à jour avec ces points.

## Tests

### Backend (TDD pour les parties critiques)

- `test_classements.py` : élèves, encadreurs et clubs sur deux DRE ; national et DRE ; semestre et historique ;
  égalités ; comptes suspendus, anciens élèves, encadreurs non vérifiés, clubs hors service ; score décimal ;
  pagination ; absence de semestre ; paramètres invalides ; clés publiques exactes ; `moi` et `mon-club` avec
  membre, encadreur, président, étranger au club ; `est_moi` ; admin avec identifiants.
- `test_points_registre.py` : filtres combinés, pagination, champs du registre, absence de route d'écriture,
  refus sans 2FA, refus hors périmètre national, recherche de bénéficiaires.
- `test_points_correction.py` : correction positive et négative, motif obligatoire, bornes, rôles refusés, aucune
  part de club, semestre et année en cours, journal, idempotence, total négatif ; annulation d'un gain avec part
  de club et semestre d'origine, annulation d'une correction, double annulation 409 ; migration et contraintes.
- `test_clubs_podium.py` : remplace le monkeypatch par de vraies lignes `crediter` et vérifie le score décimal.
- Les tests d'administration (`test_admin_droits.py`, `test_admin_cas_limites.py`) sont mis à jour pour
  `points:consulter` sensible et pour les nouvelles routes.
- Migration : montée, retour, remontée sur la base locale ; les lignes existantes restent lisibles.

### Site

- `src/lib/classements.test.ts` : mise en forme des rangs, des scores décimaux et des noms publics.
- `npm test` existant.
- Vérification navigateur : page publique (filtres, pagination, états vides, mobile), espaces élève/encadreur,
  registre admin, correction, annulation, refus d'un compte de DRE.

## Risques

- **Performance** : un classement national sur beaucoup d'élèves peut être lent. Les index et la pagination
  limitent le coût ; une vue matérialisée reste la porte de sortie, sans changer le registre.
- **Fuite de données** : le risque principal. Les schémas sont fermés et testés ; aucun identifiant utilisateur
  dans les charges publiques.
- **Migration des contraintes** : `montant_signe` doit continuer d'accepter toutes les annulations existantes.
  Aller-retour testé avant la fusion.
- **Double authentification** : rendre `points:consulter` sensible change l'accès au barème et aux semestres ;
  les collaborateurs concernés devront activer la 2FA. C'est le prix de la lecture du registre nominatif.
- **Correction sans part de club** : choix assumé, expliqué dans la spec et l'ADR. Une erreur de club se corrige
  en annulant la ligne d'origine, qui porte la part.
- **Ligne technique dans le barème** : `admin.correction` ne doit jamais être modifiable ni créditée par le code
  ordinaire ; `lister_bareme` la masque et `modifier_bareme` la refuse.
- **Semestre d'annulation** : l'annulation admin copie le semestre d'origine, contrairement à l'annulation de
  certification existante (semestre courant). Le comportement est explicite dans l'ADR et testé.
- **Route `/hall-of-fame`** : elle cohabite avec `/genie-imhotep/hall-of-fame`. Le menu et les liens distinguent
  « Classements » et « Hall of Fame du Génie Imhotep ».
