# 017 — Compte élève et registre des points

## Objectif

Roadmap R2, phase 1. Un élève crée lui-même son compte depuis le site et reçoit une seule fois
100 points de bienvenue. Il retrouve ses points et son profil dans son espace, sans avoir besoin d'un club
(PRD, parcours 1 ; Q4, Q8, Q17, Q20 à Q22).

En même temps, la spec pose le socle des points, que toutes les specs suivantes réutiliseront :

- le registre `mouvement_points` (ADR-0004), où chaque ligne porte son semestre ;
- les semestres, dont l'admin fixe les dates ;
- le barème, réglable depuis l'espace admin.

## Comportement attendu

**Inscription (visiteur)**

1. Depuis la page de connexion (« Pas encore de compte ? ») ou le menu, le visiteur ouvre `/inscription`.
2. Il remplit le formulaire :
   - prénom et nom : visibles seulement de l'espace admin ;
   - pseudonyme : son nom public, unique ;
   - identifiant de connexion et mot de passe ;
   - e-mail : facultatif ;
   - classe : de la 6e à la Terminale ;
   - établissement : choisi par une recherche dans le référentiel (spec 016). S'il ne le trouve pas, il
     le propose : son nom et son IESG. L'établissement est créé avec le statut « proposé », invisible
     du public, et l'inscription continue.
3. Il coche deux cases obligatoires :
   - « J'ai lu et j'accepte la charte des Clubs Santé » ;
   - « Mon parent ou tuteur est d'accord pour que je m'inscrive » (Q8).
4. Il valide. Son compte est actif tout de suite (Q17), il est connecté et arrive sur son espace.
   Un message lui annonce ses 100 points de bienvenue.

**Espace de l'élève (`/mon-espace`)**

- Ses points du semestre en cours et son total historique.
- Ses dernières lignes de points, avec leur motif et leur date.
- Son profil : pseudonyme, classe, établissement, statut « Sans club ».
- Il peut changer sa classe, son établissement, son e-mail et son mot de passe. Le pseudonyme ne change
  que par l'admin.

**Espace admin**

- **Points et classements, semestres** : l'admin crée un semestre (libellé, date de début, date de
  fin), le modifie tant qu'il n'a pas commencé, puis voit le semestre en cours.
- **Points et classements, barème** : l'admin voit la grille de toutes les actions du PRD (élève,
  encadreur, club). Il change un montant ou désactive une action. Le changement vaut pour les gains à
  venir, jamais pour les lignes déjà écrites.
- **Inscrits, fiche d'un élève** : en plus de ce qu'apporte la spec 015, l'admin voit :
  - classe, établissement, DRE, pseudonyme ;
  - ses points (semestre et total) et son registre.

  Il peut aussi :
  - imposer un nouveau pseudonyme, avec un motif ;
  - réinitialiser le mot de passe (Q4) : un mot de passe provisoire s'affiche une seule fois, et toutes
    les sessions de l'élève sont coupées.

- **Clubs et DRE, référentiel, établissements proposés** : l'onglet Établissements de la spec 016
  filtre déjà le statut « proposé ». L'admin y voit combien d'élèves sont rattachés à chaque proposition.
  Il peut alors :
  - l'accepter : l'établissement devient actif, en corrigeant son nom si besoin ;
  - la remplacer par un établissement existant : ses élèves y sont déplacés et la proposition devient
    inactive.
- Toutes ces actions vont au journal d'audit, avec la valeur avant et après.

## Critères d'acceptation

**Inscription**

- [ ] Étant donné un formulaire complet et valide, quand le visiteur s'inscrit, alors :
  - un compte élève actif est créé, avec la date du consentement et la version de la charte ;
  - il est connecté ;
  - une seule ligne de +100 points est écrite au registre, avec la clé `bienvenue:<élève>` et le
    semestre en cours.
- [ ] Étant donné une même inscription envoyée deux fois de suite, alors un seul compte et une seule
      ligne de bienvenue existent.
- [ ] Étant donné un pseudonyme ou un identifiant déjà pris (sans tenir compte des majuscules ni des
      accents pour le pseudonyme), alors l'inscription est refusée avec un message qui nomme le champ.
- [ ] Étant donné une case de consentement ou de charte non cochée, alors l'inscription est refusée
      (vérifié par l'API, pas seulement par le formulaire).
- [ ] Étant donné un établissement inactif ou inconnu, alors l'inscription est refusée.
- [ ] Étant donné un établissement proposé (nom et IESG active), alors :
  - il est créé avec le statut « proposé » et l'élève y est rattaché ;
  - il n'apparaît ni sur la carte, ni dans l'annuaire public, ni dans la recherche publique.
- [ ] Étant donné une proposition dont le nom existe déjà dans cette IESG :
  - si l'établissement existant est actif, la proposition est refusée et le message invite à le choisir ;
  - s'il est déjà proposé, l'élève est rattaché à cette proposition, sans doublon.
- [ ] Étant donné une proposition remplacée par un établissement existant, alors :
  - ses élèves sont rattachés à ce dernier ;
  - la proposition devient inactive ;
  - le journal garde l'ancien et le nouvel établissement.
- [ ] Étant donné un pseudonyme qui contient un e-mail, un numéro de téléphone ou un mot de la liste
      interdite, alors il est refusé.
- [ ] Étant donné que les inscriptions sont fermées dans la configuration (production avant le récépissé
      de l'IPDCP, RULES), alors la route d'inscription répond 403 et la page l'explique.
- [ ] Étant donné plus d'inscriptions depuis une même adresse en une heure que le seuil réglable (20 par
      défaut : une salle informatique partage souvent une adresse), alors les suivantes sont refusées (429).

**Points, semestres et barème**

- [ ] Toute écriture de points passe par une seule fonction du domaine `points`. Cette fonction :
  - lit le montant dans le barème ;
  - rattache la ligne au semestre qui contient sa date ;
  - refuse les doublons grâce à la clé d'idempotence, même en cas d'appels simultanés.
- [ ] Étant donné une action désactivée ou à 0 dans le barème, alors aucune ligne n'est écrite.
- [ ] Étant donné un montant modifié dans le barème, alors les lignes existantes ne changent pas et les
      gains suivants prennent le nouveau montant.
- [ ] Étant donné deux semestres qui se chevauchent, ou une fin avant le début, alors la création est
      refusée.
- [ ] Étant donné un semestre déjà commencé, alors ses dates ne peuvent plus être modifiées, sauf la date
      de fin d'un semestre en cours, qui peut être prolongée.
- [ ] Le total historique d'un élève est la somme de toutes ses lignes ; ses points du semestre sont la
      somme des lignes de ce semestre.
- [ ] Modifier le barème ou les semestres exige le droit `points:modifier`, avec la double
      authentification (ADR-0008). Le consulter exige `points:consulter`.

**Espace élève et admin**

- [ ] Un élève ne voit que ses propres points et son propre profil ; aucune route ne renvoie le nom ou le
      prénom d'un autre élève.
- [ ] Changer de classe ou d'établissement est journalisé dans le compte de l'élève et ne touche pas à
      ses points.
- [ ] L'admin qui impose un pseudonyme ou réinitialise un mot de passe a le droit `inscrits:modifier`.
      L'action est écrite au journal ; la réinitialisation coupe les sessions de l'élève.
- [ ] Le seed de démonstration crée des élèves avec leur pseudonyme, leur établissement et leur ligne de
      bienvenue, ainsi qu'un semestre en cours.

## Cas limites et erreurs

- **Aucun semestre en cours** (vacances, ou avant la première configuration) : la ligne est écrite sans
  semestre. Elle compte dans le total historique, pas dans les points du semestre. L'espace de l'élève
  affiche « Aucun semestre en cours », et le tableau de bord admin le signale.
- **Pseudonyme**
  - Il fait de 3 à 30 caractères : lettres, chiffres, espace, tiret et point.
  - Les espaces sont nettoyés, et la comparaison ignore les majuscules et les accents (« Aya » = « AYA »
    = « Àya »).
  - Il ne peut pas être identique à l'identifiant de connexion, qui reste secret.
- **Identifiant** : même règle que la spec 001 (`a-z0-9._-`, 3 à 30 caractères). Un identifiant pris
  donne le même message qu'un pseudonyme pris, champ par champ.
- **E-mail** : facultatif, unique quand il est donné, mis en minuscules.
- **Mot de passe** : de 8 à 256 caractères, comme la spec 001.
- **Deux inscriptions simultanées avec le même pseudonyme** : la base garantit l'unicité. La seconde
  reçoit le message « pseudonyme déjà pris ».
- **API injoignable pendant l'inscription** : le formulaire garde la saisie (sauf le mot de passe) et
  affiche « Service indisponible ».
- **Compte suspendu** : l'élève ne peut plus se connecter (spec 015). Ses lignes de points restent au
  registre ; les classements de R13 décideront s'ils l'affichent.
- **Un élève connecté ouvre `/inscription`** : il est renvoyé vers son espace.
- **Semestre qui commencerait dans le passé** : refusé. Des points ont pu être gagnés hors semestre, et un
  semestre ouvert après coup ne les contiendrait pas.
  Un semestre peut commencer le jour même : les points gagnés ce jour-là avant sa création restent hors
  semestre. C'est accepté, pour ne pas obliger l'admin à attendre le lendemain.
- **Barème**
  - Un montant est un entier de 0 à 10 000.
  - Une ligne d'action ne se supprime pas, elle se désactive.
  - Deux admins qui modifient la même ligne : la seconde modification reçoit un conflit de version,
    comme dans la spec 016.
- **Établissement désactivé après l'inscription** : le profil l'affiche toujours. L'élève peut en choisir
  un autre, mais pas le réactiver.

## Hors périmètre

- La carte membre et le numéro d'adhérent (R15).
- Les clubs, l'affiliation, et donc le club affiché sur le profil (R4, R5).
- Les classements, le rang, la clôture de semestre et le Top 3 (R13, R14).
- Une correction manuelle des points par l'admin (une ligne négative) : elle arrive avec le module Points
  de R13. Le registre la prévoit déjà, sans écran.
- La réinitialisation du mot de passe par e-mail ou par un encadreur (R5) ; le compte encadreur (R3).
- La photo de profil : interdite pour les élèves (SECURITY).
- La suppression d'un compte par l'élève : elle sera traitée avec l'avis juridique (droits d'accès et
  d'effacement), avant l'ouverture.

## Décisions

- Prénom et nom sont obligatoires mais ne sortent jamais de l'espace admin (RULES, Q20). L'identifiant de
  connexion n'est jamais affiché publiquement non plus : seul le pseudonyme l'est.
- Le barème est une table complète, préremplie avec toutes les lignes du PRD. Chaque spec suivante y lit
  le montant de son action au lieu d'ajouter le sien.
- Les inscriptions s'ouvrent par une variable de configuration, fermée par défaut en production
  (RULES : aucune vraie donnée d'élève avant le récépissé de l'IPDCP). Ce n'est pas un bouton de
  l'espace admin, pour qu'aucun collaborateur ne puisse les ouvrir trop tôt.
- Le montant est copié dans chaque ligne du registre : un total ne dépend jamais du barème actuel.

Validées par le porteur du projet le 2026-11-04 :

- Un élève qui ne trouve pas son établissement le propose. L'admin accepte la proposition ou la
  remplace par un établissement existant.
- Un gain hors semestre compte dans le total historique seulement ; sa ligne n'a pas de semestre.
- Seul l'admin change un pseudonyme, avec un motif (Q20).

## Questions ouvertes

Aucune.
