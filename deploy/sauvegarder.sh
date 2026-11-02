#!/usr/bin/env bash
# Sauvegarde la base de l'environnement dans ./sauvegardes et garde 14 jours d'historique.
# Attention : ces fichiers restent sur le VPS. Il faut encore les copier ailleurs (voir deploy/README.md).
#
# Usage : sauvegarder.sh [étiquette]
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"
etiquette="${1:-quotidienne}"
[[ "$etiquette" =~ ^[a-zA-Z0-9_-]+$ ]] || { echo "Étiquette invalide : $etiquette" >&2; exit 2; }

umask 077
mkdir -p sauvegardes
fichier="sauvegardes/$(date -u +%Y%m%dT%H%M%SZ)-$etiquette.dump"

# Écrit d'abord à côté : une sauvegarde interrompue ne doit pas passer pour une sauvegarde valide.
docker compose exec -T db pg_dump --username sosclub --format custom sosclub > "$fichier.partiel"
# Un fichier illisible ne doit pas passer pour une sauvegarde.
docker compose exec -T db pg_restore --list < "$fichier.partiel" > /dev/null
mv "$fichier.partiel" "$fichier"

find sauvegardes -name '*.dump' -mtime +14 -delete
find sauvegardes -name '*.partiel' -mtime +1 -delete
echo "Sauvegarde : $PWD/$fichier"
