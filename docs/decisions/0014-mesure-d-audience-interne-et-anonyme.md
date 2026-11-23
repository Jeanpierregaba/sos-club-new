# 0014 — Mesure d'audience interne et anonyme

- **Statut** : Accepté
- **Date** : 2026-11-23
- **Décidé avec** : spec 051 (suivi d'activité du super-administrateur)

## Contexte

Le porteur du projet veut suivre l'usage de la plateforme : visiteurs, provenance, clics d'inscription et abandons,
usage des Jeux, de la certification et des contenus. La plateforme accueille surtout des mineurs (`docs/SECURITY.md`),
sous la loi togolaise n° 2019-014 ; aucune donnée d'élève ne doit partir chez un tiers (ARCHITECTURE, suivi
d'erreurs). Une partie des chiffres est déjà en base (comptes, parties, certification) ; les pages vues, clics et
abandons de formulaire ne laissent aucune trace.

## Options envisagées

1. **Outil tiers** (Google Analytics, Meta Pixel) : complet et gratuit, mais envoie le comportement de mineurs à un
   tiers hors du Togo, dépose des cookies et impose un bandeau de consentement.
2. **Outil libre auto-hébergé** (Plausible, Umami, Matomo) : sans tiers, mais un service et une base de plus à tenir
   sur le VPS, des comptes à gérer en dehors de l'admin, et aucun lien avec les chiffres déjà en base.
3. **Mesure interne dans l'API** : événements anonymes envoyés à notre propre API, visiteur compté par une empreinte du
   jour (IP + navigateur + sel aléatoire du jour, détruit ensuite), sans cookie, et lecture dans la page admin à côté
   des chiffres tirés de la base.

## Décision

Option 3 : la mesure d'audience est faite par l'API elle-même, sans cookie ni service tiers, avec des événements qui
ne contiennent ni adresse IP, ni identifiant de compte, ni texte saisi, gardés 90 jours puis agrégés par jour ; la
lecture est réservée au super-administrateur.

## Conséquences

- Pas de bandeau de cookies ; `Sec-GPC` et `DNT` sont respectés ; les comptes admin et les robots ne sont pas comptés.
- Un visiteur ne peut pas être suivi d'un jour à l'autre : les visiteurs « uniques » se comptent par jour, et ceux
  d'une période sont une somme de visiteurs quotidiens. Une classe derrière une même adresse et un même navigateur
  compte pour un : le chiffre est un minimum.
- Les bloqueurs de publicités peuvent couper les événements du site ; les chiffres tirés de la base restent justes.
- Seule la rétention lie une donnée à un compte : la semaine d'activité (`presence_semaine`), effacée avec le compte
  et au bout de 26 semaines, jamais affichée par personne.
- La collecte est une route publique : schéma fermé, chemins en liste blanche, débit limité par adresse.
- À déclarer à l'IPDCP avec le reste des traitements (Q9).
