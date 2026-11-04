# SECURITY — Sécurité de l'application

La plateforme accueille surtout des mineurs : c'est le premier critère de ce document. `/audit-securite`
passe ces points en revue. Une case cochée a été vérifiée dans le code ; le reste est à mettre en place
par la spec indiquée.

## Secrets et configuration

- [ ] Aucun secret dans le code ni dans l'historique git (scan gitleaks avant la mise en ligne, spec 002).
- [ ] Aucun secret exposé au navigateur : les variables `VITE_*` ne contiennent que du public.
- [ ] Clés différentes entre développement et production.
- [x] La production refuse de démarrer avec la `DATABASE_URL` de développement.

## Authentification et accès

- [x] Le contrôle d'accès est appliqué dans l'API, jamais seulement dans l'interface (spec 001).
- [ ] Chaque requête vérifie le droit sur CETTE ressource : un encadreur n'agit que sur son club, un élève que sur ses données.
- [x] Sessions : en base, expiration (30 jours, 12 heures pour l'admin), révocation immédiate, cookie `HttpOnly` + `Secure` + `SameSite=Lax` (ADR-0003).
- [x] Mots de passe hachés avec Argon2id, 8 caractères au minimum, sans plafond trop bas.
- [ ] Les réinitialisations par un encadreur et les décisions de modération sont journalisées.
- [ ] Double authentification de l'admin à étudier avant l'ouverture.
- Sans objet : RLS et règles de sécurité côté client. Seule l'API accède à la base, qui n'est jamais exposée au navigateur.

## Entrées et sorties

- [ ] Toutes les entrées sont validées côté serveur avec Pydantic.
- [ ] Requêtes via SQLAlchemy, jamais de concaténation SQL.
- [ ] Articles et commentaires en texte simple : pas de HTML utilisateur rendu (XSS).
- [ ] Upload : type réel, taille et emplacement contrôlés, images recompressées, métadonnées et GPS retirés, PDF réservés à l'admin (ADR-0005).
- [ ] Les liens vidéo n'acceptent qu'un identifiant YouTube, jamais une URL ou un code d'intégration libre.

## Abus

- [ ] Limite de débit sur l'inscription et l'envoi d'articles, en tenant compte des classes qui partagent une adresse réseau (connexion : en place, spec 001 ; inscription, changement de mot de passe et d'email : en place, spec 017 ; articles : à faire).
- [x] CSRF : `SameSite=Lax` et contrôle de l'en-tête `Origin` sur les actions modifiantes.
- Sans objet : CORS. Le site et l'API sont sur la même origine (ADR-0006).
- [x] Les messages d'erreur ne révèlent pas d'information interne ni l'existence d'un compte.
- [ ] Quiz : réponses jamais envoyées avant la réponse de l'élève, temps et score calculés par le serveur (ADR-0004).
- [ ] Points : clé d'idempotence unique, plafonds et annulations tracées (ADR-0004).

## Dépendances

- [ ] Audit des dépendances dans la CI (`bun audit`, `pip-audit`) : en place, mais non bloquant pour le site tant que ses 13 failles élevées connues ne sont pas corrigées (`TASKS.md`).
- [x] Mises à jour de sécurité automatisées (Dependabot).
- [ ] Fichiers de lock commités (`bun.lock`, `backend/uv.lock`).

## Fonctionnalités IA

Sans objet : aucune fonctionnalité d'IA n'est prévue.

## Données personnelles et protection des mineurs

Cadre : loi togolaise n° 2019-014 du 29 octobre 2019. Cette liste est une lecture technique, pas un avis
juridique.

- [ ] Récépissé de l'IPDCP obtenu avant toute donnée réelle (art. 6), responsable du traitement désigné (Q9).
- [ ] Hébergement hors du Togo signalé à l'IPDCP avant tout transfert (art. 28).
- [ ] Consentement du représentant légal des élèves mineurs recueilli selon l'avis juridique (Q8), sa date enregistrée.
- [ ] Photos d'élèves publiées seulement avec l'attestation de l'encadreur ; retrait possible sur demande.
- [ ] Données limitées au nécessaire : ni date de naissance exacte, ni adresse, ni photo de profil, ni téléphone d'élève.
- [ ] Élèves affichés par leur pseudonyme et leur club ; liste des membres réservée au club (pseudonyme unique, alphabet latin, sans le nom complet : en place, spec 017 ; club et liste des membres : R4, R5).
- [ ] Pas de messagerie privée, pas de commentaire d'élève ; un témoignage est toujours modéré avant publication.
- [ ] Modérateurs alertés sur les témoignages révélant une situation de danger : procédure à définir avec AIMES-AFRIQUE.
- [ ] Aucune donnée de santé individuelle dans le MVP (art. 21 et 24).
- [ ] Droits d'accès, de rectification, d'opposition et d'effacement pris en charge (art. 39 et suivants).
- [ ] Durées de conservation définies et publiées avec les mentions d'information (art. 35).
- [ ] Sauvegardes chiffrées et restauration testée.
