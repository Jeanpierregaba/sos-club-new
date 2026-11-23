# 051 — Plan technique

## Principe

Deux sources, jamais mélangées :

1. **La base existante**, lue au moment de la demande comme le tableau de bord (`app/admin/tableau_de_bord.py`) :
   comptes, parties (`tentative_quiz`), certification (`place_reussie`, `badge_obtenu`, `certificat`), défi du jour
   (`defi_reponse`), étoiles, partages, clubs, référentiel. Aucune nouvelle collecte pour ces chiffres.
2. **Un nouveau domaine `app/activite/`** pour ce que la base ne garde pas : pages vues, clics, étapes d'inscription,
   téléchargements, erreurs, recherches. Événements anonymes, gardés 90 jours, puis totaux par jour.

Aucune dépendance nouvelle : FastAPI, SQLAlchemy et, côté site, `navigator.sendBeacon` et les graphiques déjà
utilisés par l'admin (à vérifier en tâche 6 ; sinon des barres en CSS, sans bibliothèque).

Décision structurante (mesure d'audience sans cookie, empreinte du jour, données d'un public mineur) :
**ADR-0014 — Mesure d'audience interne et anonyme**.

## Modèle de données (migration Alembic)

**`sel_activite`** — `jour` (date, clé primaire), `sel` (32 octets aléatoires). Une ligne par jour, créée au premier
événement ; celles des jours passés sont effacées par la purge. Sans le sel, l'empreinte d'hier ne se recalcule pas.

**`evenement_activite`** — les événements bruts, 90 jours :

| Colonne      | Type         | Contenu                                                                                                          |
| ------------ | ------------ | ---------------------------------------------------------------------------------------------------------------- |
| `id`         | UUID         |                                                                                                                  |
| `cree_le`    | timestamptz  | à la seconde                                                                                                     |
| `jour`       | date         | jour de Lomé, pour les regroupements                                                                             |
| `type`       | texte (enum) | `page_vue`, `clic_inscription`, `etape_inscription`, `telechargement`, `erreur`, `recherche`                     |
| `visiteur`   | texte(16)    | empreinte du jour : `sha256(sel du jour ‖ IP ‖ User-Agent)` tronquée ; jamais l'IP                               |
| `chemin`     | texte(120)   | gabarit de la route (`/quiz/$id`), jamais les paramètres ni l'identifiant                                        |
| `detail`     | texte(60)    | selon le type : endroit du clic, profil et étape, code d'erreur, mot cherché…                                    |
| `provenance` | texte(30)    | catégorie : `direct`, `recherche`, `facebook`, `whatsapp`, `tiktok`, `youtube`, `autre`, ou `utm_source` nettoyé |
| `appareil`   | texte(10)    | `telephone`, `tablette`, `ordinateur`                                                                            |
| `navigateur` | texte(20)    | famille seulement (`chrome`, `safari`…)                                                                          |
| `connecte`   | bool         | une session valide accompagnait l'événement (sans dire laquelle)                                                 |

Index sur (`jour`, `type`). Pas de clé étrangère vers `utilisateur` : rien ne relie un événement à un compte.

**`total_activite_jour`** — (`jour`, `type`, `chemin`, `detail`, `provenance`, `appareil`) → `evenements`,
`visiteurs`. Rempli par la purge pour les jours qui sortent des 90 jours ; les requêtes de la page lisent l'union des
deux tables, pour que les totaux ne changent pas à la purge.

**`presence_semaine`** — (`utilisateur_id`, `semaine` lundi) en clé primaire, `ON DELETE CASCADE`. Écrite au plus
une fois par semaine et par compte, à la lecture de la session (`utilisateur_courant`), par un `INSERT … ON CONFLICT
DO NOTHING`. Sert seulement à la rétention (cohorte = semaine de `utilisateur.cree_le`) ; seules des parts sont
affichées. Effacée après 26 semaines par la purge. Le journal des sessions ne suffit pas : une session dure 30 jours
et une déconnexion l'efface.

**`recherche_activite`** — rien de plus : les recherches sont des événements `recherche`, et la page n'affiche un mot
que s'il compte au moins 3 empreintes différentes ; la purge efface tout mot sous ce seuil, et le total quotidien ne
garde que les mots au-dessus.

## API

**Collecte, publique** — `POST /api/activite/evenements` (routeur `app/activite/router.py`) :

- Corps : `{type, chemin, detail?, referent?, utm_source?}`, validé par Pydantic : type dans la liste, chemin
  ramené à son gabarit par une liste blanche des routes du site (sinon `autre`), longueurs bornées, `detail` dans
  une liste fermée par type (sauf `recherche` : 60 caractères, minuscules, sans chiffres longs pour exclure
  téléphones et codes).
- L'API calcule elle-même empreinte, appareil, navigateur et provenance à partir des en-têtes ; le `referent` n'est
  gardé que sous forme de catégorie.
- N'enregistre rien et répond 204 si : `Sec-GPC: 1` ou `DNT: 1`, User-Agent de robot, session d'un compte `admin`,
  mode maintenance. Répond toujours 204 en cas de succès, 422 si le corps est invalide.
- Limite de débit par IP via `app/comptes/limite_adresse.limiter` (préfixe `ACTIVITE`, plafond 120 par fenêtre).

**Événements côté serveur**, sans passer par le site, là où l'API voit déjà l'action :

- `etape_inscription` `envoye`, `refuse:<motif>`, `cree` dans `app/comptes/inscription.py`, `app/visiteurs` et
  `app/encadreurs` ; `confirme` (code du visiteur), `verifie` (encadreur), `premiere_connexion` (session créée pour
  un compte sans session précédente).
- `telechargement` dans la route `/api/bibliotheque/{id}/fichier` (`detail` = `lire` ou `telecharger`, `chemin` =
  `/bibliotheque/<titre court>`).
- `erreur` 500 dans le gestionnaire d'exceptions de `main.py`.

Ces appels passent par une fonction `activite.enregistrer(db, request, type, …)` qui applique les mêmes exclusions
et n'échoue jamais : une erreur du suivi est journalisée et ignorée, l'action de l'utilisateur continue.

**Lecture, super-administrateur** — `GET /api/admin/activite?du=&au=` avec `exiger_super_admin_pour("activite:voir")`
(refus journalisé comme les autres) et `GET /api/admin/activite/export.csv?bloc=…`. Une réponse par bloc pour que la
page s'affiche bloc par bloc : `…/audience`, `…/inscription`, `…/jeux`, `…/certification`, `…/contenus`,
`…/regions`, `…/retention`, `…/erreurs`. Chaque réponse porte la période et la période précédente. Période limitée à
366 jours.

Calculs dans `app/activite/indicateurs/<bloc>.py`, en SQL agrégé (`GROUP BY`), jamais en boucle Python sur les
lignes.

**Purge** — `app/activite/purge.py` : `purger_regulierement()` ajoutée au `lifespan` de `main.py` comme les autres
purges (toutes les heures) : agrège puis efface les événements de plus de 90 jours, efface les sels des jours passés,
les mots de recherche sous le seuil, et les présences de plus de 26 semaines. Idempotente.

## Site

- **`src/lib/activite.ts`** : `signaler(type, donnees)` envoie par `navigator.sendBeacon` (repli `fetch` avec
  `keepalive`), sans attendre ni afficher d'erreur. Ne fait rien côté serveur (SSR) ni si `navigator.globalPrivacyControl`.
- **Pages vues** : dans `src/routes/__root.tsx`, un abonnement à `router.subscribe("onResolved")` envoie le gabarit
  de la route (`match.routeId`), le `document.referrer` à la première page et l'`utm_source` de l'URL.
- **Clics d'inscription** : un composant `LienInscription` remplace les liens vers `/inscription` (accueil, Jeux,
  certification, menu, pied de page, connexion) et porte l'endroit (`accueil-hero`, `menu`…).
- **Étapes d'inscription côté site** : `ouvert` (profil choisi), `commence` (premier champ modifié), dans les trois
  composants `src/components/inscription/Inscription*.tsx`.
- **Recherches** : `ChoixEtablissement` (aucun résultat) et la carte des clubs (aucun résultat), après 1 seconde sans
  frappe.
- **404** : le `notFoundComponent` signale `erreur` `404`, avec pour chemin le premier segment de l'adresse demandée
  (`/ancienne-page`) s'il ne ressemble ni à un code ni à un identifiant, sinon `autre`.
- **Page `src/routes/_connecte/admin/activite.tsx`** : sélecteur de période, 8 sections chargées séparément, cartes
  de chiffres avec écart à la période précédente, courbes et barres, tableaux, carte du Togo par DRE (réutiliser la
  carte de `carte-des-clubs` si elle a un découpage par région, sinon un tableau trié et des barres), heatmap 7 × 24
  en grille CSS, bouton CSV par bloc, mentions des limites (bloqueurs, IP partagée). Lien dans le menu admin pour le
  super-administrateur seulement.
- Types régénérés (`export_openapi`, `api:types`).

## Sécurité et données personnelles

- Aucune IP, aucun identifiant de compte dans les événements ; empreinte non réversible dès que le sel du jour est
  effacé ; présence hebdomadaire seule donnée liée à un compte, effacée avec lui et après 26 semaines.
- Chemins en liste blanche : un code de carte (`/carte/$code`) ou un jeton de mot de passe n'est jamais stocké.
- Collecte publique mais bornée : schéma fermé, débit limité, aucune donnée renvoyée.
- Lecture réservée au super-administrateur, export agrégé seulement, journalisé (`activite:exporter`).
- `docs/SECURITY.md` : nouvelle ligne « Mesure d'audience (spec 051) » ; `docs/PRD.md` : mention dans les questions
  sur les données personnelles (à déclarer avec le reste à l'IPDCP, Q9).

## Tests

- API : empreinte identique le même jour, différente le lendemain ; sel effacé ; exclusions (GPC, DNT, robot,
  admin) ; schéma refusé ; liste blanche des chemins ; débit ; chaque indicateur sur un jeu de données construit
  (y compris période vide) ; agrégation à 90 jours sans changement des totaux ; 403 pour un non-super-admin ;
  export sans colonne par personne ; un échec du suivi ne casse pas l'inscription.
- Site : `signaler` muet en SSR et avec GPC ; `LienInscription` envoie son endroit ; page admin rendue avec des
  données vides et pleines.
