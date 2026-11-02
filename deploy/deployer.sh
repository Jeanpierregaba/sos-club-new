#!/usr/bin/env bash
# Déploie une version sur le VPS : sauvegarde, migrations, puis nouveaux conteneurs, avec retour à la version
# précédente si ceux-ci ne démarrent pas. Lancé par la CI, depuis le dossier de l'environnement.
#
# Usage : deployer.sh <preprod|prod> <version> [--retour-arriere]
# --retour-arriere ne lance pas les migrations : une ancienne image ne connaît pas les migrations plus récentes.
# Le jeton de lecture des images arrive sur l'entrée standard, jamais en argument, pour ne pas apparaître dans ps.
# À la main sur le VPS, sans jeton : deployer.sh prod <version> < /dev/null
set -euo pipefail

environnement="${1:-}"
version="${2:-}"
mode="${3:-}"
[[ "$environnement" =~ ^(preprod|prod)$ ]] || { echo "Environnement invalide : $environnement" >&2; exit 2; }
[[ "$version" =~ ^[0-9a-f]{7,40}$ ]] || { echo "Version invalide : $version" >&2; exit 2; }
[[ -z "$mode" || "$mode" == "--retour-arriere" ]] || { echo "Option inconnue : $mode" >&2; exit 2; }

cd "$(dirname "$(readlink -f "$0")")"

# Compose refuse de continuer s'il manque une variable obligatoire. Le nom évite de déployer sur le mauvais environnement.
configuration="$(docker compose config)"
grep -qx "name: sosclub-$environnement" <<<"$configuration" \
  || { echo "La configuration de $PWD ne correspond pas à $environnement : voir deploy/README.md" >&2; exit 2; }
# En http://, le cookie de session perdrait l'attribut Secure sans que rien ne le signale.
grep -qE '^ +SITE_ORIGINE: https://' <<<"$configuration" \
  || { echo "SITE_ORIGINE doit commencer par https://" >&2; exit 2; }

# Une configuration Docker jetable : le jeton ne reste pas sur le serveur après le déploiement.
DOCKER_CONFIG="$(mktemp -d)"
export DOCKER_CONFIG
trap 'rm -rf "$DOCKER_CONFIG"' EXIT
# Docker cherche aussi ses extensions, dont compose, dans ce dossier.
[[ -d "$HOME/.docker/cli-plugins" ]] && ln -s "$HOME/.docker/cli-plugins" "$DOCKER_CONFIG/cli-plugins"
jeton="$(cat)"
if [[ -n "$jeton" ]]; then
  printf '%s' "$jeton" | docker login ghcr.io --username "${REGISTRE_UTILISATEUR:-github-actions}" --password-stdin >/dev/null
fi

precedente="$(cat .version 2>/dev/null || true)"

echo "==> Récupération de la version $version"
IMAGE_TAG="$version" docker compose --profile migrations pull api site migrations

# Avant tout redémarrage de la base : si son image change, la sauvegarde porte encore sur les vraies données.
if [[ -n "$(docker compose ps --status running --quiet db)" ]]; then
  echo "==> Sauvegarde"
  ./sauvegarder.sh "depuis-${precedente:-inconnue}"
fi

echo "==> Base de données"
IMAGE_TAG="$version" docker compose up --detach --wait db

if [[ "$mode" == "--retour-arriere" ]]; then
  echo "==> Retour arrière : migrations ignorées"
else
  echo "==> Migrations"
  IMAGE_TAG="$version" docker compose --profile migrations run --rm -T migrations
fi

echo "==> Démarrage"
if ! IMAGE_TAG="$version" docker compose up --detach --wait --wait-timeout 180 api site; then
  # Les journaux restent sur le VPS : ils contiennent les adresses des visiteurs.
  docker compose logs --tail 200 api site > "echec-$version.log" 2>&1 || true
  docker compose ps >&2 || true
  echo "Journaux : $PWD/echec-$version.log" >&2
  if [[ -n "$precedente" ]]; then
    echo "==> Échec : retour à la version $precedente. Les migrations ne sont pas annulées." >&2
    IMAGE_TAG="$precedente" docker compose up --detach --wait --wait-timeout 180 api site
  fi
  exit 1
fi

echo "$version" > .version

# Une fois publiée, la version doit répondre derrière le proxy. Sans DNS ou proxy prêts, on prévient sans annuler :
# les conteneurs, eux, sont sains. La preprod répond 401 tant que le mot de passe n'est pas fourni.
origine="$(docker compose exec -T api printenv SITE_ORIGINE || true)"
code="$(curl --silent --output /dev/null --max-time 20 --write-out '%{http_code}' "$origine/" || true)"
if [[ "$code" != "200" && "$code" != "401" ]]; then
  echo "ATTENTION : $origine répond $code. Vérifie le proxy et le DNS." >&2
fi

# Libère l'espace des images construites il y a plus de 14 jours et inutilisées, sans faire échouer le déploiement.
docker image prune --all --force --filter "until=336h" >/dev/null 2>&1 || true

echo "==> Version $version déployée sur $environnement"
