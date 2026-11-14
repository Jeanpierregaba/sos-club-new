# 035 — Plan technique

## Données

- `backend/alembic/donnees/etablissements_secondaire_1.json` : le fichier Excel converti une fois (nom, IESG, DRE,
  préfecture, ordre), en casse normale. Le script de conversion `backend/app/referentiel/import_secondaire.py`
  reste dans le dépôt pour une prochaine liste (lycées). L'Excel lui-même n'est pas commité.
- Casse : chaque mot prend une majuscule initiale ; restent en majuscules les sigles (CEG, CEGIL, CPL, CPI, CPC,
  CPP, CSS, EPP, CES, CEP, ISTI…) et les chiffres romains ; « de, du, des, d', et, la, le, les, l' » restent en
  minuscules au milieu du nom, sauf juste après le sigle (« CPL Les Bâtisseurs »). Les apostrophes et traits
  d'union du fichier sont gardés.
- Correspondance IESG : par nom normalisé, avec un alias « IESG AGOE NYIVE » → IESG Agoényivé. Une IESG inconnue
  fait échouer la conversion (et la migration).

## Modèle

- Type déduit du premier mot du nom (lycée, complexe, autre, collège sinon) ; accents des mots courants rétablis.
- `etablissement.prefecture` (texte 100, facultatif) et `etablissement.ordre` (énumération en texte, facultative) :
  `public`, `prive_laic`, `prive_catholique`, `prive_protestant`, `prive_islamique`, `communautaire`.
- `etablissement.import_source` (texte 40, facultatif) : `secondaire-1-2026` pour les lignes créées par l'import.
  Il sert au retour arrière (ne retirer que ce que l'import a créé) et à un filtre du back office.
- Index `ix_etablissement_prefecture` pour le filtre.

## Migration

1. Ajoute les trois colonnes.
2. Lit le JSON ; pour chaque ligne : IESG par nom normalisé ; si `(iesg_id, nom_normalise)` existe, met à jour
   préfecture et ordre (ni nom, ni statut) ; sinon, si un seul établissement de même nom normalisé existe dans la même DRE (IESG différente,
   comme Grand Kpendjal rangé sous Mango par le fichier), le met à jour de même ; sinon insère (type déduit du nom,
   statut `actif`, `import_source`).
   Une seule requête `INSERT … ON CONFLICT (iesg_id, nom_normalise) DO UPDATE SET prefecture, ordre`, en lots.
3. Retour : refuse (RuntimeError) si un établissement importé a un club, un élève ou un encadreur ; sinon supprime
   les lignes `import_source = 'secondaire-1-2026'`, puis les colonnes.

Les tests chargent l'annuaire par `referentiel.chargement.charger` (annuaire.json) : la migration y est vérifiée
dans un test dédié (montée sur une base contenant l'annuaire de test, comptes, casse, mise à jour d'un existant).

## API

- `schemas.py` : `prefecture` et `ordre` dans `EtablissementAdmin`, `EtablissementModification` et
  `EtablissementTrouve` (la recherche publique) ; pas dans l'annuaire public de la carte (poids).
- `GET /api/admin/referentiel/etablissements` : filtres `ordre`, `prefecture` (sans casse) et `importes` (créés par l'import).
- `PATCH /api/admin/referentiel/etablissements/{id}` : modifie préfecture et ordre (journal existant).
- `GET /api/referentiel/annuaire` : inchangé. Mesuré après import : 253 Ko, 0,15 s en local. Le cache prévu au
  départ est abandonné : l'API pose `no-store` partout (`main.py`), et le poids reste acceptable.

## Site

- Recherche d'établissement à l'inscription (élève, encadreur) : la préfecture en second texte sous le nom.
- `src/routes/_connecte/admin/referentiel.etablissements.tsx` : colonnes préfecture et ordre, filtres, champs de la
  fiche, libellés des ordres.
- Types de l'API régénérés.

## Activation des clubs

Aucun changement : `clubs.activation.club_de` crée le club d'un établissement à la première adhésion ou au premier
rattachement, et `recalculer` l'active au seuil (3 encadreurs, 21 élèves). Un test le vérifie sur un collège
importé.

## Risques

- Préfectures : graphie officielle (39 entrées, « Tône », « Agoè-Nyivé »), liste fermée dans le back office.
- `normaliser` est copiée dans la migration : une évolution du code ne change pas un rejeu.
- Doublons orthographiques (environ 140 noms proches) : acceptés, traités par l'équipe (filtre `import_source`).
- Poids de l'annuaire public : 253 Ko mesurés ; à surveiller si la liste des lycées s'ajoute.
- La spec 033 n'est pas encore commitée et touche aussi `referentiel/` : commit de la 033 avant celui de la 035.
