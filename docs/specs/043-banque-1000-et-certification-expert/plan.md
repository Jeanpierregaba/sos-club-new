# 043 — Plan technique

## Approche

Deux fichiers de données, versionnés et relisibles, puis une migration qui les charge ; un service de lecture pour le
suivi, sans nouvelle table.

1. **Lot 7.** Un outil lit le document Word et en tire `backend/alembic/donnees/quiz_sante_lot7.json`, au format de
   `quiz_sante.json` (15 entrées, une par thématique). L'outil reconnaît la bonne réponse par le gras du document.
   Il refuse un QCM qui n'a pas exactement 3 propositions et une seule réponse en gras. Le document lui-même n'entre
   pas dans le dépôt : seul le JSON, relu, y entre.
2. **Sélection expert.** Un second outil, `python -m app.certification.selection_expert`, lit la banque d'une base
   et écrit `backend/alembic/donnees/certification_expert.json` : 20 places, 10 QCM chacune (énoncé, choix, bonne
   réponse, explication, quiz Jeux d'origine). Les règles :
   - thématique de la place, puis axe et lots de la thématique (tableau de la spec) ;
   - d'abord les questions actives des réserves des défis Expert publiés de ces lots, dans l'ordre des défis, puis
     dans l'ordre de leur réserve ;
   - quand il y en a plus de 40 (places 9 à 12 et 17 à 20), on les prend à parts égales entre les défis Expert,
     tour à tour ;
   - quand il en manque (places 1 à 8), on complète avec les autres questions actives du même lot, dans l'ordre du
     document ;
   - doublons écartés partout, par énoncé normalisé : les 200 sont différentes ;
   - les 40 questions d'une thématique sont réparties tour à tour entre ses 4 places, pour que chaque quiz mêle
     défis Expert et complément.

   Il est lancé une fois sur la base locale, qui a la même banque que la préprod et la prod (même migration, mêmes
   fichiers). Le JSON est commité : c'est lui qui fait foi, et l'équipe peut le relire.

3. **Migration.** Elle charge le lot 7 puis les 20 quiz de certification, depuis les deux JSON. Elle ne fait rien sur
   une base sans la banque (celle des tests), comme la migration des 100 défis.
4. **Suivi.** Un module `app/certification/suivi.py` calcule les candidats et les statistiques à partir des tables
   existantes : `tentative_quiz` (hors parties d'essai), `place_reussie`, `badge_obtenu` et `certificat`. Il ne crée
   aucune table de compteurs : à l'échelle attendue (quelques milliers de candidats), des requêtes groupées suffisent.

Pourquoi des fichiers plutôt qu'un tirage dans la migration : la sélection doit être relue par l'équipe et identique
en préprod et en prod. Une migration qui tire elle-même dépendrait de l'état de chaque base (questions corrigées ou
désactivées).

## Fichiers touchés

**Créés**

- `backend/app/quiz/import_docx.py` : lecture d'un QCM Word (gras = bonne réponse), avec sa commande
  `python -m app.quiz.import_docx <docx> <json>`. Il lit le XML de `word/document.xml` avec `zipfile` et
  `xml.etree`, sans dépendance nouvelle.
- `backend/alembic/donnees/quiz_sante_lot7.json` : les 78 QCM.
- `backend/app/certification/selection_expert.py` : la sélection, en fonction pure (`selectionner(banque, defis)`)
  plus la commande qui lit la base et écrit le JSON.
- `backend/alembic/donnees/certification_expert.json` : les 20 places.
- `backend/alembic/versions/<rev>_banque_1000_et_certification_expert.py` : la migration.
- `backend/app/certification/suivi.py` : les candidats, l'entonnoir, les chiffres et l'export CSV.
- `backend/tests/test_import_docx.py`, `test_selection_expert.py`, `test_certification_expert_migration.py` et
  `test_certification_suivi.py`.
- `src/routes/_connecte/admin/certification.suivi.tsx` : la page « Suivi ».
- `src/components/admin/SuiviCertification.tsx` (chiffres, entonnoir, par DRE, par semaine) et son test.

**Modifiés**

- `backend/app/certification/router_gestion.py` : les trois routes du suivi.
- `backend/app/certification/schemas.py` : les schémas du suivi.
- `backend/app/certification/regles.py` : les axes et les lots de chaque thématique, au même endroit que les noms
  des badges.
- `src/routes/_connecte/admin/certification.tsx` : l'onglet « Suivi ».
- `src/lib/api/client.ts`, `src/lib/api/schema.gen.ts` : les appels et les types.
- `src/lib/admin.ts` : le libellé du journal `export_suivi_certification`.
- `docs/DESIGN.md` (la page du suivi), `docs/PRD.md` (banque de 1 000 QCM), `TASKS.md`.

## Données

Aucune table ni colonne nouvelle.

Migration `banque_1000_et_certification_expert`, qui révise `8224c2108aff` :

- **Garde.** Si la banque n'est pas chargée (aucun quiz `Lot N —` du Jeu Quiz Santé), la migration ne fait rien.
- **Lot 7.** Pour chaque entrée de `quiz_sante_lot7.json` dont le titre n'existe pas encore, elle insère :
  - un quiz Jeux `depublie` avec le motif « Réserve de la banque (spec 043). », la description
    « Lot 7 — Quiz Santé, 78 questions · thématique N », l'axe, le validateur AIMES-AFRIQUE et la qualité
    « Document officiel « Quiz Santé – 78 questions » » ;
  - ses questions, actives, sans explication.
- **Certification**, pour chaque place de 1 à 20 :
  - un quiz publié de certification qui n'est pas un contenu de test : la place est laissée telle quelle, avec un
    message dans la sortie de la migration ;
  - des quiz de test publiés sur la place : ils passent à `depublie`, avec un motif et `version + 1` ;
  - sinon, elle insère le quiz : `parcours = certification`, `place`, `etat = publie`, `axe_code`, titre
    « Génie Imhotep N — <badge> (k/4) », description « Niveau expert · questions des défis Expert du parcours
    Jeux. », validateur AIMES-AFRIQUE, `publie_le = now()`, et ses 10 questions (`ordre` 1 à 10).
- **Idempotence.** Un titre déjà présent n'est pas réinséré.
- **Retour arrière.** Il supprime les quiz créés qui n'ont jamais été joués et leurs questions. Il dépublie ceux qui
  ont été joués, ce qui garde l'historique. Il ne republie pas les quiz de test.

Les paramètres du parcours ne changent pas (10 questions, 20 s, 10/10) : chaque quiz a exactement le nombre de
questions tirées.

## API / interfaces

Toutes sous `/api/admin/certification/suivi`, droit `quiz : consulter`, et filtrées par le périmètre du
collaborateur (DRE de l'établissement de l'élève ou de l'encadreur, comme `clubs/suivi.py`).

- `GET /candidats`
  - Filtres : `dre`, `club_id`, `role` (`eleve` ou `encadreur`), `etat` (`en_cours`, `inactif` ou `certifie`),
    `recherche`, `page` et `par_page` (au plus 100).
  - Renvoie `PageCandidats {total, candidats: CandidatCertification[]}`.
  - `CandidatCertification` contient : `id`, `nom` (prénom et nom pour un collaborateur national ou un encadreur ;
    pseudonyme d'un élève sinon), `role`, `ancien_eleve`, `club`, `etablissement`, `dre`, `places_validees`,
    `badges` (rangs), `place_en_cours` (nulle si certifié), `tentatives_place`, `tentatives`, `debut`,
    `derniere_activite` et `certificat` (numéro du certificat valide, ou nul).
  - Le nom d'un élève n'est rendu qu'à un collaborateur national avec la double authentification active
    (`suivi.voit_les_noms`) ; `/certificats` et `/badges` suivent la même règle et le périmètre DRE (relecture).
  - **Inactif** : pas certifié, et aucune activité depuis 30 jours.
- `GET /statistiques` (périmètre du collaborateur) renvoie `StatistiquesCertification` :
  - `totaux` : candidats, actifs sur 30 jours, certifiés, et badges par rang (avec leur nom) ;
  - `entonnoir` : 20 lignes, chacune avec `place`, `quiz_publie`, `tentes`, `reussis`, `taux_reussite`
    (tentatives réussies sur tentatives terminées) et `tentatives_avant_reussite` (moyenne, nulle sans réussite) ;
  - `par_dre` : pour chaque DRE, candidats, badges et certifiés ;
  - `par_semaine` : les 12 dernières semaines, du lundi au dimanche (heure de Lomé, soit UTC), avec les nouveaux
    candidats et les nouveaux certifiés.
- `POST /candidats/export`
  - Corps : `{filtres, finalite}`.
  - Droit `inscrits : exporter` et périmètre national (`exiger_permission(..., national=True)`) ; sinon 403.
  - Renvoie un CSV au séparateur `;`, avec les cellules neutralisées comme dans `admin/exports.py`
    (`neutraliser`).
  - Limité comme les autres exports (`settings.export_lignes_max`) : au-delà, 422 « Trop de candidats : précise
    les filtres. ».
  - Journal : `export_suivi_certification`, avec la finalité, les filtres et le nombre de lignes.
  - Un POST plutôt qu'un GET : la finalité n'a pas sa place dans l'URL.

**Site.** La page `/admin/certification/suivi` (onglet « Suivi ») :

- en tête, des tuiles de chiffres ;
- l'entonnoir, en barres horizontales simples en CSS (20 lignes : tentés, réussis, taux, tentatives moyennes) ;
- un tableau par DRE ;
- un graphique par semaine (Recharts, déjà présent) ;
- la liste des candidats : filtres, recherche, pagination, tableau sur bureau et cartes à 375 px ;
- le bouton « Exporter », montré seulement aux collaborateurs nationaux qui ont le droit. Il ouvre une boîte qui
  demande la finalité.

## Dépendances

Aucune. Le document Word se lit avec la bibliothèque standard (`zipfile`, `xml.etree`) ; Recharts est déjà là.

## Sécurité

- **Droits** : chaque route vérifie `quiz : consulter` et applique le périmètre DRE dans la requête (ADR-0003,
  ADR-0008). L'export exige en plus `inscrits : exporter` et le périmètre national.
- **Données des élèves** (RULES, SECURITY) :
  - un collaborateur de DRE ne voit que le pseudonyme des élèves ;
  - l'export nominatif est national, motivé et journalisé ;
  - aucune route publique n'est ajoutée.
- **Injection CSV** : les cellules sont neutralisées (`=`, `+`, `-`, `@`).
- **Contenu** : les QCM viennent de documents officiels d'AIMES-AFRIQUE, chargés au nom du validateur, comme les
  100 défis. Le JSON de la sélection est relu avant la mise en prod (tâche de relecture dans `TASKS.md`).

## Tests

- **Import Word** : un petit document construit dans le test (gras sur une proposition), puis les refus (deux
  réponses en gras, ou 2 propositions). Le JSON du lot 7 a 78 QCM, 15 thématiques, 3 choix chacun, et des axes
  connus.
- **Sélection** (fonction pure, sur une banque fabriquée) :
  - les défis Expert passent d'abord, à parts égales ;
  - le complément vient du même lot ;
  - aucune question en double ;
  - chaque place a 10 questions ;
  - un axe qui n'a pas assez de questions est refusé.

  Puis, sur le JSON commité : 200 énoncés distincts, 10 par place, et l'axe de chaque place.

- **Migration** : sur une base de test avec une petite banque fabriquée :
  - le lot 7 est chargé et dépublié ;
  - 20 quiz de certification de 10 questions sont publiés ;
  - un quiz de test est dépublié, un vrai quiz reste ;
  - une seconde exécution ne change rien ;
  - le retour arrière s'applique ;
  - sans banque, rien n'est fait.
- **Suivi** :
  - un candidat apparaît dès sa première tentative, avec ses places, sa place en cours, ses tentatives et ses
    dates ;
  - les parties d'essai et les joueurs sans compte sont exclus ;
  - les filtres (DRE, club, rôle, états `inactif` et `certifie`) et la recherche fonctionnent ;
  - un certificat révoqué ne compte pas, un certificat réémis compte une fois ;
  - le périmètre DRE s'applique, avec le pseudonyme au lieu du nom ;
  - un refus 403 sans droit ;
  - l'entonnoir et ses moyennes, les chiffres par DRE et par semaine ;
  - l'export : 403 sans le droit ni le périmètre national, journal, neutralisation des cellules et limite.
- **Site** : le test du composant (tuiles, entonnoir, état vide, bouton d'export masqué sans droit), puis tsc, lint
  et build ; vérification au navigateur à 375 px et sur bureau.
- **Bout en bout** : un élève réussit la place 1 d'un quiz chargé, gagne +50, et la place 2 s'ouvre (un test de
  l'API).

## Risques

- **La banque de la prod diffère de la base locale.** L'équipe a pu corriger ou désactiver des QCM en prod. Le
  JSON reste celui qui a été relu ; une correction déjà faite en prod n'est pas reprise dans la certification.
  Accepté : l'équipe corrige dans l'éditeur des quiz.
- **Quiz de certification réels déjà publiés en préprod ou en prod.** Leurs places sont laissées telles quelles.
  La sortie de la migration le dit, à vérifier dans les journaux du déploiement.
- **Questions fixes et arrêt à la première erreur.** Un candidat finit par apprendre les 10 questions d'une place à
  force de reprises. C'est le comportement déjà en place (spec 034), hors périmètre ici.
- **Performance du suivi.** Les agrégats parcourent `tentative_quiz` filtrée sur les quiz de certification. Il
  faut ajouter un index `(joueur_id, quiz_id)` si l'`EXPLAIN` le demande. Celui de `(joueur_id, quiz_id, jour)`
  existe et devrait suffire.
