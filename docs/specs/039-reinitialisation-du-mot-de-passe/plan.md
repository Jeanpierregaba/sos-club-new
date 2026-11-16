# 039 — Plan technique

## Approche

Deux parcours qui réutilisent ce qui existe déjà.

**1. Réinitialisation par l'encadreur.** Elle copie la réinitialisation de l'admin (`eleves/administration.py`,
spec 017) :

- un mot de passe provisoire de 12 caractères sans caractères ambigus, haché avec Argon2id ;
- les sessions coupées ;
- le journal, sans le mot de passe ;
- le mot de passe rendu une seule fois à l'écran.

Une fonction commune, `comptes.service.reinitialiser(db, eleve, auteur, motif, ...)`, sert aux deux voies (admin et
encadreur). Elle écrit aussi le marqueur « provisoire » et la notification à l'élève. La route de l'encadreur
s'ajoute à « Mon Club Santé » (spec 033), à côté de confirmer, refuser et retirer une affiliation, et vise une
**affiliation active** du club de l'encadreur, verrouillée (`FOR UPDATE`). Hors de son club, l'affiliation
n'existe pas (404).

**Plafond de 10 par jour.** Il se compte dans le **journal d'audit**, qui garde déjà chaque réinitialisation : pas de
nouvelle table. Un verrou consultatif par encadreur (`pg_advisory_xact_lock`) fait passer les requêtes simultanées
d'un même encadreur l'une après l'autre : la 11e voit les 10 précédentes et reçoit 429.

**« Provisoire ».** Une colonne `utilisateur.mot_de_passe_provisoire_le` est posée par une réinitialisation et
effacée par tout changement de mot de passe. `Moi` expose `mot_de_passe_provisoire: bool`, et le site affiche le
bandeau qui conseille de le changer, sans rien bloquer (décision du porteur du projet).

**2. Mot de passe oublié par e-mail.** Il copie l'invitation des collaborateurs (spec 015) :

- un jeton aléatoire envoyé dans un lien ; seule son empreinte est stockée ;
- une expiration de 30 minutes ;
- un usage unique ;
- un nouveau lien annule le précédent.

La demande répond toujours la même chose. Le travail visible (recherche du compte, contrôle d'éligibilité, envoi)
se fait de la même manière dans tous les cas, et l'e-mail part en tâche de fond : le temps de réponse ne révèle pas
qu'un compte existe. La limite par adresse IP réutilise les essais de connexion (`TentativeConnexion`), et la limite
de 3 liens par heure se compte dans la table des liens.

## Fichiers touchés

### Backend

- `backend/app/comptes/models.py` :
  - colonne `Utilisateur.mot_de_passe_provisoire_le` ;
  - table `LienMotDePasse` (id, utilisateur_id FK CASCADE, jeton_hash unique, cree_le, expire_le, utilise_le,
    remplace_le).
- `backend/app/comptes/service.py` :
  - `reinitialiser(db, eleve, auteur, motif, *, par, adresse_ip)` : par l'encadreur ou l'équipe ; renvoie le
    provisoire ;
  - `changer_mot_de_passe` efface le marqueur ;
  - `demander_lien(db, email, adresse_ip)`, `lien_valide(db, jeton)` et `choisir_mot_de_passe(db, jeton, nouveau,
adresse_ip)` ;
  - `eligible_au_lien(utilisateur)` : visiteur à l'adresse confirmée ou encadreur activé ; jamais un élève, un
    collaborateur de l'admin (rôle `admin`), un compte suspendu ou supprimé.
- `backend/app/comptes/router.py` et `schemas.py` :
  - `POST /api/comptes/mot-de-passe-oublie` → 202, toujours le même message ;
  - `GET /api/comptes/mot-de-passe-oublie/{jeton}` → `{valide}` (la page de choix sait si le lien sert encore) ;
  - `POST /api/comptes/mot-de-passe-oublie/{jeton}` `{nouveau}` → 204 ;
  - `Moi.mot_de_passe_provisoire`.
- `backend/app/clubs/mon_club_sante.py` et `clubs/router.py` : `POST
/api/clubs/mon-club-sante/affiliations/{affiliation_id}/mot-de-passe` `{motif}` → `{mot_de_passe}`.
- `backend/app/clubs/schemas.py` : l'id de l'élève dans les membres confirmés si le site en a besoin (aujourd'hui
  l'affiliation suffit).
- `backend/app/eleves/administration.py` : la réinitialisation de l'admin passe par `comptes.service.reinitialiser`.
- `backend/app/courriel/messages.py` : `lien_mot_de_passe(prenom, lien, minutes)`.
- `backend/alembic/versions/<rev>_reinitialisation_du_mot_de_passe.py` : la colonne et la table ; non destructive.

### Site

- `src/lib/api/client.ts` : `reinitialiserMembre`, `demanderLienMotDePasse`, `verifierLienMotDePasse`,
  `choisirMotDePasse` ; `Moi.mot_de_passe_provisoire`.
- `src/components/clubs/MonClubSante.tsx` :
  - le bouton **Réinitialiser son mot de passe** sur chaque membre confirmé ;
  - un dialogue avec le motif, puis l'affichage du mot de passe une seule fois, avec un bouton pour le copier et la
    consigne « donne-le à l'élève en main propre ».
- `src/components/espace/BandeauMotDePasse.tsx` : le conseil de changer un mot de passe provisoire, dans l'espace de
  l'élève ; il ouvre le dialogue de changement qui existe déjà.
- `src/routes/connexion.tsx` : le lien **Mot de passe oublié ?**.
- `src/routes/mot-de-passe-oublie.tsx` :
  - un élève est renvoyé vers son encadreur ;
  - un encadreur ou un visiteur saisit son adresse ;
  - même message de confirmation dans tous les cas.
- `src/routes/mot-de-passe.nouveau.tsx` : la page de choix (jeton en paramètre), avec `Referrer-Policy: no-referrer`
  ; message clair si le lien a expiré.
- `src/lib/admin.ts` : libellés du journal.

### Documents

- `docs/SECURITY.md` (ligne 20 et une ligne pour le lien e-mail), `docs/PRD.md` (Q4 traité), `docs/DESIGN.md`
  (parcours « Mot de passe oublié »), `TASKS.md`.

## Données

```
utilisateur
  + mot_de_passe_provisoire_le  timestamptz NULL   posé par une réinitialisation, effacé à tout changement

lien_mot_de_passe
  id            uuid PK
  utilisateur_id  FK utilisateur CASCADE, index
  jeton_hash    varchar(64) unique            empreinte SHA-256, jamais le jeton
  cree_le       timestamptz default now()     sert à la limite de 3 par heure
  expire_le     timestamptz                   cree_le + 30 min
  utilise_le    timestamptz NULL
  remplace_le   timestamptz NULL              un lien plus récent l'annule
  CHECK utilise_le IS NULL OR remplace_le IS NULL
```

Les liens de plus de 7 jours sont purgés à chaque demande, comme les essais de connexion. La migration est non
destructive : une colonne nullable et une table neuve.

## API / interfaces

| Route                                                           | Qui                       | Rôle                                                                                         |
| --------------------------------------------------------------- | ------------------------- | -------------------------------------------------------------------------------------------- |
| `POST /api/clubs/mon-club-sante/affiliations/{id}/mot-de-passe` | encadreur vérifié du club | réinitialise un membre confirmé ; renvoie le provisoire une fois (`Cache-Control: no-store`) |
| `POST /api/admin/inscrits/{id}/mot-de-passe` (existant)         | `inscrits:modifier`, 2FA  | inchangé, plus le marqueur et la notification                                                |
| `POST /api/comptes/mot-de-passe-oublie`                         | tous, limité              | 202 « Si cette adresse correspond à un compte, un lien vient d'y être envoyé. »              |
| `GET /api/comptes/mot-de-passe-oublie/{jeton}`                  | tous                      | `{valide: bool}`                                                                             |
| `POST /api/comptes/mot-de-passe-oublie/{jeton}`                 | tous, limité              | change le mot de passe, coupe les sessions ; 410 si le lien n'est plus valide                |

## Dépendances

Aucune nouvelle : `secrets`, Argon2 (déjà là), l'envoi SMTP existant (spec 030).

## Sécurité

- **Droits** : l'encadreur n'agit que sur une affiliation active de **son** club, vérifiée dans l'API sur la
  ressource (ADR-0003). L'élève suspendu ou l'encadreur non vérifié sont refusés.
- **Mot de passe provisoire** : jamais au journal, dans une notification, un e-mail ou un log ; réponse en
  `no-store`. Les sessions de l'élève sont coupées.
- **Plafond** : 10 par encadreur sur 24 heures glissantes, sous verrou consultatif.
- **Lien e-mail** :
  - jeton de 32 octets (`secrets.token_urlsafe`), seule son empreinte est stockée ;
  - 30 minutes, usage unique, un nouveau lien annule le précédent ;
  - réponse identique et temps de traitement comparable pour les comptes connus et inconnus ;
  - envoi seulement aux adresses fiables ;
  - le changement coupe toutes les sessions ;
  - limites par IP et par adresse.
    La page du lien n'envoie pas de `Referer` (le jeton est dans l'adresse) et le jeton n'apparaît dans aucun log.
- **Journal** : `mot_de_passe_reinitialise` (encadreur ou admin, avec le club et le motif), `lien_mot_de_passe_envoye`
  (sans l'adresse en clair dans les détails) et `mot_de_passe_choisi`.
- `docs/SECURITY.md` : la ligne 20 devient cochable pour les réinitialisations.

## Tests

En TDD (droits, comptes) :

1. **Encadreur** :
   - le membre confirmé est réinitialisé : le provisoire marche, l'ancien mot de passe non, les sessions sont
     coupées ;
   - une affiliation en attente, d'un autre club ou retirée donne 404 ;
   - un élève suspendu, un encadreur non vérifié ou sans club en service sont refusés ;
   - un motif trop court est refusé ;
   - la 11e réinitialisation est refusée (429), aussi en parallèle ;
   - journal sans mot de passe ; notification qui nomme l'encadreur ;
   - `Moi.mot_de_passe_provisoire` est vrai, puis faux après un changement.
2. **Admin** : marqueur et notification « par l'équipe des Clubs Santé ».
3. **Lien e-mail** :
   - encadreur activé et visiteur confirmé reçoivent un e-mail ;
   - adresse inconnue, élève, collaborateur, compte suspendu, encadreur en attente ou visiteur non confirmé : rien
     d'envoyé, et la même réponse ;
   - lien expiré, déjà utilisé ou remplacé : 410 ;
   - le changement coupe les sessions et journalise ;
   - 4e demande dans l'heure : rien d'envoyé ;
   - le jeton n'est pas en base en clair ;
   - adresse en majuscules et avec des espaces.
4. **Site** :
   - dialogue de l'encadreur (motif, affichage unique, copie) ;
   - bandeau de l'élève ;
   - pages « Mot de passe oublié » et « Nouveau mot de passe » (lien valide, expiré, erreurs) ;
   - vérification dans le navigateur des pages publiques.

## Risques

- **Encadreur malveillant ou compte d'encadreur volé.** Il peut prendre la main sur 10 comptes d'élèves par jour.
  Parades :
  - le plafond ;
  - la notification à l'élève, qui voit qui a réinitialisé son compte ;
  - le journal, que l'équipe peut filtrer par action.
    Une alerte automatique à l'équipe au-delà d'un seuil relève de R22.
- **Mot de passe provisoire vu par l'encadreur.** Le changement n'est pas obligatoire (décision du porteur du
  projet) : l'encadreur connaît le mot de passe tant que l'élève ne l'a pas changé. Le bandeau le rappelle à l'élève.
  C'est un risque accepté.
- **Adresse d'un encadreur jamais confirmée par un code.** Elle a servi à l'activation par l'équipe (spec 018) ; un
  encadreur qui s'est trompé d'adresse ne recevra simplement rien. Utiliser le lien vaut confirmation de l'adresse
  (`email_confirme_le` est posé).
- **SMTP en panne.** La demande répond pareil ; la personne réessaie ou passe par l'équipe. L'échec est loggé sans
  l'adresse.
