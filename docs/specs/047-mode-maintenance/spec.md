# 047 — Mode maintenance du site

## Objectif

Permettre à un super-administrateur de mettre l’ensemble de la plateforme en maintenance (par exemple avant une mise à jour ou une intervention sur les données) et de la rouvrir, sans intervention technique sur le serveur.

## Comportement attendu

1. Un super-administrateur, depuis l’espace admin, active le mode maintenance.
2. Dès l’activation, le site public et les espaces connectés (élèves, encadreurs, visiteurs) ne sont plus accessibles : toutes les pages affichent une page de maintenance avec l’image des mascottes regroupées et le message « La plateforme est actuellement en maintenance et sera de nouveau disponible. »
3. Les appels à l’API répondent `503` avec un motif identifiable (`raison: "maintenance"`) pour les usages non autorisés, afin que le client affiche la page de maintenance.
4. Les super-administrateurs peuvent toujours se connecter et accéder à l’espace admin pour désactiver la maintenance. Les collaborateurs non super-admin sont bloqués comme les autres utilisateurs.
5. Pendant la maintenance, un bandeau visible rappelle au super-administrateur connecté que le mode maintenance est actif et lui permet de la désactiver.
6. À la désactivation, le site redevient accessible normalement. L’activation et la désactivation sont journalisées.

## Critères d’acceptation

- [ ] Étant donné un super-administrateur connecté (2FA effective), quand il active le mode maintenance, alors l’état est enregistré et l’activation est inscrite au journal d’audit.
- [ ] Étant donné le mode maintenance actif, quand un visiteur ou un utilisateur non super-admin charge une page du site, alors il voit la page de maintenance (mascottes regroupées + message « La plateforme est actuellement en maintenance et sera de nouveau disponible. »).
- [ ] Étant donné le mode maintenance actif, quand un appel API est fait sans session de super-administrateur (hors exemptions techniques), alors l’API répond `503` avec `detail` et `raison: "maintenance"`.
- [ ] Étant donné le mode maintenance actif, quand un super-administrateur se connecte (mot de passe, puis code 2FA si requis), alors la connexion aboutit et il accède à l’espace admin.
- [ ] Étant donné le mode maintenance actif et un super-administrateur connecté, quand il consulte l’admin, alors un bandeau indique que la maintenance est active et propose de la désactiver.
- [ ] Étant donné le mode maintenance actif, quand le super-administrateur le désactive, alors l’état est enregistré, la désactivation est journalisée et le site redevient accessible.
- [ ] Étant donné le mode maintenance actif, quand un collaborateur non super-admin tente d’accéder au site ou à l’admin, alors il est bloqué (page de maintenance / 503).
- [ ] Étant donné le mode maintenance actif, quand on interroge `/health`, alors l’endpoint répond normalement (le suivi de déploiement n’est pas interrompu).
- [ ] Étant donné un serveur redémarré, quand le mode maintenance était actif avant le redémarrage, alors il reste actif.

## Cas limites et erreurs

- **Déjà actif / déjà inactif** : activer alors que c’est actif (ou désactiver alors que c’est inactif) est sans effet de données mais renvoie un état cohérent (idempotent), sans erreur.
- **Non super-admin** : un collaborateur admin sans statut super-admin ne peut ni activer, ni désactiver, ni contourner la maintenance (403 sur la bascule, 503/page de maintenance sur le reste).
- **2FA non satisfaite** : un super-administrateur dont les droits sensibles exigent la 2FA ne peut pas activer/désactiver tant que la 2FA n’est pas effective (comportement habituel des actions sensibles).
- **Concurrence** : deux activations/désactivations simultanées aboutissent à un état cohérent, sans corruption.
- **Échec réseau côté client** : en cas d’échec, le client affiche un message d’erreur et ne change pas l’état affiché.
- **Photos/fichiers publics** : les ressources publiques (`/api/articles/.../photos/...`) sont bloquées comme le reste pendant la maintenance.

## Hors périmètre

- Planification automatique (activation/désactivation programmée).
- Maintenance partielle (par fonctionnalité ou par rôle autre que le contournement super-admin).
- Message personnalisé saisi à l’activation (message fixe pour cette version).
- Restriction de l’accès au serveur/déploiement (le mode maintenance est applicatif).

## Questions ouvertes

Aucune (périmètre confirmé le 2026-11-21).
