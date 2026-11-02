# 001 — Connexion et rôles

## Objectif

Permettre à un utilisateur de se connecter et de se déconnecter, et garantir que chaque rôle (élève,
encadreur, admin) n'accède qu'à ce qui le concerne. C'est la première brique du PRD et le premier lien
réel entre le site et l'API. Elle s'appuie sur les hypothèses Q3 (pas de compte club partagé) et Q4
(élève avec identifiant, sans email obligatoire).

Personne ne peut encore s'inscrire depuis le site : l'enregistrement des clubs et des élèves arrive avec
les specs 003 et 004. Les comptes sont créés en ligne de commande, par l'équipe technique.

## Comportement attendu

**Se connecter**

1. Depuis l'accueil, je clique sur « Se connecter » et j'arrive sur la page `/connexion`.
2. Je saisis mon identifiant, ou mon email si j'en ai un, et mon mot de passe. Je peux afficher le mot de
   passe pendant la saisie.
3. Si c'est correct, j'arrive sur « Mon espace », ou sur la page que je voulais ouvrir au départ.
4. Je reste connecté pendant 30 jours sur cet appareil (12 heures pour un admin), puis je dois me reconnecter.

**Mon espace** (`/mon-espace`)

- La page me salue par mon prénom, affiche mon rôle et un bouton « Me déconnecter ».
- Un admin y voit aussi le nombre de comptes par rôle. Les autres rôles ne le voient pas.
- Cette page provisoire sera remplacée par le Passeport (005), la console du club (006) et la console
  admin (015).

**En-tête de l'accueil**

- Visiteur : « Se connecter » et « Rejoindre le club », comme aujourd'hui.
- Connecté : « Mon espace » remplace « Se connecter ».

**Se déconnecter** : je clique sur « Me déconnecter » et je reviens à l'accueil. Revenir en arrière dans
le navigateur ne rouvre pas la page protégée.

**Créer un compte** : l'équipe technique lance une commande, indique le rôle et les informations du
compte, puis saisit le mot de passe sans qu'il apparaisse à l'écran. C'est ainsi qu'est créé le premier
admin.

## Critères d'acceptation

**Connexion**

- [x] Étant donné un compte actif, quand je saisis son identifiant et le bon mot de passe, alors je suis connecté et j'arrive sur « Mon espace ».
- [x] Étant donné un compte avec un email, quand je saisis cet email et le bon mot de passe, alors je suis connecté.
- [x] Étant donné ` JeanK` ou `jeank`, quand je me connecte au compte `jeank`, alors les majuscules et les espaces autour ne changent rien.
- [x] Quand le mot de passe est faux ou le compte inconnu, alors j'obtiens le même message, « Identifiant ou mot de passe incorrect », sans indice sur l'existence du compte.
- [x] Étant donné un compte suspendu, quand je saisis le bon mot de passe, alors la connexion est refusée avec un message qui m'invite à contacter un encadreur ou l'équipe nationale.
- [x] Étant donné 5 échecs en 15 minutes sur un même identifiant, existant ou non, quand je réessaie, alors je suis bloqué avec « Trop d'essais. Réessaie dans 15 minutes. », même avec le bon mot de passe.
- [x] Étant donné 50 échecs en 15 minutes depuis une même adresse réseau, quand je réessaie, alors je suis bloqué. Une classe de 40 élèves qui se connectent correctement n'est jamais bloquée.

**Session**

- [x] Quand je me connecte, le cookie de session est `HttpOnly`, `SameSite=Lax`, et `Secure` dès que le site est en HTTPS.
- [x] La base ne contient que l'empreinte du jeton de session, jamais le jeton, et que l'empreinte du mot de passe (Argon2id), jamais le mot de passe.
- [x] Étant donné un élève ou un encadreur, sa session expire après 30 jours. Étant donné un admin, après 12 heures.
- [x] Étant donné une session expirée, une session supprimée ou un compte suspendu, quand j'appelle l'API, alors j'obtiens une erreur 401, immédiatement.
- [x] Quand je me déconnecte, la session est supprimée en base : réutiliser l'ancien cookie donne une erreur 401.
- [x] Une connexion sur un deuxième appareil ne déconnecte pas le premier.

**Rôles et pages protégées**

- [x] Étant donné un visiteur, quand il ouvre `/mon-espace`, alors il arrive sur `/connexion`, puis revient sur `/mon-espace` après s'être connecté.
- [x] Étant donné un utilisateur connecté, quand il ouvre `/connexion`, alors il arrive sur « Mon espace ».
- [x] Étant donné un élève ou un encadreur, quand il appelle la route des chiffres admin, alors il obtient une erreur 403. Un visiteur obtient une erreur 401, un admin obtient les chiffres.
- [x] Une redirection après connexion ne peut viser qu'une page du site : `/connexion?redirection=https://autre-site.tg` mène à « Mon espace ».
- [x] Une requête qui modifie des données et vient d'une autre origine que le site est refusée (erreur 403).

**Création de compte**

- [x] Quand la commande crée un admin, alors celui-ci peut se connecter. Le mot de passe n'apparaît ni dans la commande, ni à l'écran, ni dans les logs.
- [x] Quand je tente de créer un compte avec un identifiant ou un email déjà pris, un mot de passe de moins de 8 caractères, un admin ou un encadreur sans email, alors la commande refuse avec un message clair et ne crée rien.

**Site**

- [x] Les pages publiques s'affichent aussi quand l'API est arrêtée ; l'en-tête propose alors « Se connecter ».
- [x] La page `/connexion` est utilisable à 320 px de large et au clavier seul, au tutoiement, sans texte en anglais. Le site déclare `lang="fr"`, et les pages 404 et d'erreur sont en français.

## Cas limites et erreurs

| Cas                                                                  | Comportement                                                                                          |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Champ vide                                                           | Message sous le champ, aucun appel à l'API                                                            |
| Mot de passe de plus de 256 caractères                               | Refusé sans le hacher, pour éviter une surcharge volontaire du serveur                                |
| Caractères spéciaux ou accents dans le mot de passe                  | Acceptés et conservés tels quels                                                                      |
| Identifiant contenant `@`                                            | Traité comme un email. La création de compte interdit `@` dans un identifiant                         |
| Double clic sur « Me connecter »                                     | Bouton désactivé pendant l'envoi                                                                      |
| Réseau coupé ou API arrêtée à la connexion                           | « Connexion impossible pour le moment. Réessaie dans quelques instants. », le formulaire reste rempli |
| API arrêtée à l'ouverture de `/mon-espace`                           | Message d'indisponibilité avec « Réessayer », et non un renvoi vers la connexion                      |
| Session expirée pendant la navigation                                | Renvoi vers `/connexion`, avec retour à la page demandée                                              |
| Déconnexion sans session valide                                      | Sans erreur : je reviens à l'accueil                                                                  |
| Se connecter alors qu'une session est déjà ouverte sur ce navigateur | L'ancienne session est supprimée, une nouvelle est créée                                              |
| Erreur de validation de l'API                                        | Message en français, sans renvoyer le mot de passe reçu                                               |

## Hors périmètre

- Inscription depuis le site (003, 004) et réinitialisation du mot de passe par un encadreur (004).
- Réinitialisation par email et envoi d'emails (003).
- Changement de mot de passe par l'utilisateur, à ajouter à la spec 004.
- Suspension d'un compte depuis une interface : le statut existe, mais seule l'équipe technique le change pour l'instant.
- Double authentification de l'admin, à étudier avant l'ouverture (`docs/SECURITY.md`).
- Sessions prolongées à l'usage, liste des appareils connectés.
- Mise en ligne (002) : elle reprendra la configuration d'une même origine décrite dans le plan.

## Questions ouvertes

Aucune ne bloque le plan. Q3 et Q4 du PRD restent à confirmer : si Q4 change, seul le mode d'identification
des élèves sera à reprendre.
