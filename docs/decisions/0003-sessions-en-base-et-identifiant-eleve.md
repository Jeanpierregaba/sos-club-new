# 0003 — Sessions en base et identifiant de l'élève

- **Statut** : Proposé (dépend de Q3 et Q4 du PRD)
- **Date** : 2026-11-02

## Contexte

Des comptes de mineurs, des enseignants et une équipe d'administration doivent se connecter, et il faut
pouvoir couper un accès immédiatement (faux compte, enseignant muté, téléphone perdu). Beaucoup d'élèves
n'ont pas d'email ; les enseignants en ont un, le cahier des charges l'exige.

## Options envisagées

- **Session en base avec cookie `HttpOnly`** (retenu) : révocation immédiate, jeton inaccessible au
  JavaScript. Une lecture en base à chaque requête, négligeable à cette échelle.
- **JWT** : pas de lecture en base, mais révocation difficile et jeton exposé s'il est gardé dans le
  navigateur.
- **Service d'authentification externe** : moins de code, mais coût à l'utilisateur, données de mineurs
  chez un tiers et transfert hors du Togo à déclarer.
- **Compte partagé pour chaque club** : proche de la lecture littérale du cahier des charges, mais un mot
  de passe partagé ne se révoque pas quand un enseignant part, et personne n'est identifiable.

## Décision

Sessions opaques en PostgreSQL, dont seule l'empreinte est stockée, et cookie `HttpOnly`, `Secure`,
`SameSite=Lax`. Mots de passe hachés avec Argon2id (`argon2-cffi`).
L'élève se connecte avec un identifiant choisi, sans email obligatoire. Les encadreurs accèdent à la
console de leur club avec leur compte personnel : il n'existe pas de compte club.

## Conséquences

- Un élève sans email récupère son accès auprès d'un encadreur de son club : l'action est journalisée.
- Les actions modifiantes vérifient l'en-tête `Origin`, en plus de `SameSite`.
- Connexion et inscription ont une limite de débit par adresse réseau et par identifiant, en tenant
  compte qu'une classe peut partager une même adresse.
- Le site et l'API partagent la même origine (ADR-0006), plutôt qu'un domaine parent comme prévu au départ.
