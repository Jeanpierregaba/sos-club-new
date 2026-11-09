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
- [ ] Chaque requête vérifie le droit sur CETTE ressource : un encadreur n'agit que sur son club, un élève que sur ses données. (Au 2026-11-04 : élève = ses seules données ; collaborateur de DRE = sa DRE, filtré en base — encadreurs et référentiel ; exports nominatifs = demandeur seul ; inscrits et journal = national. Clubs : à revalider en R4/R5. En 019 : clubs vérifiés comme les encadreurs — file filtrée par la DRE de l'établissement, hors DRE = 404, décisions = double auth exigée. En 020 : président = le club qu'il préside (403 sinon), membres = leur club, encadreur = les clubs où il est rattaché ; files d'affiliations et de rattachements filtrées par DRE, hors DRE = 404, club supplémentaire = national seul (403) ; décisions en lot élément par élément, mêmes contrôles pour chaque élément.)
- [x] Sessions : en base, expiration (30 jours, 12 heures pour l'admin), révocation immédiate, cookie `HttpOnly` + `Secure` + `SameSite=Lax` (ADR-0003).
- [x] Mots de passe hachés avec Argon2id, 8 caractères au minimum, sans plafond trop bas.
- [ ] Les réinitialisations par un encadreur et les décisions de modération sont journalisées. (Les réinitialisations de l'admin le sont, spec 017 ; celles de l'encadreur et la modération n'existent pas encore — R4, R6.)
- [x] Double authentification de l'admin à étudier avant l'ouverture. (En place, spec 015 / ADR-0008 : TOTP chiffré en base, anti-rejeu, codes de secours ; exigée pour les droits sensibles.)
- Sans objet : RLS et règles de sécurité côté client. Seule l'API accède à la base, qui n'est jamais exposée au navigateur.

## Entrées et sorties

- [x] Toutes les entrées sont validées côté serveur avec Pydantic. (Vérifié le 2026-11-04 : chaque route a ses schémas bornés ; emails, téléphone et pseudonyme validés aussi au service.)
- [x] Requêtes via SQLAlchemy, jamais de concaténation SQL. (Aucun `text()` avec une donnée d'entrée ; les seuls SQL bruts sont des constantes de migration. `hide_parameters=True`.)
- [x] Articles et commentaires en texte simple : pas de HTML utilisateur rendu (XSS). (Articles, spec 023 : Markdown restreint par `react-markdown`, sans HTML ni lien. Commentaires, spec 025 : texte brut affiché par React, sans Markdown ni lien, caractères de contrôle retirés à l'envoi ; un test du site vérifie qu'un `<img onerror>` reste du texte. Ailleurs, seuls le SVG du QR de double auth — produit par le serveur — et le CSS du graphique shadcn utilisent `dangerouslySetInnerHTML`.)
- [ ] Upload : type réel, taille et emplacement contrôlés, images recompressées, métadonnées et GPS retirés, PDF réservés à l'admin (ADR-0005). (Photos, spec 024 : image décodée et ré-encodée en WebP, 8 Mo et 24 Mpx au plus, clés tirées par l'API. PDF, spec 028 : déposés seulement par les collaborateurs qui ont le droit `bibliotheque`, 20 Mo au plus (proxy à 25 Mo), lus par pypdf et refusés s'ils sont chiffrés, illisibles, sans page, ou portent du JavaScript, une action de lancement, un fichier joint (arbre ou annotation), un lien vers un autre fichier (GoToR, GoToE), du multimédia, un formulaire XFA, une action d'envoi, ou un lien qui n'est ni http(s) ni mailto ; puis réécrits par pypdf (objets atteignables seulement, table des références neuve) et vérifiés de nouveau : c'est cette version qui est stockée et servie ; servis en flux avec leur type exact, `nosniff` et `no-store`, au public seulement une fois publiés à deux personnes avec validateur nommé. Reste : le contenu des flux (polices, images) n'est pas inspecté, et l'analyse d'un PDF piégé n'a pas de délai maximal, risque accepté tant que seule l'équipe dépose.)
- [ ] Les liens vidéo n'acceptent qu'un identifiant YouTube, jamais une URL ou un code d'intégration libre. (Aucune vidéo n'existe encore ; à revalider en R10/R20.)

## Abus

- [ ] Limite de débit sur l'inscription et l'envoi d'articles, en tenant compte des classes qui partagent une adresse réseau (connexion : en place, spec 001 ; inscription, changement de mot de passe et d'email : en place, spec 017 ; articles : à faire).
- [x] CSRF : `SameSite=Lax` et contrôle de l'en-tête `Origin` sur les actions modifiantes.
- Sans objet : CORS. Le site et l'API sont sur la même origine (ADR-0006).
- [x] Les messages d'erreur ne révèlent pas d'information interne ni l'existence d'un compte.
- [ ] Quiz : réponses jamais envoyées avant la réponse de l'élève, temps et score calculés par le serveur (ADR-0004). (À revalider en R11. En 021 : le défi du jour part sans sa bonne réponse, la correction vient d'une seconde requête ; « Quel axe » est calculé par l'API, réservé aux élèves actifs (401/403), et n'enregistre rien. En 022 : le défi du jour rapporte +20 à un élève actif, une seule réponse comptée par jour (contrainte unique), crédit idempotent `question_jour:<élève>:<jour>` ; chaque élève a sa propre question, différente de la publique, et la correction n'est donnée que pour une question reçue (404 sinon) ; « Quel axe » ne donne aucun point. En 027 : une question à la fois, envoyée sans réponse ni explication (schémas du joueur sans ces champs, testé sur toute une partie) ; délai mesuré par le serveur à partir de l'envoi (temps affiché + tolérance) ; réponse et fin verrouillent la tentative ; +50 une seule fois par élève et par quiz (clé du registre) ; banque réservée aux droits `quiz`, publication par un autre collaborateur que les contributeurs, avec double authentification et validateur médical nommé. En 029 : un quiz de certification ne se lance que si la place précédente est réussie, vérifié par l'API au lancement ; une place n'est acquise que par une tentative terminée par le serveur ; badges et certificat délivrés par insertions idempotentes (clés primaires, index uniques, clés du registre `badge:<rang>:<compte>` et `certification:<compte>`).)
- [ ] Points : clé d'idempotence unique, plafonds et annulations tracées (ADR-0004). (Clé d'idempotence et plafonds : en place, spec 017. Annulation, spec 029 : `points.annuler` écrit une ligne négative liée au gain, unique par gain (`annule_id`), utilisée par la révocation d'un certificat, qui exige le droit de dépublier un quiz, la double authentification, un motif, et entre au journal d'audit.)

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
- [ ] Photos d'élèves publiées seulement avec l'attestation de l'auteur ; retrait possible sur demande. (Spec 024 : attestation obligatoire et enregistrée pour chaque photo, contrôlée par le modérateur ; photo ré-encodée en WebP sans aucune métadonnée, dont la position GPS ; lue seulement par l'auteur, les modérateurs de son périmètre et, après approbation, le public ; fichiers effacés 90 jours après un refus. Retrait : le modérateur dépublie ou demande une correction. Reste à valider par un juriste, Q8.)
- [ ] Fiche d'adhésion de l'élève (spec 030, décision du porteur du projet le 2026-11-09) : la fiche papier est reprise en entier — date et lieu de naissance, contact de l'élève, père et mère (nom, profession, contact), parent ou tuteur responsable, préfecture, commune, canton, axes, années antérieures, réseaux sociaux. Elle sert notamment au soutien des membres actifs pour les bourses. **À déclarer à l'IPDCP et à faire valider par un juriste avant toute donnée réelle (Q8, Q9).** Table à part (`fiche_eleve`) ; lue par l'élève lui-même et par les collaborateurs ayant le droit sensible `fiches_eleves:consulter` (double authentification, périmètre DRE), chaque lecture journalisée sans le contenu ; jamais par un encadreur ni en public, dans aucun export.
- [x] Données limitées au nécessaire hors de la fiche d'adhésion : ni adresse, ni photo de profil ; aucun téléphone d'élève sur le compte (seulement dans la fiche). Visiteur (spec 030) : nom, prénoms, e-mail confirmé par un code (6 chiffres, empreinte Argon2, 15 minutes, 5 essais, 5 envois par heure), téléphone et ville obligatoires, région, sexe et statut facultatifs ; lus par lui-même et par les collaborateurs `inscrits` du niveau national ; compte jamais confirmé effacé au bout de 7 jours ; ni code ni adresse dans les journaux. Encadreur (spec 018, puis 030) : e-mail et téléphone obligatoires, pour la vérification ; lus par lui-même et par les collaborateurs habilités de sa DRE ou du niveau national, jamais publics. Articles (spec 023) : la file de modération montre le nom complet, l'identifiant et l'établissement de l'auteur aux collaborateurs habilités (national, ou DRE de l'établissement ; consultation sous double authentification) ; en public, un élève signe par son pseudonyme (et son club s'il le choisit), un encadreur par son prénom, l'initiale de son nom et sa fonction ; le journal ne garde jamais le texte d'un article. Notifications : sur le site seulement, lues par leur seul destinataire. Club (spec 019) : nom officiel + description courte + axes + encadreurs associés déclaratifs (nom + e-mail/téléphone facultatifs) sur une demande ; une fiche publique minimale (nom, établissement IESG/DRE, axes, date d'activation) sans aucun e-mail, téléphone ou nom d'élève. (Inscrits et journaux : national ; exports : national + droit + double auth ; listes publiques : référentiel uniquement.)
- [x] Élèves affichés par leur pseudonyme et leur club ; liste des membres réservée au club (pseudonyme unique, alphabet latin, sans le nom complet : en place, spec 017. En 019 : clubs actifs et fiches publiques sans données nominatives. En 020 : la liste des membres — pseudonymes et date d'adhésion seulement — n'est visible que du président, des membres actifs, des encadreurs rattachés et des collaborateurs de la DRE ; pour tout autre, 404. Le président voit la classe d'un demandeur pour décider, jamais son nom.)
- [ ] Pas de messagerie privée, pas de commentaire d'élève ; un témoignage est toujours modéré avant publication. (Spec 023 : les articles passent tous par la file de modération ; rien n'est lisible avant l'approbation, une révision reste masquée jusqu'à la sienne, et le texte est rendu sans HTML ni lien. Commentaires, spec 025 : élèves et encadreurs actifs seulement, en attente jusqu'à l'approbation, signés comme les articles, 20 envois par jour au plus, retirables par leur auteur. Espace du président, spec 026 : fiche et actualités du club proposées par le seul président en place et validées avant publication ; une actualité est signée du nom du club, jamais de l'élève ; « Mon club » n'est lisible que du président, des membres actifs et des encadreurs rattachés (404 pour les autres). Messagerie et témoignages : n'existent pas encore, à revalider en R18.)
- [ ] Modérateurs alertés sur les témoignages révélant une situation de danger : procédure à définir avec AIMES-AFRIQUE.
- [x] Aucune donnée de santé individuelle dans le MVP (art. 21 et 24). (Aucun champ de santé, nulle part — vérifié le 2026-11-04.)
- [ ] Droits d'accès, de rectification, d'opposition et d'effacement pris en charge (art. 39 et suivants). (Accès et rectification : en place, spec 017 ; opposition et effacement : pas encore.)
- [ ] Durées de conservation définies et publiées avec les mentions d'information (art. 35).
- [ ] Sauvegardes chiffrées et restauration testée. (Le volume des photos est archivé avec la base depuis la spec 024. Non : dump en clair, sur le VPS seulement, restauration jamais testée — voir `deploy/sauvegarder.sh` ; à corriger avant toute donnée réelle.)
