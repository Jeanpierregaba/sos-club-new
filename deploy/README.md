# Déploiement sur le VPS

Un seul VPS héberge la preprod et la prod, derrière un même proxy HTTPS. La décision est expliquée dans
[l'ADR 0007](../docs/decisions/0007-deploiement-vps-docker-compose.md).

| Branche   | Environnement | Accès              |
| --------- | ------------- | ------------------ |
| `develop` | preprod       | Public, non indexé |
| `main`    | prod          | Public             |

À chaque push, GitHub Actions vérifie le code, construit les images, les publie sur GitHub Container Registry,
puis lance `deployer.sh` sur le VPS : sauvegarde, migrations, nouveaux conteneurs, et retour automatique à la
version précédente s'ils ne démarrent pas. **Un push sur `main` part en production sans validation
supplémentaire** : sur un dépôt privé en GitHub Free, les approbations de déploiement ne sont pas disponibles.

## Avant la production

- **Données d'élèves** : aucune donnée réelle avant le récépissé de l'IPDCP (`docs/PRD.md`, Q8 et Q9).
- **VPS hors du Togo** : c'est un transfert vers un pays tiers, à signaler d'abord à l'IPDCP (loi n° 2019-014, art. 28).
- **Sauvegardes** : elles restent sur le VPS tant que l'étape 8 n'est pas faite. Si le VPS disparaît, elles disparaissent avec lui.

## Mise en place, une seule fois

Prérequis : un VPS Linux Debian ou Ubuntu en x86-64, et deux noms de domaine pointant vers lui. Prévois au moins
2 vCPU et 4 Go de mémoire : c'est une estimation, à mesurer sous charge.

**1. Préparer le serveur**, en root. Installe Docker depuis la
[documentation officielle](https://docs.docker.com/engine/install/), puis :

```bash
adduser --disabled-password --gecos "" deploiement
```

```bash
usermod -aG docker deploiement
```

```bash
install -d -o deploiement -g deploiement -m 750 /opt/sosclub /opt/sosclub/preprod /opt/sosclub/prod /opt/sosclub/proxy
```

```bash
apt install -y ufw && ufw allow OpenSSH && ufw allow 80,443/tcp && ufw allow 443/udp && ufw enable
```

Si SSH n'écoute pas sur le port 22, remplace `OpenSSH` par ton port, sinon tu te bloques dehors.

Le groupe `docker` donne des droits équivalents à root : la clé de déploiement est donc une clé sensible.
Désactive aussi la connexion SSH par mot de passe.

**2. Créer la clé de déploiement**, sur ton ordinateur :

```bash
ssh-keygen -t ed25519 -f ~/.ssh/sosclub_deploiement -C "github-actions-sosclub" -N ""
```

Copie le contenu de `~/.ssh/sosclub_deploiement.pub`, puis, sur le VPS, en root, colle-le à la place de `CLE_PUBLIQUE` :

```bash
install -d -m 700 -o deploiement -g deploiement /home/deploiement/.ssh
```

```bash
echo "CLE_PUBLIQUE" >> /home/deploiement/.ssh/authorized_keys && chown deploiement:deploiement /home/deploiement/.ssh/authorized_keys && chmod 600 /home/deploiement/.ssh/authorized_keys
```

**3. Lancer le proxy**, sur le VPS, avec l'utilisateur `deploiement`. Copie-y `deploy/proxy/compose.yaml` et
`deploy/proxy/Caddyfile` dans `/opt/sosclub/proxy/`, puis crée `/opt/sosclub/proxy/.env` à partir de
`deploy/proxy/env.example` :

```bash
docker network create web-prod && docker network create web-preprod
```

```bash
cd /opt/sosclub/proxy && chmod 600 .env && docker compose up -d --wait
```

**4. Configurer chaque environnement** : crée `/opt/sosclub/preprod/.env` et `/opt/sosclub/prod/.env` à partir de
`deploy/env.example`, avec un mot de passe différent pour chacun, en droits `600`.

**5. Déclarer les secrets sur GitHub**, depuis ton ordinateur :

```bash
gh secret set VPS_HOTE --body "adresse-du-vps"
```

```bash
gh secret set VPS_UTILISATEUR --body "deploiement"
```

```bash
gh secret set VPS_SSH_KEY < ~/.ssh/sosclub_deploiement
```

```bash
ssh-keyscan -t ed25519 -p 22 adresse-du-vps | gh secret set VPS_KNOWN_HOSTS
```

Si SSH écoute sur un autre port, indique-le dans `-p` ci-dessus et déclare-le aussi :

```bash
gh secret set VPS_PORT --body "2222"
```

Vérifie que l'empreinte obtenue par `ssh-keyscan` est bien celle du serveur, indiquée par ton hébergeur ou par
`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` sur le VPS.

**6. Activer le déploiement.** Tant que cette variable n'existe pas, les pushs lancent seulement les vérifications :

```bash
gh variable set DEPLOIEMENT_ACTIF --body "true"
```

Le prochain push sur `develop` déploie la preprod, le prochain push sur `main` déploie la prod.

**7. Créer le premier admin** de chaque environnement, sur le VPS, une fois celui-ci déployé. Pour la preprod,
remplace `prod` par `preprod` :

```bash
cd /opt/sosclub/prod && docker compose exec -it api python -m app.comptes.creer_compte --role admin --identifiant ton-identifiant --prenom Prénom --nom Nom --email adresse@exemple.tg
```

**Comptes de test de la preprod** (facultatif) : un super-administrateur (2FA active), un encadreur actif, un
élève et un élève président d'un club actif, tous du même établissement de la DRE Grand Lomé. Le script est
refusé hors de la preprod. Relancé, il change les mots de passe et coupe les sessions en cours.

```bash
cd /opt/sosclub/preprod && docker compose exec -T api python -m app.seed_preprod
docker compose exec -T api cat /tmp/comptes-preprod.txt
```

Le fichier d'accès est dans le `/tmp` du conteneur, effacé au prochain déploiement : copie les accès dans un
gestionnaire de mots de passe, efface le terminal (`clear`), puis supprime le fichier
(`docker compose exec -T api rm /tmp/comptes-preprod.txt`). Le script refuse de tourner si l'établissement de
test a déjà un autre club actif, ou si une passation du club de test est en attente : il dit quoi faire.

**8. Programmer les sauvegardes**, sur le VPS, avec `crontab -e` (chaque nuit à 2 h et 3 h, heure du serveur) :

```cron
0 2 * * * /opt/sosclub/prod/sauvegarder.sh >> /opt/sosclub/prod/sauvegardes.log 2>&1
0 3 * * * /opt/sosclub/preprod/sauvegarder.sh >> /opt/sosclub/preprod/sauvegardes.log 2>&1
```

Il reste à copier `/opt/sosclub/prod/sauvegardes/` hors du VPS, de façon chiffrée. Le service reste à choisir.

## Au quotidien

**Revenir à une version précédente** : dans l'onglet Actions de GitHub, lance « Déploiement » à la main, avec
l'environnement et le SHA complet d'un commit déjà déployé. Ou en ligne de commande :

```bash
gh workflow run deployer.yml --ref main -f environnement=prod -f version=SHA_COMPLET
```

Le bouton n'apparaît dans l'onglet Actions qu'une fois `deployer.yml` présent sur `main`. Un retour arrière ne lance
pas les migrations : le code revient en arrière, **pas la base**. Chaque migration doit donc rester compatible avec
la version précédente de l'API.

À la main sur le VPS, sans jeton de registre (les images doivent déjà être sur le serveur) :

```bash
/opt/sosclub/prod/deployer.sh prod SHA_COMPLET --retour-arriere < /dev/null
```

**Restaurer une sauvegarde** : cela efface la base actuelle. Fais d'abord une sauvegarde de l'état actuel, arrête
l'API, recrée une base vide, puis restaure en une seule transaction, qui s'arrête à la première erreur :

```bash
cd /opt/sosclub/prod && ./sauvegarder.sh avant-restauration && docker compose stop api site
```

```bash
docker compose exec -T db dropdb --username sosclub --force sosclub && docker compose exec -T db createdb --username sosclub sosclub
```

```bash
docker compose exec -T db pg_restore --username sosclub --dbname sosclub --single-transaction --exit-on-error < sauvegardes/FICHIER.dump
```

Redéploie ensuite, en retour arrière, **la version qui tournait quand la sauvegarde a été faite** : son nom de
fichier l'indique (`depuis-SHA`). Le schéma de la base correspond alors au code.

**Changer de version majeure de PostgreSQL** : ne change jamais `postgres:18-alpine` directement. Une nouvelle
version majeure démarre sur une base vide. Il faut sauvegarder, déployer la nouvelle image sur un nouveau volume,
puis restaurer comme ci-dessus. Dependabot ignore donc ces montées de version.

**Modifier le proxy** : le CI/CD ne le met pas à jour, car il est partagé par les deux environnements. Après un
changement de `deploy/proxy/`, copie les fichiers sur le VPS, puis :

```bash
cd /opt/sosclub/proxy && docker compose up -d --wait --force-recreate
```

La recréation coupe les connexions quelques secondes. Elle garantit que Caddy lit le nouveau fichier, ce que ne fait
pas toujours un simple rechargement.

**Lire les journaux** :

```bash
cd /opt/sosclub/prod && docker compose logs --tail 100 api site
```

## Ce qui a été vérifié, et ce qui ne l'a pas été

Testé en local, avec les vraies images, un registre local et le vrai Caddyfile : déploiement des deux
environnements, accès et en-têtes via le proxy, connexion et rendu serveur en HTTPS,
séparation des bases et des réseaux (la preprod ne joint pas l'API de prod), adresse réseau non falsifiable,
refus d'une origine en http://, sauvegarde et restauration suivant la procédure ci-dessus, retour automatique après
une version cassée, et retour arrière manuel sans migrations.

Si un déploiement échoue au démarrage, les journaux sont écrits dans `/opt/sosclub/<environnement>/echec-<version>.log`
sur le VPS, et non dans GitHub : ils contiennent les adresses des visiteurs.

Pas encore testé : le workflow GitHub de bout en bout, la publication sur GitHub Container Registry, un vrai VPS
et l'obtention de vrais certificats Let's Encrypt. Le premier déploiement sur la preprod servira à le vérifier.
