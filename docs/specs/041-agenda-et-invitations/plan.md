# 041 — Plan technique

## Approche

Un nouveau domaine `agenda` dans l'API. Un événement de club suit le chemin des rapports (spec 038) : c'est un
**type du moteur de modération** (`evenement`, ADR-0009). Le moteur fournit le brouillon, la version soumise
figée, les décisions motivées sous verrou, la file par DRE, l'auteur qui ne décide jamais du sien, les
notifications, et le crédit de points « une fois » à la première approbation.

Ce que la base doit filtrer, trier, compter ou rendre unique vit dans une table d'**en-tête** `evenement`, une
ligne par événement :

- le niveau, le club ou la DRE ;
- la date de début et de fin, le type, l'axe ;
- les places, l'annulation, le rappel envoyé.

**Une seule table publique.** L'agenda public ne lit que `evenement`, jamais les versions :

- un événement de club y recopie les champs de sa version **à chaque approbation**, par un nouveau crochet
  du moteur `a_chaque_approbation` (`a_la_publication` ne part qu'à la première : `decisions.py:393`) ;
- un événement national ou régional n'a pas de contenu : l'équipe écrit directement dans `evenement`, publié à
  la création ;
- les textes publiés (titre, objectif, description, lieu, lien, public) sont donc des colonnes de `evenement`,
  copie de la version approuvée ;
- un brouillon ou une version en attente n'y écrit rien : rien n'est public avant l'approbation (RULES), et une
  route publique ne peut pas fuiter un brouillon.

**Invitations calculées.** Les invités sont les membres dont l'adhésion au club est active, lus à chaque fois.
Aucune ligne n'est écrite par invitation. Une table `reponse_evenement` ne garde que les réponses et le pointage.

- Un élève qui rejoint le club voit les événements à venir dans « Mes événements », sans notification.
- Un élève qui part n'est plus compté.
- Cela évite toute synchronisation avec les affiliations, les passations et les suspensions.

**Notifications.** Elles passent par `notifications.notifier`, dans la transaction de l'action :

- l'invitation, à la première approbation ;
- le changement de date ou de lieu ;
- l'annulation.

Le rappel de la veille passe par une commande quotidienne, comme les échéances des clubs (`app.clubs.echeances`,
cron du VPS).

**Droit de décision par type.** Le moteur exige « modération : approuver » pour tout type. `TypeContenu` gagne un
champ facultatif `domaine_droit`. Pour `evenement` (« agenda »), décider exige en plus « agenda : approuver », et
retirer du site « agenda : dépublier ». Les autres types ne changent pas.

## Fichiers touchés

**Créés (API)**

- `backend/app/agenda/models.py` : `Evenement`, `ReponseEvenement`, les énumérations `NiveauEvenement`,
  `TypeEvenement` et `Reponse`.
- `backend/app/agenda/types.py` : la déclaration du type `evenement` dans le moteur (schéma `ChampsEvenement`,
  `actions_auteur={encadreur: "encadreur.evenement"}`, crochets de publication et destinataires).
- `backend/app/agenda/service.py` : les droits du club, la création, la soumission, la recopie à l'approbation,
  l'annulation, les réponses, le pointage et les lectures publiques.
- `backend/app/agenda/administration.py` : les événements nationaux et régionaux de l'équipe.
- `backend/app/agenda/rappels.py` : la commande `python -m app.agenda.rappels`.
- `backend/app/agenda/schemas.py`, `router.py` (public et membres), `router_admin.py`.
- La migration Alembic `agenda_et_invitations`.
- `backend/tests/test_agenda_club.py`, `test_agenda_reponses.py`, `test_agenda_public.py`, `test_agenda_admin.py`,
  `test_agenda_rappels.py`.

**Modifiés (API)**

- `app/moderation/models.py` : les CHECK `adresse_si_publie` et `contenu_du_club` acceptent `evenement` (club
  obligatoire, pas d'adresse : la page publique est `/agenda/<id>` de l'en-tête).
- `app/moderation/types.py` : le champ `domaine_droit`.
- `app/moderation/router.py` ou `decisions.py` : la vérification du droit du domaine.
- `app/rapports/models.py`, `service.py`, `schemas.py` : la colonne `evenement_id` du rapport et sa vérification à
  la soumission.
- `app/main.py` : les routeurs.
- `alembic/env.py` : l'import des modèles.
- `app/seed_dev.py` : deux événements de club publiés, un national et un en attente.
- `openapi.json`.

**Créés et modifiés (site)**

- `src/routes/agenda.tsx` : réécrit sur l'API. La liste à venir, puis passée, par section, et des filtres dans
  l'URL (`?dre=&club=&type=&axe=`).
- `src/routes/agenda.$id.tsx` : la page d'un événement, avec la réponse d'un membre connecté.
- `src/components/AgendaSidebar.tsx` : les trois prochains événements, ou « Aucun événement à venir ».
- `src/routes/_connecte/mon-club.agenda.*` : l'agenda du club (encadreurs et président). Il comprend la liste,
  le nouveau brouillon, la modification, la soumission, l'annulation, les réponses et le pointage des présents.
- `src/routes/_connecte/mes-evenements.tsx` : les invitations et les réponses de l'élève.
- `src/routes/_connecte/admin/agenda.tsx` : les événements nationaux et régionaux. La file de décision reste
  `/admin/moderation`.
- `src/components/agenda/*` : `CarteEvenement`, `FormulaireEvenement`, `ChoixReponse`, `ListeReponses`,
  `Pointage`, avec leurs tests.
- Le formulaire de rapport : le choix facultatif d'un événement du club.
- Les liens « Agenda du club » dans « Mon club » et « Mes événements » dans l'en-tête de l'espace élève.
- `src/lib/api/client.ts`, `schema.gen.ts`, `src/lib/agenda.ts` (les libellés).

## Données

Migration **non destructive** : deux tables neuves, une colonne nullable sur `rapport` et deux contraintes
élargies sur `contenu`.

**`evenement`**

- **Identité et rattachement :**
  - `id` ;
  - `contenu_id` : FK `contenu`, unique, nul pour un événement national ou régional ;
  - `niveau` : `national`, `regional` ou `club` ;
  - `club_id` : FK `club`, obligatoire si et seulement si `club` ;
  - `dre_code` : FK `dre`, obligatoire si `regional` ou `club`, copiée de l'établissement du club.
- **Description :**
  - `type` (texte contrôlé) et `axe_code` (FK `axe`, nul permis pour le national) ;
  - `titre`, `objectif`, `description`, `lieu`, `en_ligne` (booléen), `lien` (`https://` seulement), `public_vise`.
- **Dates et places :**
  - `debut` et `fin` en `timestamptz`, avec CHECK `fin > debut` ;
  - `places` : entier ≥ 1, nul s'il n'y a pas de limite.
- **Publication et suivi :**
  - `publie` : booléen. Un événement de club passe vrai à la première approbation et faux s'il est retiré du
    site.
  - `annule_le`, `annule_par`, `motif_annulation`, avec CHECK `motif` si annulé ;
  - `rappel_pour` (`date`) : la date de l'événement à laquelle le rappel est parti, pour ne pas l'envoyer deux
    fois ;
  - `cree_par`, `cree_le`, `modifie_le`.
- **Index :**
  - `(publie, debut)` ;
  - `(club_id, debut)` ;
  - `(dre_code, debut)`.

**`reponse_evenement`**

- **Colonnes :**
  - `evenement_id` et `eleve_id` : la clé primaire composée ;
  - `reponse` : `participe`, `peut_etre` ou `non`, nulle si l'élève n'a pas répondu mais a été pointé ;
  - `repondu_le` ;
  - `present` : booléen nul tant que l'élève n'est pas pointé, avec `pointe_par` et `pointe_le`.
- **Index partiel :** `(evenement_id) WHERE reponse = 'participe'`, pour le compte des participants.

**`rapport.evenement_id`** : FK `evenement`, nullable, avec un **index unique partiel** sur les rapports non
refusés. Un événement n'est lié qu'une fois, et la base le tranche sous concurrence.

**Contraintes du moteur** : `evenement` est ajouté à la liste de `adresse_si_publie` et à celle de
`contenu_du_club`.

**Heures** : saisies au format local `YYYY-MM-DDTHH:MM`, interprétées en `Africa/Lome` (UTC+0, sans heure d'été)
avec `zoneinfo`, stockées en UTC et renvoyées en ISO avec fuseau. Le site affiche avec `timeZone: "Africa/Lome"`.

## API / interfaces

| Route                                                          | Qui                                                       | Rôle                                                                                                                                   |
| -------------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /api/agenda?dre=&club=&type=&axe=&periode=a_venir\|passe` | public                                                    | Événements publiés, paginés, avec le club et l'établissement, le nombre de participants, « Complet » et « Annulé ». Aucun nom d'élève. |
| `GET /api/agenda/{id}`                                         | public                                                    | Un événement publié (404 sinon). Pour un membre connecté du club : sa réponse.                                                         |
| `GET /api/agenda/prochains`                                    | public                                                    | Les 3 prochains, pour l'accueil.                                                                                                       |
| `PUT /api/agenda/{id}/reponse`                                 | membre actif du club                                      | `{reponse}` ; 403 hors du club, 409 si commencé ou complet (verrou `FOR UPDATE` sur l'événement).                                      |
| `GET /api/agenda/mes-evenements`                               | élève                                                     | Les événements à venir de son club et ses réponses.                                                                                    |
| `GET /api/clubs/moi/agenda`                                    | encadreur actif rattaché, président                       | Les événements du club, tous états.                                                                                                    |
| `POST /api/clubs/moi/agenda`                                   | idem                                                      | Crée un brouillon (contenu + en-tête), auteur = l'appelant.                                                                            |
| `PUT /api/clubs/moi/agenda/{id}`                               | l'auteur, encore habilité                                 | Modifie la version de travail.                                                                                                         |
| `POST /api/clubs/moi/agenda/{id}/soumettre`                    | l'auteur                                                  | Soumet (moteur), 422 si la date est passée ou incohérente.                                                                             |
| `POST /api/clubs/moi/agenda/{id}/annuler`                      | encadreur du club, président                              | `{motif}` 10 à 200 caractères ; notifie les invités.                                                                                   |
| `GET /api/clubs/moi/agenda/{id}/reponses`                      | encadreur du club, président                              | La liste nominative et les totaux, `Cache-Control: no-store`.                                                                          |
| `PUT /api/clubs/moi/agenda/{id}/presences`                     | encadreur du club, président                              | `{eleve_id: present}` ; après le début, au plus 30 jours après, membres du club seulement.                                             |
| `GET/POST /api/admin/agenda`, `PUT /api/admin/agenda/{id}`     | `agenda : consulter / créer / modifier`, DRE              | Événements nationaux et régionaux, publiés à la création, journalisés (`evenement_cree`, `evenement_modifie`).                         |
| `POST /api/admin/agenda/{id}/annuler`                          | `agenda : modifier`, ou `agenda : dépublier` pour un club | Annulation par l'équipe, journalisée (`evenement_annule`).                                                                             |

Les décisions sur un événement de club passent par les routes existantes de `/api/admin/moderation`, avec le
droit du domaine en plus.

## Dépendances

Aucune nouvelle :

- `zoneinfo` fait partie de la bibliothèque standard ;
- la base de fuseaux est déjà présente dans l'image Python. **À vérifier dans l'image Docker de l'API.** Si elle
  manque, `Africa/Lome` étant UTC+0 sans heure d'été, un fuseau fixe `timezone.utc` suffit, avec un commentaire.

## Sécurité

- **Droits vérifiés dans l'API sur chaque route (ADR-0003) :**
  - membre actif pour répondre ;
  - encadreur **actif et rattaché** au club, ou président en place, pour l'agenda du club ;
  - périmètre DRE pour l'équipe.
- **RULES :**
  - aucune route publique n'expose de nom, de pseudonyme ou de contact d'élève, seulement des comptes ;
  - la liste des réponses porte `no-store` et n'est lue que par le club et l'équipe habilitée.
- **Rien de public avant l'approbation :** les routes publiques filtrent `publie` ; les brouillons n'écrivent pas
  dans `evenement` publié.
- **Textes en texte brut :**
  - rendus par React sans `dangerouslySetInnerHTML` ;
  - le lien `https://` seulement (validé par Pydantic `HttpUrl` et le schéma), affiché avec
    `rel="noopener noreferrer"`.
- **Visuel :** il passe par les photos du moteur (spec 024, ADR-0010), avec ré-encodage et sans métadonnées. Pas
  de visuel pour le national en v1.
- **Concurrence :**
  - places sous verrou de l'événement ;
  - lien rapport–événement sous index unique ;
  - crédit +30 par la clé du registre `evenement:<contenu>`.
- **Journal :** toute action de l'équipe est journalisée ; l'annulation d'un club l'est aussi (`evenement_annule`).

## Tests

TDD pour les parties critiques de `docs/TESTING.md` (droits, points, données d'élèves).

- **Club :**
  - qui crée et soumet ;
  - rien de public avant l'approbation ;
  - +30 une seule fois, rien au président ;
  - invitations notifiées aux membres actifs seulement ;
  - modification republiée sans recrédit ;
  - changement de date notifié.
- **Droits de décision :**
  - « modération : approuver » sans « agenda : approuver » donne 403 ;
  - un auteur ne décide pas du sien.
- **Réponses :**
  - membre seulement ;
  - fin au début de l'événement ;
  - complet, y compris deux réponses simultanées sur la dernière place (deux sessions) ;
  - un membre parti n'est plus compté.
- **Public :**
  - filtres ;
  - aucun nom d'élève dans les réponses JSON (recherche du prénom, du nom et du pseudonyme d'un élève inscrit) ;
  - annulé marqué ;
  - les 3 prochains.
- **Équipe :** droits, périmètre DRE, journal.
- **Rappels :** la veille seulement, à ceux qui participent ; pas deux fois ; pas pour un annulé ; renvoyé après
  un report à une autre date.
- **Rapports :** lien à un événement publié du club ; refus d'un événement déjà lié, d'un autre club ou non
  publié.
- **Heures :** une saisie à Lomé redonne la même heure.
- **Site :** Vitest des composants (choix de réponse, complet, formulaire et ses erreurs, liste des réponses,
  pointage). Vérification au navigateur à 375 px et en bureau.

## Risques

- **Recopie à l'approbation :** le crochet `a_chaque_approbation` est un ajout au moteur, appelé après la
  validation de la version ; testé par une modification republiée et par les types existants inchangés.
- **Droit par type :** la file de modération doit aussi masquer les événements à un modérateur sans « agenda :
  approuver », ou les montrer sans boutons. Le plan retient de **les montrer en lecture seule**.
- **Suite API longue (42 min) :** les nouveaux tests ajoutent deux tables à tronquer. On garde les tests ciblés
  pendant les tâches, et la suite complète à la fin.
- **Données réelles :** l'agenda ne contient aucune donnée personnelle publique. Les réponses et le pointage
  sont des données d'élèves : à mentionner dans la déclaration IPDCP (Q9) avec la fiche.
