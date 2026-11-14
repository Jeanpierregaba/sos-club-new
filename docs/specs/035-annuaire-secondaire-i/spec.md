# 035 — Annuaire national des établissements du Secondaire I

> Source : « 2. LISTE DES ETABLISSEMENTS DU SECONDAIRE 1.xlsx », transmise le 2026-11-12 par le porteur du projet,
> à la suite de la spec 033 (activation des clubs). Décisions du 2026-11-12 : création à part de tout nom non
> identique, noms en casse normale, préfecture et ordre en base et dans le back office, rien n'est retiré.

## Objectif

Tous les établissements du Secondaire I du Togo (2 396, 18 IESG, 7 DRE) doivent pouvoir être choisis à
l'inscription d'un élève ou d'un encadreur. Un établissement n'a pas besoin d'être déclaré à la main : dès que ses
membres atteignent le seuil de la spec 033 (3 encadreurs actifs et 21 élèves), son club s'active tout seul.

## Comportement attendu

1. **Import.** Chaque ligne du fichier devient un établissement actif rattaché à son IESG (« IESG AGOE NYIVE » =
   IESG Agoényivé). Son type se déduit du premier mot : lycée (« LYCEE », « LPL »), complexe (« COMPLEXE », « CS »,
   « CSI », « CSPL », « GROUPE »), autre (centre, institut, école…), collège sinon. Son nom est écrit en casse
   normale, sigles gardés en majuscules et accents des mots courants rétablis : « CPL LES BÂTISSEURS » devient
   « CPL Les Bâtisseurs », « LYCEE HANYIGBA » devient « Lycée Hanyigba ».
2. **Déjà présent.** Si l'annuaire a déjà un établissement de même nom (après normalisation : accents, casse)
   dans la même IESG, il n'est pas recréé : il reçoit la préfecture et l'ordre du fichier, son nom ne change pas.
   De même s'il est seul de ce nom dans la même DRE mais rangé sous une autre IESG (le fichier range sous Mango
   les établissements que l'annuaire place sous Grand Kpendjal).
3. **Nom proche.** Un nom seulement ressemblant (« CEG DASSOUTE-NANIK » / « CEG Dassouté Nank ») est créé à part.
   L'équipe repère et traite les doublons dans le back office.
4. **Préfecture et ordre.** Chaque établissement importé porte sa préfecture, dans sa graphie officielle
   (« Tône », « Agoè-Nyivé »), et son ordre
   d'enseignement : Public, Privé laïc, Privé catholique, Privé protestant, Privé islamique, Communautaire.
5. **Inscription.** La recherche d'établissement (élève, encadreur) trouve les nouveaux collèges ; la préfecture
   s'affiche sous le nom pour distinguer deux homonymes.
6. **Back office.** La liste des établissements montre la préfecture et l'ordre, et se filtre par ordre et par
   préfecture. L'équipe peut corriger les deux champs sur la fiche.
7. **Activation.** Rien ne change au moteur de la spec 033 : le club d'un collège importé naît « en constitution »
   à la première adhésion ou au premier rattachement, puis s'active au seuil.
8. **Absents du fichier.** Les établissements de l'annuaire actuel absents du fichier (lycées, complexes, 194
   collèges) restent actifs, inchangés.

## Critères d'acceptation

- [x] Après la migration, chaque ligne du fichier correspond à un établissement actif de l'IESG indiquée : 2 396
      lignes, sans doublon de nom normalisé dans une même IESG.
- [x] Un établissement déjà présent sous le même nom normalisé n'est pas dupliqué ; il reçoit préfecture et ordre,
      et garde son nom, son identifiant, son club et ses membres.
- [x] Les noms importés sont en casse normale, sigles (CEG, CEGIL, CPL, CPI, CPC, CPP, CSS…) et chiffres romains
      en majuscules.
- [x] `GET /api/referentiel/etablissements?recherche=…` trouve un collège importé et renvoie sa préfecture.
- [x] `GET /api/admin/referentiel/etablissements?ordre=prive_islamique&prefecture=…` filtre ; la fiche modifie
      préfecture et ordre, avec journal.
- [x] Un élève inscrit dans un collège importé crée son club « en constitution » ; avec 3 encadreurs actifs et
      21 élèves, le club devient actif (moteur de la spec 033).
- [x] La migration se rejoue (montée, retour, montée) ; le retour ne retire que les établissements créés par
      l'import et refuse si l'un d'eux a déjà un club, un élève ou un encadreur. Ce retour supprime des lignes
      (exception à `docs/RULES.md`) : en preprod ou en prod, il ne se lance qu'avec l'accord du porteur.
- [x] Aucun établissement existant n'est désactivé ni renommé.

## Cas limites et erreurs

- **IESG du fichier inconnue** : la migration échoue avec le nom fautif (rien n'est importé à moitié).
- **Deux lignes identiques dans le fichier** (même nom normalisé, même IESG) : une seule ligne en base.
- **Ordre ou préfecture vides** : l'établissement est importé, champ vide.
- **Établissement existant inactif ou « proposé »** au même nom : il reçoit préfecture et ordre, son statut ne
  change pas (un « proposé » reste à valider par l'équipe).
- **Annuaire public plus lourd** (`/api/referentiel/annuaire`, environ 2 800 établissements) : 253 Ko, 0,15 s en
  local. L'API interdit tout cache (`no-store`, règle générale) : pas d'exception ici tant que le poids reste bas.

## Hors périmètre

- Les lycées (Secondaire II) : un autre fichier, s'il existe.
- La fusion automatique des noms proches et la fusion d'un doublon actif qui a déjà des membres : l'équipe
  désactive les doublons ; un outil de fusion fera l'objet d'une spec si le besoin se confirme.
- L'affichage public de l'ordre ou de la préfecture.
- Tout changement des seuils ou du moteur d'activation (spec 033).

## Questions ouvertes

Aucune.
