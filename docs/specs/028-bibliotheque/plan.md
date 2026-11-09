# 028 — Plan technique

## Approche

Un nouveau domaine `app/bibliotheque/`, sur le modèle de la banque de quiz (spec 027) pour la publication à deux
personnes, et des photos des articles (spec 024) pour les fichiers. La règle à deux personnes est recopiée, pas
mise en commun : deux usages ne justifient pas encore une abstraction (à reconsidérer avec R11 ou R20).

- **Fichiers** : sur le disque du VPS derrière `Stockage` (ADR-0010). Clés tirées par l'API :
  `ressources/<uuid>-document.pdf`, `ressources/<uuid>-grande.webp`, `ressources/<uuid>-vignette.webp`. Un
  fichier remplacé change de clé. Écriture avant la validation de la base, effacement aussitôt si elle échoue ;
  l'ancien fichier n'est effacé qu'après la validation qui le libère (comme `moderation/photos.py`).
- **Contrôle des PDF** (`app/fichiers/pdf.py`) : en-tête `%PDF-`, lecture par **pypdf** (6.21, maintenue, pure
  Python, vérifiée sur Context7) dans un fil à part ; refus d'un PDF chiffré, illisible, sans page, ou dont un
  objet atteignable depuis le catalogue porte `/JavaScript`, `/JS`, `/Launch`, `/EmbeddedFile(s)`,
  `/RichMedia`, `/XFA`, `/SubmitForm` ou `/ImportData`. Parcours depuis le trailer avec un ensemble de visités
  (pas de boucle), plafonné en nombre d'objets.
- **Réécriture** (après la relecture `reviewer`) : le PDF vérifié est réécrit par pypdf (`clone_from`, objets
  non référencés retirés) puis vérifié de nouveau ; c'est cette version qui est stockée. Refus ajoutés : fichier
  joint par annotation (`/EF`, `/FileAttachment`), `/GoToR`, `/GoToE`, `/Rendition`, `/Movie`, `/Sound`, et
  tout `/URI` hors `http:`, `https:` et `mailto:`.
- **Service des PDF** : en flux, par morceaux de 256 Ko (`StreamingResponse`, `Content-Length`), pour ne pas
  charger 20 Mo en mémoire par lecture sur un petit VPS. `Stockage` gagne `lire_par_morceaux(cle)`. Pas de
  `Accept-Ranges`. En-têtes : `application/pdf`, `X-Content-Type-Options: nosniff`, `Content-Disposition`
  (`inline` pour « Lire », `attachment` pour « Télécharger ») avec un nom tiré du titre, `no-store` (une
  ressource dépubliée cesse d'être servie, y compris depuis un cache).
- **Couvertures** : `images.preparer` (spec 024), deux tailles, WebP sans métadonnées.
- **Compteur** : `UPDATE ressource SET telechargements = telechargements + 1` au début de chaque lecture
  publique ; aucune ligne par personne.

## Fichiers touchés

API (`backend/`) :

- `pyproject.toml` : `pypdf`.
- `app/config.py` : `ressource_octets_max` (20 Mio), `couverture_octets_max` = `photo_octets_max`.
- `app/fichiers/stockage.py` : clés `.pdf` admises, `lire_par_morceaux`.
- `app/fichiers/pdf.py` : `verifier(octets) -> InfosPdf(pages)`, `PdfRefuse(message)`.
- `app/bibliotheque/models.py` : `Ressource`, `CategorieRessource`, `EtatRessource`.
- `app/bibliotheque/gestion.py` : créer, modifier, déposer le fichier, déposer ou retirer la couverture,
  soumettre, reprendre, approuver, refuser, dépublier, supprimer ; journal et notifications.
- `app/bibliotheque/public.py` : liste, « À la Une », chiffres, lecture du fichier et de la couverture.
- `app/bibliotheque/schemas.py`, `router.py` (public, `/bibliotheque`), `router_gestion.py`
  (`/admin/bibliotheque`).
- `app/admin/catalogue.py` : module `bibliotheque` (« Bibliothèque », consulter, créer, modifier, soumettre,
  approuver, dépublier) ; approuver et dépublier sensibles ; préréglages du gestionnaire pédagogique et du
  gestionnaire de contenus : consulter, créer, modifier, soumettre.
- `app/main.py`, `alembic/env.py` : inclusion.
- Migration `bibliotheque`.
- `app/seed_dev.py` : 4 ressources « [Test] » (dont 2 magazines publiés avec couverture), PDF d'une page générés
  par pypdf.
- Tests : `tests/test_pdf.py`, `tests/test_bibliotheque_gestion.py`, `tests/test_bibliotheque_public.py`,
  `tests/test_seed_dev.py`.

Déploiement : `deploy/proxy/Caddyfile`, `max_size` 25MB (un PDF de 20 Mo plus l'enveloppe du formulaire).

Site (`src/`) :

- `lib/api/client.ts` : types et appels (liste publique ; gestion ; envoi des fichiers en `FormData`).
- `routes/bibliotheque.tsx` : réécrite sur les données de l'API (chargée côté serveur), filtres catégorie et
  axe en paramètres d'URL, carrousel « À la Une », état vide ; les documents d'exemple disparaissent.
- `components/bibliotheque/CarteRessource.tsx`, `ALaUne.tsx`.
- `routes/_connecte/admin/bibliotheque.tsx`, `.index.tsx` (onglets par état), `.$id.tsx` (informations,
  fichier, couverture, décisions) ; entrée « Bibliothèque » du menu admin.

Docs : ADR-0010 (les PDF et la lecture en flux), `ARCHITECTURE.md`, `SECURITY.md` (contrôle des PDF),
`TASKS.md`.

## Modèle de données

`ressource` :

| Colonne                                    | Type                      | Note                                       |
| ------------------------------------------ | ------------------------- | ------------------------------------------ |
| `id`                                       | uuid                      | uuid7                                      |
| `titre`, `description`                     | text (150, 500)           |                                            |
| `categorie`                                | enum                      | magazine, guide, fiche, affiche, fascicule |
| `axe_code`                                 | FK `axe`, nullable        |                                            |
| `parution`                                 | text (60), nullable       | numéro ou date, magazine seulement         |
| `etat`                                     | enum                      | brouillon, soumis, publie, depublie        |
| `contributeurs`                            | uuid[]                    | créé, modifié, déposé, soumis              |
| `fichier_cle`, `fichier_octets`, `pages`   | text, int, int (nullable) |                                            |
| `couverture_grande`, `couverture_vignette` | text, nullable            |                                            |
| `telechargements`                          | int, défaut 0             |                                            |
| `soumis_par/le`, `publie_par/le`           | uuid, timestamptz         | `publie_le` : la dernière publication      |
| `validateur_nom`, `validateur_qualite`     | text                      | contrainte : obligatoires si `publie`      |
| `depublie_le`, `motif`                     | timestamptz, text         |                                            |
| `deja_publiee`                             | bool                      | interdit la suppression                    |
| `contenu_de_test`                          | bool                      | « Contenu de test » (seed seulement)       |
| `cree_le`, `modifie_le`                    | timestamptz               |                                            |

Index : `(etat, publie_le desc)` ; `(categorie, etat, publie_le desc)` pour « À la Une ».

## API

Public (sans connexion) :

- `GET /api/bibliotheque?categorie=&axe=` → `{ a_la_une, ressources, chiffres }` (ressources publiées).
- `GET /api/bibliotheque/{id}/fichier?telecharger=1` → le PDF, compté (404 si non publiée).
- `GET /api/bibliotheque/{id}/couverture/{taille}` → WebP (404 si non publiée).

Gestion (`exiger_permission("bibliotheque", …)`) :

- `GET /api/admin/bibliotheque?etat=` ; `POST` ; `GET|PUT|DELETE /{id}`.
- `PUT /{id}/fichier`, `PUT|DELETE /{id}/couverture` (multipart).
- `POST /{id}/soumettre | reprendre | approuver | refuser | depublier`.
- `GET /{id}/fichier`, `GET /{id}/couverture/{taille}` : relecture quel que soit l'état, non comptée.

Erreurs : 401/403 droits ; 404 introuvable ; 409 état ; 413 fichier trop lourd ; 422 données ou fichier
refusé ; 503 stockage indisponible.

## Composants

- `CarteRessource` : couverture ou visuel de catégorie (couleur et icône actuels), titre, description, taille,
  date, téléchargements, « Validé par … », boutons « Lire » et « Télécharger » (liens directs vers l'API).
- `ALaUne` : 3 magazines, défilement horizontal accessible au clavier (pas de défilement automatique).
- Admin : formulaire d'informations, dépôt du PDF et de la couverture avec message d'erreur de l'API, aperçu
  (« Ouvrir le PDF »), décisions avec la même interface que la banque de quiz.

## Dépendances

- `pypdf` 6.21.x (PyPI, licence BSD, maintenue, pure Python). Ajout par `uv add pypdf`, vérification de la
  version installée et de l'API utilisée sur Context7.

## Risques et points d'attention

- **Analyse d'un PDF piégé** (bombe de décompression, structure en boucle) : seul un collaborateur peut déposer ;
  parcours plafonné ; taille limitée à 20 Mo. Accepté pour le pilote.
- **Lecteur PDF du navigateur** : le PDF est servi depuis le domaine du site ; le refus du JavaScript, `nosniff`
  et le type exact limitent le risque. Pas de `Content-Security-Policy: sandbox`, qui empêche Chrome d'afficher
  le PDF.
- **Compteur gonflable** par rechargement : sans enjeu (aucun point), noté dans la spec.
- **Mémoire** : un dépôt de 20 Mo est lu en mémoire une fois (collaborateur seulement) ; la lecture publique est
  en flux.
