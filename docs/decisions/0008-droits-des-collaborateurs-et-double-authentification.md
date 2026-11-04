# 0008 — Droits des collaborateurs et double authentification

- **Statut** : Proposé
- **Date** : 2026-11-04

## Contexte

Le cahier des charges de l'espace administrateur (03/11/2026) demande :

- des comptes nominatifs pour l'équipe de gestion ;
- des droits par module et par action, et non de simples rôles ;
- un périmètre national ou limité à une DRE ;
- la double authentification pour les droits sensibles ;
- un journal que personne ne peut altérer ;
- des exports nominatifs tracés.

Jusqu'ici, un seul rôle `admin` donnait tous les droits (ADR-0003, spec 001).

## Options envisagées

- **Rôles fixes** (modérateur, analyste…) codés en dur. C'est simple, mais le CDC exige des droits
  granulaires et cumulables : chaque nouveau besoin imposerait un nouveau rôle.
- **Matrice de permissions (module, action) par collaborateur, avec des rôles qui ne sont que des
  préréglages.** Retenu : c'est fidèle au CDC, se vérifie simplement côté serveur et reste lisible dans une
  grille.
- **Service d'identité externe** (Keycloak, Auth0) : la double authentification et les rôles seraient
  fournis, mais il y aurait un service de plus à héberger, ou des données confiées à un tiers. Rejeté pour
  les mêmes raisons que l'ADR-0003.

## Décision

- **Rôle et profil.** Un collaborateur garde le rôle `admin` de `utilisateur`. Une table `collaborateur`
  porte son profil de gestion : périmètre, fin d'accès, super-administrateur ou non.
- **Droits.** Une table `permission` contient ses couples (module, action). Le super-administrateur a tous
  les droits sans ligne de permission.
- **Contrôle.** Chaque route d'administration vérifie un couple précis. Le contrôle vérifie aussi le
  compte actif, la date de fin d'accès, le périmètre et la double authentification si le collaborateur
  a un droit sensible.
- **Double authentification.** Codes TOTP (RFC 6238) générés par `pyotp`. Le secret est chiffré en base
  avec `cryptography` (Fernet), avec une clé fournie par l'environnement. L'étape refuse le rejeu d'un code
  déjà utilisé, et 10 codes de secours à usage unique sont stockés hachés.
- **Journal d'audit.** Une table en ajout seul, protégée par un déclencheur PostgreSQL qui refuse
  `UPDATE` et `DELETE`.

## Conséquences

- Les modules à venir (modération, quiz, points…) ajoutent leurs propres actions au catalogue des
  permissions, sans changer le mécanisme.
- Le périmètre DRE est stocké comme identifiant de DRE en attendant le référentiel de la spec 003. Une
  migration le reliera à la table des DRE.
- Il faut une variable `CLE_CHIFFREMENT` en production. La perdre rend inutilisables les doubles
  authentifications déjà activées : chacune devra être réinitialisée par le super-administrateur.
- Le déclencheur du journal empêche aussi les corrections par SQL ordinaire. Une purge légale future devra
  passer par une migration explicite et tracée.
- Le journal garde quelques données nominatives qu'il ne pourra pas effacer : l'e-mail d'un invité et les
  motifs saisis. Le texte des recherches d'export, lui, n'y est jamais écrit. Une durée de conservation est à
  fixer avec un juriste (question Q8 du PRD, § 16 du CDC admin) ; la purge passera alors par une migration
  tracée.

## Note du 2026-11-04 : vérification des encadreurs par DRE (spec 018)

Les données nominatives restent réservées au périmètre national, avec une exception limitée : le module
`encadreurs` (`consulter`, `approuver`). Un collaborateur de DRE y voit le nom, l'e-mail et le téléphone des
seuls encadreurs inscrits dans un établissement de sa DRE, pour vérifier leur inscription, comme la
validation des affiliations par la DRE (Q18). Le périmètre se lit sur l'établissement actuel, sous verrou, au
moment de la décision ; hors de sa DRE, la demande lui est introuvable (404). `approuver` est un droit
sensible : il exige la double authentification. L'annuaire des inscrits reste national.
