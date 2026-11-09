# 0010 — Fichiers sur le disque du VPS, servis par l'API

- **Statut** : Proposé (précise l'ADR-0005 pour les fichiers)
- **Date** : 2026-11-07

## Contexte

L'ADR-0005 prévoyait un stockage compatible S3 pour les photos et les PDF, derrière une petite couche qui utilise
le disque en développement. Les premières photos sont celles des articles (spec 024) : elles peuvent montrer des
élèves mineurs, et un fournisseur hors du Togo impose une démarche de transfert auprès de l'IPDCP (art. 28). Le
volume attendu au pilote reste faible (quelques milliers de photos de 200 à 400 Ko).

## Options envisagées

- **Fournisseur S3 dès maintenant** : indépendant du VPS, sauvegarde gérée ; mais un fournisseur à choisir, un
  coût, et un transfert de photos d'élèves à déclarer avant toute donnée réelle.
- **Disque du VPS, dans un volume Docker** (retenu) : gratuit, aucun transfert, même serveur que la base ; mais à
  inclure dans la sauvegarde, et lié à ce serveur.
- **Dans la base PostgreSQL** (comme les fichiers d'export, temporaires) : sauvegardé avec la base, mais une base
  qui grossit vite et des lectures plus lourdes pour des fichiers permanents.

## Décision

Les fichiers vont sur le disque du VPS, dans un volume Docker, derrière une interface unique `Stockage`
(`enregistrer`, `lire`, `supprimer`) ; l'API les sert elle-même après avoir vérifié le droit de lecture.

## Conséquences

- Un seul fichier (`app/fichiers/stockage.py`) connaît le disque : passer à S3 revient à écrire une seconde
  implémentation de `Stockage`, sans toucher aux domaines.
- Le conteneur de l'API reste en lecture seule ; seul le volume des fichiers est inscriptible.
- `deploy/sauvegarder.sh` archive le volume des fichiers en plus de la base. La copie hors du VPS reste à faire
  (déjà notée dans `deploy/README.md` et `docs/SECURITY.md`).
- L'API sert les images : une photo privée n'a jamais d'adresse publique, et la vérification du droit se fait à
  chaque lecture. Les photos publiques portent un en-tête de cache long, car leur adresse change avec leur
  contenu.
- Les clés de fichier sont des UUID tirés par l'API : aucun nom choisi par l'utilisateur n'arrive sur le disque.

## Mise en œuvre (spec 028)

- Les PDF de la bibliothèque suivent le même chemin (`ressources/<uuid>-document.pdf`) ; `Stockage` gagne
  `lire_par_morceaux`, et l'API sert un PDF en flux par morceaux de 256 Ko, avec sa taille, sans jamais le
  charger en entier. Un passage à S3 devra fournir la même lecture en flux.
- Contrairement aux photos publiques, les fichiers de la bibliothèque ne se gardent dans aucun cache
  (`no-store`) : une ressource dépubliée cesse aussitôt d'être servie.
- La limite du proxy passe à 25 Mo, pour un PDF de 20 Mo et l'enveloppe du formulaire.
