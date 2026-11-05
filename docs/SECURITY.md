# SECURITY — Sécurité de l'application

La plateforme accueille surtout des mineurs : c'est le premier critère de ce document. `/audit-securite`
passe ces points en revue. Une case cochée a été vérifiée dans le code ; le reste est à mettre en place
par la spec indiquée.

## Secrets et configuration

- [ ] Aucun secret dans le code ni dans l'historique git (scan gitleaks avant la mise en ligne, spec 002 ; scan manuel du 2026-11-04 : aucun trouvé).
- [x] Aucun secret exposé au navigateur : les variables `VITE_*` ne contiennent que du public. (Aucune variable `VITE_*` n'existe ; seul `API_URL_INTERNE`, côté serveur.)
- [x] Clés différentes entre développement et production. (Production : `CLE_CHIFFREMENT` exigée, refus de la `DATABASE_URL` de dev ; en dev : clé locale ignorée par git.)
- [x] La production refuse de démarrer avec la `DATABASE_URL` de développement.

## Authentification et accès

- [x] Le contrôle d'accès est appliqué dans l'API, jamais seulement dans l'interface (spec 001).
- [ ] Chaque requête vérifie le droit sur CETTE ressource : un encadreur n'agit que sur son club, un élève que sur ses données. (Au 2026-11-04 : élève = ses seules données ; collaborateur de DRE = sa DRE, filtré en base — encadreurs et référentiel ; exports nominatifs = demandeur seul ; inscrits et journal = national. Clubs : à revalider en R4/R5. En 019 : clubs vérifiés comme les encadreurs — file filtrée par la DRE de l'établissement, hors DRE = 404, décisions = double auth exigée.)
- [x] Sessions : en base, expiration (30 jours, 12 heures pour l'admin), révocation immédiate, cookie `HttpOnly` + `Secure` + `SameSite=Lax` (ADR-0003).
- [x] Mots de passe hachés avec Argon2id, 8 caractères au minimum, sans plafond trop bas.
- [ ] Les réinitialisations par un encadreur et les décisions de modération sont journalisées. (Les réinitialisations de l'admin le sont, spec 017 ; celles de l'encadreur et la modération n'existent pas encore — R4, R6.)
- [x] Double authentification de l'admin à étudier avant l'ouverture. (En place, spec 015 / ADR-0008 : TOTP chiffré en base, anti-rejeu, codes de secours ; exigée pour les droits sensibles.)
- Sans objet : RLS et règles de sécurité côté client. Seule l'API accède à la base, qui n'est jamais exposée au navigateur.

## Entrées et sorties

- [x] Toutes les entrées sont validées côté serveur avec Pydantic. (Vérifié le 2026-11-04 : chaque route a ses schémas bornés ; emails, téléphone et pseudonyme validés aussi au service.)
- [x] Requêtes via SQLAlchemy, jamais de concaténation SQL. (Aucun `text()` avec une donnée d'entrée ; les seuls SQL bruts sont des constantes de migration. `hide_parameters=True`.)
- [ ] Articles et commentaires en texte simple : pas de HTML utilisateur rendu (XSS). (Aucune publication n'existe encore ; à revalider en R6/R7. Aujourd'hui, seuls le SVG du QR de double auth — produit par le serveur — et le CSS du graphique shadcn utilisent `dangerouslySetInnerHTML`.)
- [ ] Upload : type réel, taille et emplacement contrôlés, images recompressées, métadonnées et GPS retirés, PDF réservés à l'admin (ADR-0005). (Aucun upload n'existe encore.)
- [ ] Les liens vidéo n'acceptent qu'un identifiant YouTube, jamais une URL ou un code d'intégration libre. (Aucune vidéo n'existe encore ; à revalider en R10/R20.)

## Abus

- [ ] Limite de débit sur l'inscription et l'envoi d'articles, en tenant compte des classes qui partagent une adresse réseau (connexion : en place, spec 001 ; inscription, changement de mot de passe et d'email : en place, spec 017 ; articles : à faire).
- [x] CSRF : `SameSite=Lax` et contrôle de l'en-tête `Origin` sur les actions modifiantes.
- Sans objet : CORS. Le site et l'API sont sur la même origine (ADR-0006).
- [x] Les messages d'erreur ne révèlent pas d'information interne ni l'existence d'un compte.
- [ ] Quiz : réponses jamais envoyées avant la réponse de l'élève, temps et score calculés par le serveur (ADR-0004). (Aucun quiz n'existe encore ; à revalider en R9/R11.)
- [ ] Points : clé d'idempotence unique, plafonds et annulations tracées (ADR-0004). (Clé d'idempotence et plafonds : en place, spec 017 ; aucune action d'annulation n'est encore exposée.)

## Dépendances

- [ ] Audit des dépendances dans la CI (`bun audit`, `pip-audit`) : en place, mais non bloquant pour le site tant que ses 13 failles élevées connues ne sont pas corrigées (`TASKS.md` ; le 2026-11-04, `bun audit --audit-level=high` confirme les 13, `pip-audit` est propre).
- [x] Mises à jour de sécurité automatisées (Dependabot).
- [x] Fichiers de lock commités (`bun.lock`, `backend/uv.lock`).

## Fonctionnalités IA

Sans objet : aucune fonctionnalité d'IA n'est prévue.

## Données personnelles et protection des mineurs

Cadre : loi togolaise n° 2019-014 du 29 octobre 2019. Cette liste est une lecture technique, pas un avis
juridique.

- [ ] Récépissé de l'IPDCP obtenu avant toute donnée réelle (art. 6), responsable du traitement désigné (Q9).
- [ ] Hébergement hors du Togo signalé à l'IPDCP avant tout transfert (art. 28).
- [ ] Consentement du représentant légal des élèves mineurs recueilli selon l'avis juridique (Q8), sa date enregistrée.
- [ ] Photos d'élèves publiées seulement avec l'attestation de l'encadreur ; retrait possible sur demande.
- [x] Données limitées au nécessaire : ni date de naissance exacte, ni adresse, ni photo de profil, ni téléphone d'élève. Encadreur (spec 018) : e-mail obligatoire et téléphone facultatif, pour la vérification ; lus par lui-même et par les collaborateurs habilités de sa DRE ou du niveau national, jamais publics. Club (spec 019) : nom officiel + description courte + axes + encadreurs associés déclaratifs (nom + e-mail/téléphone facultatifs) sur une demande ; une fiche publique minimale (nom, établissement IESG/DRE, axes, date d'activation) sans aucun e-mail, téléphone ou nom d'élève. (Inscrits et journaux : national ; exports : national + droit + double auth ; listes publiques : référentiel uniquement.)
- [ ] Élèves affichés par leur pseudonyme et leur club ; liste des membres réservée au club (pseudonyme unique, alphabet latin, sans le nom complet : en place, spec 017 ; club et liste des membres : R4, R5. En 019 : clubs actifs et fiches publiques sans données nominatives ; la liste des membres reste à faire en R5.)
- [ ] Pas de messagerie privée, pas de commentaire d'élève ; un témoignage est toujours modéré avant publication. (Aucune de ces fonctionnalités n'existe encore ; à revalider en R6/R7/R18.)
- [ ] Modérateurs alertés sur les témoignages révélant une situation de danger : procédure à définir avec AIMES-AFRIQUE.
- [x] Aucune donnée de santé individuelle dans le MVP (art. 21 et 24). (Aucun champ de santé, nulle part — vérifié le 2026-11-04.)
- [ ] Droits d'accès, de rectification, d'opposition et d'effacement pris en charge (art. 39 et suivants). (Accès et rectification : en place, spec 017 ; opposition et effacement : pas encore.)
- [ ] Durées de conservation définies et publiées avec les mentions d'information (art. 35).
- [ ] Sauvegardes chiffrées et restauration testée. (Non : dump en clair, sur le VPS seulement, restauration jamais testée — voir `deploy/sauvegarder.sh` ; à corriger avant toute donnée réelle.)
