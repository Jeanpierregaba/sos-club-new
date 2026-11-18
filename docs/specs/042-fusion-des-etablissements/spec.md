# 042 — Fusion des doublons d'établissements

## Objectif

L'import de la liste nationale du Secondaire I (spec 035) n'a reconnu un établissement existant qu'à nom identique. Il
a donc créé un second établissement dès qu'une graphie différait : « Lycée de Tokoin I » et « Lycée Tokoin I »,
« CEG Bogou 2 » et « CEG Bogou II ». L'[analyse du 2026-11-18](../../analyses/doublons-etablissements.md) a trouvé
environ 120 doublons certains et une quinzaine de doublons probables parmi les 2 780 établissements.

Chaque doublon :

- divise les élèves et les encadreurs d'un même établissement entre deux fiches, donc entre deux clubs ;
- fausse les nombres de la carte des clubs ;
- trompe l'élève qui s'inscrit, face à deux choix pour son établissement.

La spec 035 avait reporté l'outil de fusion « si le besoin se confirme » : il est confirmé.

Cette spec donne à l'équipe deux outils dans le back office :

- une liste des **doublons probables**, calculée par l'API ;
- une action **Fusionner** qui réunit deux établissements en un seul, sans rien perdre.

L'action remplace le bouton « Remplacer par… » des établissements proposés, qui faisait déjà une petite fusion
(specs 016 et 033).

Sources : [spec 016](../016-referentiel/spec.md) (on ne supprime rien), [spec 033](../033-activation-des-clubs/spec.md)
(club d'un établissement remplacé), [spec 035](../035-annuaire-secondaire-i/spec.md) (doublons laissés à l'équipe),
[RULES](../../RULES.md).

## Comportement attendu

**Vocabulaire**

- Le **gardé** est l'établissement qui reste.
- L'**absorbé** est celui qui disparaît des listes.

**Fusionner** (back office, Référentiel > Établissements)

1. Il y a deux façons de lancer une fusion :
   - depuis une ligne de la liste, avec l'action « Fusionner avec… », puis en cherchant l'autre établissement ;
   - depuis une paire de la page « Doublons probables ».
2. L'écran de fusion montre les deux établissements côte à côte. Pour chacun :
   - son nom, son IESG, sa préfecture, son ordre, son statut et son origine (annuaire ou import) ;
   - son nombre d'élèves et d'encadreurs ;
   - son club, avec son nom, son état et son nombre de membres actifs.
3. Le collaborateur choisit lequel est **gardé**. Par défaut, c'est celui qui a un club au-delà de « en
   constitution », sinon celui qui a le plus d'inscrits, sinon le plus ancien. Un bouton inverse les rôles.
4. Il choisit le **nom final**, celui du gardé ou celui de l'absorbé. Le nom du ministère corrige parfois une faute de
   l'annuaire. La préfecture et l'ordre du gardé sont conservés ; s'ils sont vides, ceux de l'absorbé les remplacent.
5. L'écran annonce ce qui va se passer : « 12 élèves et 1 encadreur rejoindront Lycée de Tokoin I ; le club
   … rejoindra cet établissement ».
6. Il confirme. La fusion se fait en une fois : tout ou rien.

**Effets d'une fusion**

- Les élèves et les encadreurs de l'absorbé sont rattachés au gardé.
- Le gardé prend le nom final, ainsi que la préfecture et l'ordre décrits ci-dessus.
- L'absorbé devient **inactif** et garde un renvoi vers le gardé. Rien n'est supprimé (RULES) :
  - l'absorbé ne paraît plus à l'inscription, sur la carte des clubs ni dans les suggestions ;
  - il reste visible dans le back office, marqué « Fusionné dans … ».
- Le journal d'audit enregistre :
  - les deux établissements, avant et après ;
  - le nom final ;
  - le nombre d'élèves et d'encadreurs déplacés et leurs identifiants ;
  - ce qu'il est advenu des clubs.

**Les clubs**

Un établissement n'a qu'un club vivant (`uq_club_par_etablissement`). Les élèves de l'absorbé étant rattachés au
gardé, son club doit le suivre :

| Club de l'absorbé                    | Club du gardé                      | Résultat                                                                                                                                             |
| ------------------------------------ | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| aucun club vivant                    | quelconque                         | rien à faire                                                                                                                                         |
| en constitution                      | aucun, ou en constitution          | les affiliations et rattachements en cours rejoignent le club du gardé, créé au besoin ; le club de l'absorbé est clos (comportement de la spec 033) |
| en constitution                      | actif, en régularisation, suspendu | idem                                                                                                                                                 |
| actif, en régularisation ou suspendu | aucun club vivant                  | le club passe tel quel au gardé, avec ses membres, ses points, ses contenus et son historique                                                        |
| actif, en régularisation ou suspendu | en constitution                    | le club de l'absorbé passe au gardé ; le club en constitution du gardé est clos et ses affiliations et rattachements en cours le rejoignent          |
| actif, en régularisation ou suspendu | actif, en régularisation, suspendu | **fusion refusée** : deux vrais clubs ne se fusionnent pas ici                                                                                       |

Dans tous les cas, l'activation du club restant est recalculée (spec 033).

**Doublons probables** (back office, Référentiel > Doublons probables)

- L'API calcule les paires d'établissements probablement en double, parmi les établissements actifs ou proposés du
  périmètre du collaborateur. Elle applique les règles de l'analyse :
  - même nom, une fois retirés la ponctuation, les mots « de, du, des, la, le, les » et la différence entre
    chiffres romains et arabes, dans la même DRE ;
  - nom très proche (une ou deux lettres), dans la même DRE, avec la même famille de sigle (CEG, Lycée, privé…) : deux
    IESG voisines rangent parfois le même établissement (Grand Kpendjal et Mango) ;
  - même prononciation (k/c, ou/u, dj/dz/j, lettres doublées), dans la même DRE.
- Chaque paire montre les deux établissements (nom, IESG, préfecture, origine, inscrits, club), la raison du
  rapprochement et deux actions :
  - **Fusionner**, qui ouvre l'écran de fusion ;
  - **Pas un doublon**, pour les annexes, les groupes A et B, ou deux localités proches.
- Une paire écartée ne revient plus, même après un nouvel import. L'écart est journalisé et peut être annulé depuis la
  même page, dans un filtre « Écartées ».
- La liste se lit par DRE, avec le nombre de paires restantes par DRE.

**Établissements proposés**

- « Remplacer par… » disparaît. L'équipe fusionne la proposition, qui devient l'absorbé, dans un établissement de la
  liste, qui devient le gardé. Le résultat est le même qu'aujourd'hui : profils déplacés, club en constitution clos,
  proposition désactivée.
- « Accepter » une proposition est inchangé.

## Critères d'acceptation

- [ ] Étant donné deux établissements actifs de la même DRE, quand un collaborateur ayant « clubs : modifier » les
      fusionne, alors les élèves et les encadreurs de l'absorbé sont rattachés au gardé, l'absorbé devient inactif
      avec un renvoi vers le gardé, et une entrée « etablissement_fusionne » est écrite au journal.
- [ ] Le gardé prend le nom final choisi. Sa préfecture et son ordre sont conservés s'ils sont remplis, sinon
      complétés par ceux de l'absorbé.
- [ ] La version des élèves et des encadreurs déplacés augmente : un profil ouvert avant la fusion ne réécrit pas
      l'ancien établissement.
- [ ] Absorbé sans club vivant : aucun club ne change.
- [ ] Absorbé avec un club en constitution : ses affiliations et rattachements en cours passent au club du gardé,
      créé au besoin, et son club est clos.
- [ ] Absorbé avec un club actif, gardé sans club vivant : le même club, au même identifiant, avec ses membres et ses
      points, est rattaché au gardé.
- [ ] Absorbé avec un club actif, gardé avec un club en constitution : le club actif est rattaché au gardé, le club
      en constitution est clos et ses affiliations en cours rejoignent le club actif.
- [ ] Deux clubs au-delà de « en constitution » : refus 409, avec un message qui nomme les deux clubs, et rien ne
      change.
- [ ] Après la fusion, l'absorbé n'apparaît plus dans la recherche d'inscription, l'annuaire public ni la carte des
      clubs ; le gardé y apparaît sous son nom final.
- [ ] Refus 422 :
  - un établissement fusionné avec lui-même ;
  - deux établissements de DRE différentes ;
  - un gardé qui n'est pas actif.
- [ ] Un collaborateur de DRE ne fusionne que deux établissements de sa DRE (403 sinon). Sans « clubs : modifier »,
      le refus est 403.
- [ ] Un collaborateur qui fusionne avec des versions dépassées (l'un des deux a changé entre-temps) reçoit un refus
      409, et rien ne change.
- [ ] Doublons probables :
  - les paires « Lycée de Tokoin I » et « Lycée Tokoin I », « CEG Bogou 2 » et « CEG Bogou II », « CEG Warkanbou »
    et « CEG Warkambou » sont proposées ;
  - « CPL La Fabienne I » et « CPL La Fabienne III » ne le sont pas ;
  - deux établissements de DRE différentes ne sont jamais proposés.
- [ ] Une paire marquée « Pas un doublon » n'est plus proposée et l'écart est journalisé. Son annulation la fait
      revenir.
- [ ] Un établissement absorbé ou inactif n'apparaît plus dans les doublons probables.
- [ ] La liste des doublons d'un collaborateur de DRE ne contient que sa DRE.
- [ ] Un établissement proposé se fusionne dans un établissement actif, avec le même résultat que l'ancien
      « Remplacer par… ». La route `/remplacer` n'existe plus.
- [ ] Le site : l'écran de fusion annonce ce qui va changer avant la confirmation, et la page des doublons permet
      de fusionner et d'écarter. Il est utilisable à 375 px de large.

## Cas limites et erreurs

- **Fusions en chaîne.** A est fusionné dans B, puis B dans C. Le renvoi de A reste B, et le journal permet de
  remonter la chaîne. Un établissement inactif ne peut pas être choisi comme gardé.
- **Deux collaborateurs sur la même paire, en même temps.** Les deux établissements sont verrouillés et leur version
  est vérifiée. Le second reçoit un refus 409 : « Ces établissements ont changé, recharge la page. »
- **Nom final déjà pris dans l'IESG du gardé** par un troisième établissement (contrainte `iesg_id, nom_normalise`) :
  refus 409, qui le nomme.
- **Absorbé sous une autre IESG de la même DRE** (Grand Kpendjal et Mango, Golfe et Agoényivé) : autorisé. Le gardé
  garde son IESG.
- **Élève en pleine inscription** sur l'absorbé : son compte est déplacé comme les autres. Un formulaire envoyé après
  la fusion avec l'absorbé reçoit l'erreur habituelle d'un établissement inactif.
- **Carte numérique, rapports, agenda** : ils lisent le nom de l'établissement au moment de l'affichage et montrent le
  nom final. Le parcours libre de la fiche élève (texte saisi) n'est pas touché.
- **Paire écartée dont l'un des deux est ensuite renommé** : l'écart porte sur les identifiants et reste valable.
- **Aucun doublon dans le périmètre** : la page le dit (« Aucun doublon probable dans ta DRE »).

## Hors périmètre

- L'annulation d'une fusion. Le journal garde les identifiants déplacés pour une correction manuelle si besoin.
- La fusion de deux clubs qui ont dépassé « en constitution » (membres, points, contenus, rapports).
- La fusion de plus de deux établissements à la fois. On enchaîne les fusions, comme pour « CEG Kondokopé ».
- La fusion automatique, sans confirmation, des doublons certains.
- Les anciens noms gardés comme alias de recherche à l'inscription.
- La fusion d'IESG ou de DRE.

## Questions ouvertes

Aucune. Décisions du 2026-11-18 :

- **Clubs :** le club suit le gardé ; si les deux clubs ont dépassé « en constitution », la fusion est refusée.
- **Doublons probables :** une liste dans le back office, avec « Pas un doublon ».
- **Droits :** le droit « clubs : modifier », dans le périmètre du collaborateur.
- **Propositions :** « Fusionner » remplace « Remplacer par… ».
