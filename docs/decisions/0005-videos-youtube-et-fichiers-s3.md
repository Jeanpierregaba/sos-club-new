# 0005 — Vidéos sur YouTube, photos et PDF en stockage S3

- **Statut** : Proposé (dépend de Q10 et Q11 du PRD)
- **Date** : 2026-11-02

## Contexte

La plateforme diffuse des capsules vidéo, des magazines PDF et les photos des activités, à des élèves
sur téléphone et réseau lent. SOS DOCTEUR TV produit déjà des vidéos et dispose d'une chaîne YouTube
d'après le pied de page du site.

## Options envisagées

- **Vidéos : lien YouTube** (retenu) : débit adapté au réseau, diffusion gratuite, aucun stockage.
  Dépend d'un service tiers, et ses recommandations doivent être limitées au maximum.
- **Vidéos : fichiers hébergés** : contrôle total, mais coûteux et lent sur réseau faible.
- **Fichiers : stockage compatible S3** (retenu) : indépendant du serveur, sauvegarde et volume simples,
  fournisseur remplaçable.
- **Fichiers : disque du serveur** : gratuit, mais à sauvegarder à part et lié à ce serveur.

## Décision

L'admin enregistre un identifiant de vidéo YouTube, lue en mode sans cookie et chargée seulement au
clic. Photos et PDF vont dans un stockage compatible S3, derrière une petite couche qui utilise le
disque en développement.

## Conséquences

- Les vidéos doivent être publiées sur une chaîne YouTube (Q11).
- L'API contrôle le type réel et la taille de chaque fichier, recompresse les images et retire leurs
  métadonnées, dont la position GPS. Les PDF sont réservés à l'admin.
- Un fournisseur hors du Togo entre dans la démarche de transfert auprès de l'IPDCP (art. 28), car les
  photos d'activités peuvent montrer des élèves.
