# 026 — Plan technique

## Approche

Comme les commentaires (spec 025), l'espace du président s'appuie sur le moteur de modération (ADR-0009). Deux
nouveaux types de contenu :

| Type         | Ce que c'est                             | Ce qui le distingue                                                        |
| ------------ | ---------------------------------------- | -------------------------------------------------------------------------- |
| `actualite`  | Un article au nom du club                | Mêmes champs, photos et étapes qu'un article ; signé du club ; aucun point |
| `fiche_club` | Une proposition de description et d'axes | Une proposition = un contenu ; l'approbation l'applique à la fiche du club |

Les deux portent le club dans une nouvelle colonne de l'en-tête, `contenu.club_id`.

**L'auteur d'un contenu du club est le président en place.** Le moteur, la rédaction des articles et les photos
(spec 024) retrouvent un contenu par son auteur (`contenu_de`). À la validation d'une passation (spec 019),
`auteur_id` des actualités et propositions du club passe au nouveau président, dans la même transaction. Ainsi :
tout le code des articles sert aux actualités sans copie, les notifications vont au président actuel, et
l'ancien président perd l'accès au même instant. L'historique ne perd rien : le journal garde qui a soumis chaque
version, et les décisions restent attachées aux versions.

L'alternative, vérifier la présidence à chaque accès sans toucher à `auteur_id`, demanderait de doubler chaque
fonction de rédaction et de photo (par auteur, par club), et d'envoyer les notifications au président actuel par
un réglage de plus dans le moteur.

Les droits de gestion se vérifient à chaque route par une dépendance `President` (président en place d'un club
actif), en plus de la propriété du contenu.

## Fichiers touchés

**API**

- `app/moderation/models.py` : `Contenu.club_id`, contraintes (voir Données).
- `app/moderation/types.py` : réglage `depublication` (une proposition de fiche ne se dépublie pas) ; les
  réglages `adresse`, `correction` et `a_la_publication` de la spec 025 servent tels quels.
- `app/moderation/decisions.py` : `depublier` refusé (409) si le type ne l'accepte pas ; `ElementFile.club` et
  `ApercuModeration.fiche_actuelle` (description et axes du club au moment de la lecture, pour l'avant / après) ;
  club bénéficiaire enregistré seulement pour un type qui rapporte des points.
- `app/articles/service.py`, `router.py`, `public.py` : rédaction paramétrée par le type (article ou actualité) ;
  liste et page publiques qui incluent les actualités (`nature`, signature `profil="club"`).
- `app/clubs/espace.py` (nouveau) : vue « Mon club » selon le profil (président, membre, encadreur rattaché),
  propositions de fiche (proposer, retirer, application à l'approbation), dépendance `President`.
- `app/clubs/actualites.py` (nouveau) : type `actualite`, routes de rédaction sous `/clubs/moi/actualites` (mêmes
  opérations que `/mes-articles`, photos comprises).
- `app/clubs/verification.py` : `valider_passation` transfère `auteur_id` des contenus du club.
- `app/clubs/schemas.py`, `router.py` : `EspaceClub`, `PropositionFiche`, actualités publiées dans `ClubFiche`.
- Migration Alembic `contenus_du_club`.
- `app/seed_dev.py` : une actualité publiée et une proposition de fiche en attente.

**Site**

- `src/routes/_connecte/mon-club.tsx` (nouveau) : tableau de bord ; gestion pour le président, lecture pour les
  autres. Un encadreur choisit le club parmi ses rattachements (`?club=`).
- `src/routes/_connecte/mon-club.actualites.nouveau.tsx` et `mon-club.actualites.$id.tsx` : l'éditeur des articles
  (`Editeur.tsx` et `Photos.tsx`), paramétré par le type.
- `src/components/clubs/PropositionFiche.tsx` : formulaire description et axes, état de la proposition.
- `src/routes/clubs.$id.tsx` : actualités publiées sur la fiche.
- `src/routes/articles.index.tsx`, `src/components/articles/PageArticle.tsx` : mention « Actualité du club ».
- `src/routes/_connecte/admin/moderation.tsx` : types `actualite` et `fiche_club` (avant / après de la fiche).
- `src/components/clubs/BlocClub.tsx` : lien « Mon club » ; les demandes passent dans « Mon club ».

**Docs** : ADR-0009 (note : `club_id`, auteur = président en place), `ARCHITECTURE.md`, `SECURITY.md`,
`TASKS.md`, `SESSION-LOG.md`.

## Données

Migration non destructive :

- `contenu.club_id` : UUID nul, clé étrangère vers `club.id` (`ON DELETE RESTRICT`), index `(club_id, type)`.
- Contrainte `contenu_du_club` : `(type IN ('actualite', 'fiche_club')) = (club_id IS NOT NULL)`.
- Contrainte `adresse_si_publie` élargie : une proposition de fiche publiée n'a pas d'adresse
  (`… OR type = 'fiche_club'`).
- Index partiel unique `uq_contenu_fiche_en_attente (club_id) WHERE type = 'fiche_club' AND etat = 'en_attente'` :
  une seule proposition en attente par club, même sous concurrence.

Aucune ligne de barème : ni l'actualité ni la fiche ne rapportent de points.

## API / interfaces

| Méthode et route                                                          | Qui                                         | Effet                                                                   |
| ------------------------------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------- |
| `GET /clubs/{id}/espace`                                                  | président, membre actif, encadreur rattaché | Vue du club ; demandes et suivi pour le président seul ; 404 sinon      |
| `POST /clubs/moi/fiche`                                                   | président                                   | `{description, axes}` → proposition en attente ; 409 si une autre l'est |
| `DELETE /clubs/moi/fiche/{id}`                                            | président                                   | Retire la proposition en attente                                        |
| `/clubs/moi/actualites` (+ `/{id}`, `/soumettre`, `/retirer`, `/photos…`) | président                                   | Comme `/mes-articles`, pour le club                                     |
| `GET /clubs/{id}`                                                         | tout le monde                               | Fiche, avec les 6 dernières actualités publiées                         |
| `GET /articles`, `GET /articles/{adresse}`                                | tout le monde                               | Articles et actualités ; `nature` et signature du club                  |
| File, aperçu, décisions                                                   | modérateurs                                 | Inchangés ; `corriger` et `depublier` refusés pour une fiche            |

À l'approbation d'une proposition de fiche (`a_la_publication`), sous le verrou du club : le club doit être
actif (sinon 409), sa description et ses axes sont remplacés, et le journal garde l'avant et l'après.

## Dépendances

Aucune.

## Sécurité

- Droits dans l'API pour chaque route (ADR-0003) : dépendance `President` pour toute gestion ; vue du club
  réservée aux membres actifs, aux encadreurs rattachés actifs et au président ; 404 pour les autres.
- Une actualité ne montre jamais le nom ni le pseudonyme du président : signature du club seulement.
- Rien de public avant l'approbation : listes, fiche, adresse et photos ne lisent que `version_publiee_id`.
- Passation : le transfert d'auteur se fait dans la transaction de la validation ; l'ancien président reçoit
  404 dès qu'elle est validée.
- Le périmètre DRE vient de l'établissement du club, copié à la soumission comme pour un article.

## Tests

Parties critiques (droits, modération, `docs/TESTING.md`) écrites **avant** le code :

- `test_espace_club.py` : vue selon le profil (président, membre, encadreur rattaché, autre élève, ancien membre),
  aucune donnée de gestion pour les non-présidents.
- `test_fiche_club.py` : proposition, une seule en attente (y compris deux envois simultanés), validation
  (422), retrait, approbation qui change la fiche publique, refus, club suspendu, `corriger` et `depublier` → 409,
  périmètre DRE.
- `test_actualites.py` : rédaction, photos, soumission, rien de public avant l'approbation, signature du club,
  mention dans `/articles`, aucun point, actions refusées aux membres et encadreurs, passation (le nouveau
  président gère, l'ancien reçoit 404).
- Non-régression : suites des articles, des photos, des commentaires et des clubs.
- Site : tests Vitest de « Mon club » (président et membre) et de la proposition de fiche.

## Risques

- **Transfert d'auteur à la passation** : `auteur_id` d'une actualité ne désigne plus forcément l'élève qui l'a
  écrite. C'est voulu (l'auteur est le club) et documenté dans l'ADR-0009 ; le journal garde l'historique.
- **Rédaction paramétrée** : les articles changent de code ; leurs tests (specs 023 et 024) restent le garde-fou.
- **Taille** : spec plus grande que les précédentes ; découpée en tâches livrables une à une (API d'abord).
