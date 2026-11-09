# 030 — Plan technique

Spec : [spec.md](spec.md). Aucune nouvelle dépendance : l'envoi reste en `smtplib` (bibliothèque standard), le
gabarit HTML est écrit à la main (pas de moteur de gabarits pour deux e-mails).

## Modèle de données (une migration)

### `fiche_eleve` (nouvelle, un pour un avec `eleve`)

Table à part : les données sensibles ne se mélangent pas au profil lu partout, et on sait en un coup d'œil ce qui
relève de la déclaration IPDCP.

| Colonne                                         | Type                                     | Note                                                                                          |
| ----------------------------------------------- | ---------------------------------------- | --------------------------------------------------------------------------------------------- |
| `utilisateur_id`                                | PK, FK `eleve` CASCADE                   |                                                                                               |
| `annee_scolaire`                                | `String(9)`                              | « 2026-2027 », posée par le serveur (année qui bascule au 1er septembre, heure de Lomé = UTC) |
| `numero_adhesion`                               | `String(30)` null                        |                                                                                               |
| `prefecture`, `commune`, `canton`               | `String(100)` null                       | texte libre, espaces normalisés                                                               |
| `sexe`                                          | `feminin` / `masculin` (enum texte) null |                                                                                               |
| `date_naissance`                                | `Date` null                              | 8 à 30 ans à la saisie                                                                        |
| `lieu_naissance`                                | `String(100)` null                       |                                                                                               |
| `telephone`                                     | `String(30)` null                        | contact de l'élève, normalisé                                                                 |
| `pere_nom`, `pere_profession`, `pere_telephone` | null                                     | idem pour `mere_*`                                                                            |
| `responsable_nom`, `responsable_telephone`      | null                                     | obligatoires à la validation complète                                                         |
| `reseaux`                                       | `ARRAY(String(20))`                      | `facebook`, `tiktok`, `instagram`, `autre`                                                    |
| `reseau_autre`                                  | `String(60)` null                        | si `autre`                                                                                    |
| `engagement_le`                                 | `DateTime` null                          | date de la case cochée                                                                        |
| `complete_le`                                   | `DateTime` null                          | première validation complète                                                                  |
| `cree_le` + `Suivi` (version)                   |                                          | verrou optimiste comme les autres profils                                                     |

- `fiche_eleve_axe` (`utilisateur_id`, `axe_code` FK `axe` RESTRICT), PK composite, 1 à 3 lignes.
- `fiche_eleve_parcours` (`id`, `utilisateur_id`, `rang` 1–2, `annee` `String(9)`, `etablissement` texte, `iesg`
  texte) : texte libre, un ancien établissement n'est pas forcément dans le référentiel.
- Les colonnes sont nulles (une fiche partielle pourra venir plus tard) ; aujourd'hui toute fiche est enregistrée
  complète, à l'inscription comme depuis l'espace (`complete_le`).

### `encadreur`

- `discipline String(100) null`. Le téléphone reste dans `utilisateur.telephone` : obligatoire dans le schéma
  d'inscription, pas en base (les anciens comptes n'en ont pas).

### `utilisateur` et visiteurs

- Contrainte du rôle élargie : `visiteur` ajouté à `Role` (CHECK non natif, recréée par la migration).
- `email_confirme_le DateTime null`.
- `visiteur` (nouvelle, un pour un) : `ville String(100)`, `region` enum texte (`maritime`, `plateaux`,
  `centrale`, `kara`, `savanes`, `hors_togo`) null, `sexe` null, `statut String(100)` null, `charte_version`,
  `cree_le`.
- `code_confirmation` : `utilisateur_id` PK (un seul code vivant par compte, le renvoi l'écrase), `code_hash` (Argon2, comme les mots de passe : 10⁶ possibilités, une empreinte rapide se casserait hors ligne), `expire_le`,
  `essais` (0–5), `envoye_le`. Les envois sont comptés dans `tentative_connexion` (clé `confirmation:<id>`) pour la
  limite de 5 par heure.

### Droit

- Nouveau module du catalogue `fiches_eleves` (« Fiches d'adhésion des élèves »), action `consulter`, **sensible**
  (double authentification), filtré par la DRE de l'établissement pour un collaborateur de DRE. Ajouté au
  préréglage « Administrateur national » seulement.

## API

| Route                                            | Qui                       | Effet                                                                                                                    |
| ------------------------------------------------ | ------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `POST /eleves/inscription`                       | public                    | schéma étendu d'un bloc `fiche` (obligatoire) ; tout dans la même transaction                                            |
| `GET /eleves/moi/fiche`, `PUT /eleves/moi/fiche` | l'élève                   | lire / compléter ; `version` pour le verrou ; `complete` dans la réponse                                                 |
| `GET /eleves/moi`                                | l'élève                   | + `fiche_complete: bool` pour la bannière                                                                                |
| `POST /encadreurs/inscription`                   | public                    | `telephone` requis, `discipline`                                                                                         |
| `GET/PATCH /encadreurs/moi`                      | l'encadreur               | + `discipline`, `region` (nom de la DRE), `ville` (localité)                                                             |
| `POST /visiteurs/inscription`                    | public                    | crée le compte non confirmé, envoie le code ; `code_de_test` hors production sans SMTP ; 503 en production sans SMTP     |
| `POST /visiteurs/confirmation`                   | public                    | `{email, code}` → confirme et pose la session                                                                            |
| `POST /visiteurs/confirmation/renvoi`            | public                    | `{email}` → 204 toujours (ne révèle pas si l'adresse existe)                                                             |
| `GET /visiteurs/moi`                             | le visiteur               | profil, parties récentes                                                                                                 |
| `POST /connexion`                                | public                    | un visiteur non confirmé au bon mot de passe reçoit `{etape: "confirmation", email}` et un nouveau code ; pas de session |
| `GET /admin/inscrits/{id}/fiche`                 | `fiches_eleves:consulter` | la fiche, journalisée `fiche_eleve_consultee`                                                                            |
| `GET /admin/inscrits?profil=visiteur`            | `inscrits:consulter`      | filtre existant élargi                                                                                                   |

Règles qui changent ailleurs :

- `quiz.dependances.peut_jouer` : un visiteur confirmé et actif peut jouer ; une nouvelle fonction
  `peut_certifier` (élève ou encadreur actif) protège `/certification`, et `partie.lancer` refuse un quiz du
  parcours certification à un visiteur (403). Les points de fin de partie sont déjà réservés à l'élève.
- `utilisateur_courant` refuse un compte au courriel non confirmé (cas improbable : aucune session ne s'ouvre
  avant confirmation, mais la règle tient en un endroit).
- Purge : `comptes.purge.purger_regulierement` (une fois par heure, ajoutée au `lifespan`) efface les visiteurs
  non confirmés de plus de 7 jours.
- Exports : aucun export ne lit `fiche_eleve` ; un test vérifie qu'aucun champ de la fiche n'y apparaît.

## E-mails : `app/courriel/`

- Déplacement de `app/admin/courriel.py` vers `app/courriel/envoi.py` (imports mis à jour).
- `envoyer(destinataire, sujet, texte, html)` construit un `multipart/alternative` (`set_content` +
  `add_alternative`).
- `app/courriel/gabarit.py` : `rendre(titre, paragraphes, bouton=None, code=None) -> (texte, html)`. HTML en
  tableaux et styles en ligne (compatibilité des messageries), largeur 600 px, couleurs du site (bleu du logo,
  vert du bouton), logo servi par le site (`/logo-email.png`, URL absolue de `settings.site_origine`), toutes les
  valeurs échappées par `html.escape`.
- Deux messages : invitation d'un collaborateur (existante, portée sur le gabarit) et code du visiteur.
- **Fournisseur proposé : Brevo**, offre gratuite (environ 300 e-mails par jour selon les comparatifs 2026, à
  confirmer sur sa page tarifs), relais SMTP sur le port 587 avec une clé SMTP. Il faut un domaine d'envoi
  vérifié (SPF, DKIM) pour ne pas finir en indésirables. Les variables `SMTP_*` existent déjà dans
  `.env.example` ; `deploy/README.md` reçoit la marche à suivre. L'utilisateur saisit les accès sur le VPS : rien
  dans le dépôt.

## Site

- `src/routes/inscription.tsx` : l'onglet élève devient un formulaire en étapes (Compte → Établissement → Toi →
  Parents → Club et engagement), avec une barre de progression ; les données restent dans l'état du formulaire
  jusqu'à l'envoi final (une seule requête). Composants dans `src/components/inscription/` : `FicheEleve*`,
  `ChampTelephone`, `ChoixAxes`, `ChoixReseaux`.
- Encadreur : téléphone requis, discipline, encart « Région / ville » déduit de l'établissement choisi.
- Visiteur : `InscriptionVisiteur` puis `ConfirmationCode` (6 cases, coller le code, renvoi avec compte à
  rebours) ; la page `connexion` gère l'étape `confirmation`.
- Espaces : bannière « Complète ta fiche d'adhésion » (élève) et page `/espace/fiche` ; « Ajoute ton
  téléphone » (encadreur) ; espace visiteur minimal ; le menu du visiteur montre les quiz, pas la certification.
- Admin : onglet « Fiche d'adhésion » sur `inscrits.$id` si le droit est présent ; filtre « Visiteurs ».
- Textes au tutoiement ; l'atout visiteur « Ta certification Génie Imhotep » est retiré.

## Documents

- SECURITY.md : la ligne « données limitées au nécessaire » décrit la fiche complète, ses lecteurs et la
  condition IPDCP ; le visiteur (e-mail, téléphone, ville).
- PRD : Q27 (visiteurs avancés, sans points), Q8 (le responsable remplace la signature) ; ROADMAP : R19 avancé.
- ARCHITECTURE : tableau des droits (visiteur), domaine `courriel`, tables nouvelles.

## Risques et points d'attention

- **Données sensibles de mineurs** : seul garde-fou, le droit sensible + journal. Bloquant légal : la
  déclaration IPDCP doit les lister avant toute donnée réelle (RULES : aucune donnée réelle avant le récépissé).
- **Délivrabilité** : sans SPF/DKIM, les codes arrivent en indésirables ; le message de la page le dit (« regarde
  aussi tes courriers indésirables »).
- **Énumération d'adresses** : l'inscription répond 409 pour un e-mail pris (comme les autres profils, accepté) ;
  le renvoi de code répond toujours 204.
- **Force brute du code** : 5 essais par code, 5 codes par heure → au plus 25 essais/heure sur 10⁶.
- **Formulaire long sur téléphone** : découpé en étapes ; à vérifier à 375 px.
- La migration élargit une contrainte CHECK et ajoute des tables : non destructive.
