# 029 — Plan technique

## Approche

Le parcours de certification réutilise le moteur de quiz de la spec 027 sans le dupliquer : un quiz porte un
parcours (`jeux` ou `certification`), et `partie.py` branche sur ce parcours à trois endroits seulement (paramètres
utilisés, verrou d'ordre au lancement, effet d'une réussite à la fin). Tout ce qui est propre à la certification
vit dans un nouveau domaine `app/certification/` : la progression (places réussies, badges, certificat), les
règles des badges, la vérification publique, le PDF et la gestion par l'équipe.

La progression est **matérialisée** dans une table `place_reussie` plutôt que recalculée depuis les tentatives :
un quiz dépublié ou remplacé sur sa place ne fait rien perdre, l'ordre se vérifie par une requête simple, et la
base garantit qu'une place n'est comptée qu'une fois. Chaque attribution (place, badge, certificat, points)
repose sur une contrainte d'unicité de la base : deux fins de partie simultanées ne délivrent qu'une fois.

Une seule fonction, `progression.mettre_a_jour(db, joueur)`, délivre ce qui est dû (badges et certificat) à
partir des places réussies. Elle est appelée à la fin d'une partie réussie et à l'ouverture de « Ma
certification » : c'est ce rattrapage qui couvre le palier abaissé et le compte réactivé.

Le certificat PDF est généré à la demande avec **reportlab** (texte vectoriel, QR code intégré), à partir des
données figées à la délivrance : il n'est jamais stocké.

## Fichiers touchés

**API — créés**

- `backend/app/certification/models.py` : `ReglesBadges`, `PlaceReussie`, `BadgeObtenu`, `Certificat`,
  `EtatCertificat`.
- `backend/app/certification/regles.py` : règles en cours (version la plus haute, créée par défaut au besoin),
  nouvelle version.
- `backend/app/certification/progression.py` : `enregistrer_reussite`, `mettre_a_jour`, `ma_certification`,
  numéro de certificat, club bénéficiaire, crédits et notifications.
- `backend/app/certification/certificat_pdf.py` : `generer(certificat) -> bytes` (reportlab, A4 paysage, QR code).
- `backend/app/certification/verification.py` : lecture publique d'un numéro, sans nom complet.
- `backend/app/certification/gestion.py` : liste des certificats et des badges, révocation, réémission.
- `backend/app/certification/schemas.py`, `router.py` (joueur et public), `router_gestion.py` (équipe).
- Migration `xxxx_certification.py`.
- Tests : `tests/certification.py` (fabriques), `test_certification_parcours.py`,
  `test_certification_progression.py`, `test_certification_public.py`, `test_certification_gestion.py`,
  `test_certificat_pdf.py`.

**API — modifiés**

- `app/quiz/models.py` : `Quiz.parcours`, `Quiz.place`, `Quiz.ressource_id` ; constante `PARCOURS_CERTIFICATION`.
- `app/quiz/partie.py` : paramètres du parcours du quiz ; `PlaceVerrouillee` au lancement ; à la fin, pas de
  `eleve.quiz` pour la certification mais `progression.enregistrer_reussite` ; `liste` ne montre que les jeux.
- `app/quiz/banque.py`, `schemas_banque.py`, `router_banque.py` : parcours, place et fascicule à la création et
  à la modification ; place unique à l'approbation (409) ; filtre de liste par parcours ; paramètres par parcours.
- `app/quiz/router.py` : 403 « place verrouillée ».
- `app/points/service.py` : `annuler(db, mouvement, valide_par)` (première ligne négative du registre).
- `app/points/bareme.py` : `BADGE_ELEVE`, `CERTIFICATION_ELEVE`, `CERTIFICATION_ENCADREUR` en service.
- `app/main.py`, `alembic/env.py` : nouveaux routeurs et modèles.
- `app/seed_dev.py` : 12 quiz « [Test] » du parcours, publiés, reliés au fascicule de test.
- `pyproject.toml` / `uv.lock` : `reportlab`.

**Site — créés**

- `src/routes/_connecte/certification.parcours.tsx` : « Ma certification ».
- `src/routes/certificats.$numero.tsx` : vérification publique.
- `src/routes/_connecte/admin/certification.tsx` (+ `.index.tsx`, `.badges.tsx`, `.certificats.tsx`) : paramètres
  du parcours, règles des badges, certificats.
- `src/components/certification/` : `PlaceParcours`, `BadgesParcours`, `CarteCertificat` ; `src/lib/certification.ts`
  (+ test) : état d'une place, libellés, paliers.

**Site — modifiés**

- `src/lib/api/client.ts` et types générés.
- `src/routes/certification.tsx` : bouton « Commencer mon parcours » (connecté) ou « Inscris-toi » (visiteur).
- `src/routes/_connecte/quiz.$id.tsx` : retour vers « Ma certification » pour un quiz du parcours ; erreur de
  place verrouillée.
- `src/routes/_connecte/admin/quiz.$id.tsx` et `quiz.index.tsx` : parcours, place, fascicule ; filtre.
- `src/routes/_connecte/admin.tsx` : entrée « Certification ».

**Docs** : ARCHITECTURE (domaine `certification`), SECURITY (vérification publique, PDF réservé au titulaire),
PRD Q24 (paliers provisoires), TASKS.md, SESSION-LOG.

## Données

Migration non destructive (ajouts seulement).

**`quiz`** : ajouts

- `parcours` `String(20)` non nul, défaut `'jeux'` (les quiz existants restent des jeux) ; contrainte
  `parcours IN ('jeux', 'certification')`.
- `place` `Integer` nul ; contrainte : `(parcours = 'certification') = (place IS NOT NULL)` et `place BETWEEN 1 AND 12`.
- `ressource_id` FK `ressource.id` `ON DELETE RESTRICT`, nul ; seulement pour la certification.
- Index unique partiel `uq_quiz_place_publiee (place) WHERE etat = 'publie'` : la base tranche entre deux
  approbations simultanées sur une même place.

**`regles_badges`** (versionnée, jamais modifiée) : `id`, `version` unique, `noms` `JSONB` (5 textes), `paliers`
`ARRAY(Integer)` (5 valeurs), `cree_par`, `cree_le`. La version 1 (Bronze 3 … Diamant Imhotep 12) est posée par la
migration.

**`place_reussie`** : PK (`utilisateur_id`, `place`), `quiz_id`, `tentative_id`, `reussie_le`.

**`badge_obtenu`** : PK (`utilisateur_id`, `rang` 1–5), `nom` et `palier` copiés des règles, `regles_version`,
`club_id` bénéficiaire (nul), `mouvement_id` (nul pour un encadreur), `obtenu_le`.

**`certificat`** :

- `id`, `numero` unique (`GI-XXXX-XXXX-XXXX`, 60 bits aléatoires en base 32 de Crockford, sans caractère ambigu) ;
- `utilisateur_id`, `role` au moment de la délivrance ;
- `titulaire_prenom`, `titulaire_nom` figés (seul le PDF les montre) ;
- `etat` `valide | revoque | remplace`, `delivre_le` ;
- `club_id` bénéficiaire (nul), `mouvement_id` (nul si aucun point) ;
- `remplace_id` (le certificat que celui-ci remplace), `motif`, `decide_par`, `decide_le` ;
- index unique partiel `uq_certificat_origine (utilisateur_id) WHERE remplace_id IS NULL` : un seul certificat
  délivré automatiquement par personne, à jamais (un révoqué n'est pas redélivré) ;
- index unique partiel `(utilisateur_id) WHERE etat = 'valide'`.

**`parametres_quiz`** : la version 1 du parcours `certification` (15, 5 s + 2 s, 12, 10) est créée par
`parametres.en_cours` au premier besoin, comme pour les jeux.

**Barème** : la migration passe `eleve.badge`, `eleve.certification` et `encadreur.certification` en service.

## API / interfaces

**Joueur** (élève actif ou encadreur vérifié, dépendance `Joueur` de la spec 027)

- `GET /certification` → `MaCertification` : `places[12]` (place, état `verrouillee | ouverte | reussie |
bientot`, quiz id et titre, meilleur score, fascicule publié éventuel avec ses liens, tentatives restantes,
  tentative en cours), `badges[5]` (nom, palier, obtenu le), `reussies`, `certificat` (numéro, date, état),
  `nb_questions`, `seuil`. Appelle d'abord `mettre_a_jour` (rattrapage).
- Le jeu passe par les routes existantes : `POST /quiz/{id}/tentatives` refuse une place non ouverte (403,
  « Réussis d'abord la place précédente. ») ; reprise et réponses inchangées.
- `GET /certification/certificat.pdf` → PDF du certificat **valide** du compte connecté (tout compte connecté
  actif, pas seulement un joueur : un encadreur dont la vérification a changé garde son certificat). 404 sinon.
  `Content-Disposition: attachment`, `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`.

**Public**

- `GET /certificats/{numero}` → `{numero, etat, delivre_le, titulaire: {type: "eleve", pseudonyme, club} |
{type: "encadreur", prenom, initiale, fonction}, remplace_par?}` ; 404 si inconnu ou mal formé. Rien d'autre
  (ni identifiant, ni établissement, ni nom complet). `Cache-Control: no-store`.

**Équipe** (préfixe `/admin/quiz`, droits `quiz`)

- `GET /parametres?parcours=certification` et `PUT /parametres?parcours=certification` : comme les jeux
  (approuver, 2FA).
- `GET /badges` (consulter) → historique des règles ; `PUT /badges` (approuver, 2FA) → nouvelle version ;
  validation : 5 noms non vides de 40 caractères au plus, paliers entiers strictement croissants entre 1 et 12,
  dernier = 12 (422 sinon).
- `GET /certificats?etat=` (consulter) → numéro, titulaire (prénom et nom : vue interne), rôle, club, date, état.
- `GET /badges-obtenus` (consulter) → derniers badges délivrés (titulaire, badge, date), paginés.
- `POST /certificats/{id}/revoquer` (dépublier, 2FA) `{motif}` : valide → révoqué ; annule la ligne de points
  (`points.annuler`) ; audit ; notification. 409 si pas valide.
- `POST /certificats/{id}/reemettre` (dépublier, 2FA) : valide ou révoqué → l'ancien passe « remplacé », un
  nouveau certificat valide reprend `mouvement_id`, `club_id` et le nom **actuel** du compte, avec un nouveau
  numéro ; aucun point ; audit ; notification. 409 si déjà remplacé.
- Banque : `QuizEntree` gagne `parcours`, `place` (1–12, requis pour la certification), `ressource_id` (fascicule
  publié, 422 sinon) ; `GET /admin/quiz?parcours=` ; approuver sur une place occupée → 409 « La place 4 a déjà un
  quiz publié : dépublie-le d'abord. ».

**Interne**

- `progression.enregistrer_reussite(db, joueur, quiz, tentative)` : insère `place_reussie` (ON CONFLICT DO
  NOTHING), puis `mettre_a_jour`.
- `progression.mettre_a_jour(db, joueur)` : verrou du compte (`FOR NO KEY UPDATE`, même ordre que `partie`),
  compte les places réussies, délivre les badges manquants dont le palier est atteint (règles en cours), puis le
  certificat si les 12 places sont réussies et qu'aucun certificat d'origine n'existe. Crédits : `eleve.badge`
  clé `badge:<rang>:<compte>`, `eleve.certification` clé `certification:<compte>`, `encadreur.certification`
  même clé ; seulement pour un élève actif ou un encadreur vérifié. Notification par badge et pour le
  certificat (lien `/certification/parcours`).
- `points.annuler(db, mouvement, valide_par)` : ligne négative `annule_id = mouvement.id`, clé
  `annulation:<id>` ; l'unicité de `annule_id` garantit une seule annulation.

## Dépendances

- **reportlab** `>=5.1,<6` (BSD) : génération du PDF, texte vectoriel et widget QR intégré
  (`reportlab.graphics.barcode.qr`). Vérifiée sur PyPI : 5.1.0 du 2026-10-22 (plus de deux semaines), maintenue
  (4.5 → 5.1 en 2026), Python `>=3.9,<4`. Doc consultée par Context7 (`canvas.Canvas(flux, pagesize=...)`).
  Alternative écartée : dessiner une image avec Pillow et l'enregistrer en PDF (pas de nouvelle dépendance, mais
  texte non sélectionnable et fichier plus lourd). `segno`, déjà présent, reste une solution de repli pour le QR.
- Polices : Helvetica de base (encodage WinAnsi, accents français et « œ » compris) : aucun fichier de police.

## Sécurité

- **Droits** : routes joueur derrière `Joueur` (élève actif, encadreur vérifié) ; gestion derrière `quiz`
  consulter / approuver / dépublier ; approuver et dépublier exigent la 2FA (catalogue existant). Élève,
  encadreur et président : 403 sur toute route de gestion (test paramétré).
- **Données personnelles (RULES)** : le nom complet n'apparaît que dans le PDF, servi au seul titulaire, et dans
  la liste interne de l'équipe. La vérification publique ne montre que pseudonyme et club (élève), ou prénom,
  initiale et fonction (encadreur). Test : la réponse publique ne contient ni nom, ni identifiant, ni
  établissement.
- **Numéro** : 60 bits issus de `secrets` : impossible à énumérer. Mal formé → 404 sans requête en base.
- **Arbitrage (ADR-0004)** : la réussite d'une place vient uniquement d'une tentative terminée par le serveur ;
  l'ordre est vérifié au lancement, dans la transaction qui verrouille le compte.
- **Points (ADR-0004)** : tout passe par `points.crediter` et `points.annuler`, avec clés uniques.
- **Audit** : nouvelles règles, révocation, réémission, place et fascicule d'un quiz.
- **PDF** : produit par le serveur à partir de champs figés ; les textes passent par `drawString` (aucune
  interprétation) ; `no-store` ; QR vers `SITE_ORIGINE/certificats/<numero>`.

## Tests

En TDD (parties critiques de `docs/TESTING.md` : points, quiz arbitrés, droits) :

- **Ordre** : place 4 refusée sans la 3, ouverte après ; place sans quiz publié = « bientôt » et bloque la
  suivante ; remplaçant publié sur une place réussie : pas de rejeu.
- **Points** : aucune ligne `eleve.quiz` pour la certification ; badge Bronze à la 3e place, une seule ligne de
  +500 ; une seconde réussite n'ajoute rien ; encadreur : badge sans points ; certificat : une ligne de +1 000 ;
  élève sans club : pas de club bénéficiaire ; avec club : club enregistré.
- **Concurrence** : deux fins simultanées de la place 12 (deux sessions, comme les tests de course de 027/028) →
  un certificat, une ligne ; deux approbations simultanées sur une même place → une seule publiée.
- **Règles** : 422 sur paliers non croissants, dernier ≠ 12, nom vide ; une nouvelle version garde les badges
  acquis ; palier abaissé → badge délivré à l'ouverture de « Ma certification ».
- **Certificat** : PDF réservé au titulaire (autre élève et collaborateur : 404) ; contenu (pypdf extrait le
  texte : nom, numéro) ; révocation sans motif ou sans 2FA refusée ; révocation → « révoqué », PDF 404, une
  seule ligne négative ; réémission → ancien « remplacé », nouveau « valide », aucune ligne ; révoqué rejoué →
  pas de nouveau certificat.
- **Public** : forme de la réponse élève / encadreur, 404 inconnu ou mal formé.
- **Droits** : visiteur 401, élève suspendu et encadreur non vérifié 403 ; élève, encadreur, président 403 sur
  la gestion.
- **Site** : `lib/certification` (états des places, paliers), rendu de « Ma certification » et de la page de
  vérification (Vitest) ; vérification dans le navigateur de `/certificats/<numero>` à 375 px.

## Risques

- **Réémission d'un certificat révoqué** : le certificat est rétabli **sans** rendre les points retirés (la spec
  interdit tout point de plus à la réémission). Une révocation faite par erreur coûte donc les +1 000 ; accepté
  pour ce MVP, à revoir si l'équipe en a besoin.
- **Quiz modifié après publication** : sa place ne change qu'en brouillon ; les places déjà réussies restent
  attachées au numéro de place, pas au quiz. Déplacer un quiz d'une place à l'autre ne déplace pas les réussites.
- **Changement des paramètres de certification** pendant une partie : la tentative garde sa version (comme 027).
- **Pas de rattrapage hors connexion** : un joueur qui ne revient jamais ne reçoit pas un badge rendu atteignable
  par un palier abaissé. Sans conséquence : rien de public n'en dépend.
- **reportlab** est une nouvelle dépendance du serveur : bornée à `<6` ; le PDF est testé par extraction de texte.
