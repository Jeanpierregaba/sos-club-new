# SESSION-LOG

<!--
Une entrée par session de travail, la plus récente EN HAUT. Rempli par /fin-de-session.
Objectif : que la session suivante reparte avec le contexte, sans deviner.
Reste bref : les décisions vont dans un ADR (docs/decisions/), on se contente d'y faire un lien.

Format :

### AAAA-MM-JJ — titre court
- Fait :
- Pièges rencontrés :
- Décisions : (liens vers les ADR)
- Prochaine étape :
-->

### 2026-11-06 — Seed préprod, retouches du site et affiliations (spec 020, R5)

- Fait : seed préprod finalisée (`seed_preprod.py`, `environnement` dans la config, relance sans doublon).
  Retouches du site demandées en urgence : tags de la galerie par axe, bouton de retour en haut, décors animés
  des heros (`DecorAnime`), éclairs derrière les mascottes des 7 axes, section caméléon, « Quel axe est fait
  pour toi ? », défi du jour en bulle flottante, Hall of Fame et Palmarès avec une section des éditions et une
  page par édition (compte à rebours jusqu'au 1er mars 2027), heros bleu et rouge, nouveau hero de la
  certification, choix « Particulier / visiteur » sur `/inscription` (sans formulaire). Spec 020 livrée
  (tâches 1–10) : tables `adhesion` et `rattachement`, adhésion du président reprise par la migration,
  confirmation par le président puis validation en lot par la DRE (points de sauvegarde, résultat par ligne),
  club supplémentaire réservé au national, liste des membres réservée au club, sortie au changement
  d'établissement, passation confirmée par un encadreur rattaché (Q19). Relecture `reviewer` : 0 bloquant ;
  corrigés : verrou de l'adhésion du successeur, encadreurs suspendus ignorés (`clubs/requetes.py`), 409 pour
  un successeur non membre, passation annulée quand le successeur part, verrou du club, lots triés par
  encadreur, « supplémentaire » recalculé à la lecture, texte de passation sans encadreur.
- Pièges rencontrés : le plugin du routeur réécrit le chemin de `createFileRoute` quand on déplace une route ;
  la convention de nommage doublait le préfixe d'une contrainte (utiliser `op.f()`) ; le port 8000 est pris
  en local (API sur 8003, `API_URL_INTERNE`).
- Décisions : spec 020 (1er club par la DRE, suivants par le national ; liste des membres selon `RULES.md` ;
  gestion dans `/mon-espace` ; confirmation Q19). Nouveaux heros toujours clairs.
- Prochaine étape : pousser sur develop (la migration crée les adhésions des présidents en préprod), puis
  `/spec` R6. Questions ouvertes : « 5 badges » sur le hero de la certification contre 4 paliers ; passer ou
  non les anciens heros sombres en clair.

### 2026-11-05 — Clubs et présidence (spec 019, R4)

- Fait : spec 019 livrée (tâches 1–18). API : tables `club`, `club_axe`, `club_passation`, demande et renvoi de
  l'élève, file admin filtrée par DRE (droits `clubs` sensibles, 2FA), activation atomique avec refus des
  doublures, passations proposées/annulées/décidées, compteurs admin, 546 tests verts. Site : bloc « Mon club »
  dans `/mon-espace` (formulaire `DemandeClub`, états en attente/refusée/actif, pas de CTA si l'établissement
  a déjà un club actif), `/admin/clubs` (À vérifier / Refusés / Passations), `/clubs/$id` (fiche publique
  minimale), carte des clubs sur `GET /api/clubs` (compteur réel, libellé « Aucun club enregistré »).
  Vérifié sur téléphone (viewport mobile) : carte, fiche, 404, espace président. Relecture `reviewer` :
  0 bloquant, 4 constats « à corriger » corrigés (CTA conservateur, échec clubs neutre, texte de passation,
  description non inventée) + `libelleAxes` employé et tests `BlocClub`.
- Pièges rencontrés : l'API tournait sans `SITE_ORIGINE` cohérent (port 8002, site 3002) ; la seed ne créait
  pas les clubs si elle avait déjà tourné sans eux — relancer `python -m app.seed_dev`. `RouterProvider` ne
  rend rien en test sans `router.load()` dans `act`.
- Décisions : notes ADR-0003 (le club n'a pas de compte) et ADR-0008 (file clubs, mêmes règles 2FA que les
  encadreurs) ; `SECURITY.md` et `ARCHITECTURE.md` à jour.
- Prochaine étape : `/spec` R5 — Affiliations des élèves et rattachements des encadreurs.

### 2026-11-04 — Compte encadreur (spec 018, R3)

- Fait : spec 018 livrée. Domaine `encadreurs` (inscription en attente, `verification.py` : file filtrable par DRE,
  activation avec +100 de bienvenue en une transaction idempotente, refus motivé, renvoi de l'encadreur,
  `encadreur_actif`) ; API et site (`/inscription?profil=encadreur`, espace encadreur, `/admin/encadreurs`
  avec 2FA et compteur), OpenAPI et types régénérés. Relecture du sous-agent `reviewer` : 3 constats importants
  corrigés (version envoyée par le site à l'activation **et** au refus, verrou `Utilisateur` à la décision,
  plus aucun contenu d'e-mail dans les journaux), 4 mineurs traités. Vérifié en format téléphone : boucle
  complet refusé → renvoi → en attente. Prérequis R4/R5.
- Pièges rencontrés : le `fastapi dev` de l'utilisateur tourne sur le port 8001 (le site de 3000 proxifie vers
  8000, qui sert une autre application) ; hors production, les e-mails ne sont plus journalisés : l'invitation
  admin renvoie le lien par `lien_de_test`.
- Décisions : sans objet (reprise). Note : `Row._tuple()` remplacé par `tuple()` (dépréciation SQLAlchemy 2.1).
- Prochaine étape : `/spec` R4 — Clubs et présidence (questions de cadrage posées, dossier
  `docs/specs/019-clubs-et-presidence/` ouvert, spec non encore écrite).

### 2026-11-04 — Compte élève et registre des points (spec 017, R2)

- Fait : spec 017 livrée. Domaine `points` (registre `mouvement_points` idempotent, semestres sans
  chevauchement garanti par la base, barème complet du PRD réglable) et domaine `eleves` (inscription en une
  transaction avec +100, pseudonyme unique en alphabet latin, établissement proposé, espace élève, mot de
  passe). Admin : onglets Points, fiche d'un élève (pseudonyme imposé, mot de passe provisoire),
  propositions d'établissement acceptées ou remplacées. Relu par le sous-agent `reviewer` : 6 constats
  importants corrigés (deux erreurs 500, limites d'essais, alerte de semestre). Correctif du déploiement :
  `CLE_CHIFFREMENT` passée au conteneur des migrations.
- Pièges rencontrés : `compose.yaml` est pris dans la version déployée, pas dans `main` ; relancer un run en
  échec ne profite donc pas d'un correctif du compose. La table `tentative_connexion` sert aussi aux limites
  d'inscription et de changement d'email : seules les lignes `en_cours = false` comptent pour la connexion.
- Décisions : inscriptions fermées par défaut en HTTPS (`INSCRIPTIONS_OUVERTES`), ADR-0004 accepté.
  Charte provisoire à faire valider (porteur du projet et juriste, avec le consentement Q8).
- Prochaine étape : ouvrir les inscriptions en préproduction (`INSCRIPTIONS_OUVERTES=true` dans son `.env`),
  créer le premier semestre depuis l'admin, puis `/spec` pour R3 (compte encadreur).

### 2026-11-04 — Référentiel (spec 016, R1)

- Fait : spec 016 livrée. Tables `dre`, `iesg`, `etablissement` et `axe`, chargées par la migration
  depuis `backend/alembic/donnees/annuaire.json` (7 DRE, 19 IESG, 838 établissements, 7 axes
  d'intervention). Le périmètre des collaborateurs devient une clé étrangère vers `dre`. Routes
  publiques `/api/referentiel/*` et admin `/api/admin/referentiel/*` (verrou de version, journal,
  désactivation sans suppression). Écrans `/admin/referentiel` ; carte des clubs, accueil et formulaire
  du Génie Imhotep lisent l'API ; `src/lib/etablissements.ts` supprimé. Relu par le sous-agent
  `reviewer`, constats 1 à 10 corrigés.
- Pièges rencontrés : deux `pytest` lancés en même temps se cassent mutuellement (la base de test est
  recréée à chaque run). Les modèles admin doivent importer ceux du référentiel pour la clé étrangère.
- Décisions : Q1 validée (les 7 axes d'intervention remplacent ceux de santé publique) ; 6 doublons
  de l'annuaire écartés ; le Hall of Fame garde les noms historiques des régions. Non traité : la page
  d'accueil peut attendre l'API jusqu'à 5 s si elle ne répond pas (constat 11, à surveiller).
- Prochaine étape : préparer le VPS de préproduction, puis `/spec` pour R2 (compte élève et registre
  des points).

### 2026-11-04 — Espace admin lot 1, comptes de démonstration et roadmap

- Fait : spec 015 livrée (collaborateurs et droits, double authentification, journal d'audit, annuaire,
  exports), relue par le sous-agent `reviewer` et corrigée. Seed `python -m app.seed_dev` (11 comptes
  `dev.*`, accès dans `.comptes-dev.local`). Refonte des pages Hall of Fame et Connexion. Quatre CDC
  reçus (admin, élève, club et président, encadreur), transcrits dans `docs/cdc/` ; PRD réécrit,
  [roadmap](ROADMAP.md) en 8 phases ; Q17 à Q20 et Q28 validées, règle du pseudonyme dans `RULES.md`.
- Pièges rencontrés : le port 8000 est pris par un autre projet, l'API locale tourne sur 8001
  (`API_URL_INTERNE`). `uv` est dans `~/.local/bin`, absent du PATH du terminal de l'utilisateur.
- Décisions : [ADR-0008](decisions/0008-droits-des-collaborateurs-et-double-authentification.md).
- Prochaine étape : préparer le VPS de préproduction, puis `/spec` pour R1 (référentiel DRE,
  établissements, axes).

### 2026-11-02 — Préparation du déploiement sur VPS

- Fait : branche `develop` créée, tout poussé sur `develop` et `main` (`f07a23e`), première CI au vert. Images Docker, pile `deploy/`, workflow `deployer.yml`.
- Pièges rencontrés : les secrets d'environnement GitHub ne sont pas disponibles sur un dépôt privé en Free, d'où des secrets au niveau du dépôt et un seul VPS.
- Décisions : [ADR-0007](decisions/0007-deploiement-vps-docker-compose.md).
- Prochaine étape : préparer le VPS en suivant `deploy/README.md`, puis vérifier le premier déploiement en preprod.

### 2026-11-02 — Spec 001 : connexion et rôles

- Fait : API (`backend/app/comptes/`), page `/connexion`, page `/mon-espace`, en-tête de l'accueil, commande de création de compte. Rien n'est commité.
- Pièges rencontrés : la relecture a trouvé un contournement des limites d'essais par requêtes simultanées et une erreur 500 sur une saisie piégée, tous deux corrigés. `router.clearCache()` ne suffit pas à vider les données d'un compte : le routeur remet la page en cache en la quittant, d'où `gcTime: 0`.
- Décisions : ADR-0006 (même origine). Blocage d'une adresse partagée accepté pour l'instant, à revoir dans la spec 002.
- Prochaine étape : réponses aux questions du PRD, puis spec 002 (hébergeur) ou 003 (clubs).

### 2026-11-02 — Cadrage à partir du cahier des charges

- Fait : PRD, architecture, design, règles, sécurité, tests, backlog et CI remplis à partir de `docs/cahier-des-charges.md`. Formatage Prettier de tout le site pour que le lint passe.
- Pièges rencontrés : le cahier des charges contredit le site sur les 7 axes et les régions (Q1, Q2). `bun audit` signale 13 failles élevées (`TASKS.md`). La CI n'avait encore jamais tourné.
- Décisions : ADR-0002 (accepté), ADR-0003 à ADR-0005 (proposés). Hypothèses Q1 à Q16 dans `docs/PRD.md`.
- Prochaine étape : obtenir les réponses aux questions du PRD, puis `/spec` sur 001 — Connexion et rôles.
