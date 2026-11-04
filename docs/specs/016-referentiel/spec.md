# 016 — Référentiel : DRE, inspections, établissements et axes

## Objectif

Mettre en base, et rendre modifiables depuis l'espace admin, les listes dont dépendent toutes les specs
suivantes (roadmap R1, PRD « Socle ») :

- le découpage scolaire : les DRE, leurs inspections (IESG) et les établissements ;
- les 7 axes thématiques qui classeront articles, vidéos, quiz, forums, événements et rapports.

Aujourd'hui, ces listes sont écrites en dur à deux endroits : dans le site (`src/lib/togo-dre.ts` et
`src/lib/etablissements.ts`, 7 DRE, 19 IESG et 844 établissements) et dans l'API (le dictionnaire `DRE` du
catalogue des droits, spec 015). Après cette spec, l'API seule fait foi et le site lit ses listes chez elle.

Ce que cette spec rend possible ensuite :

- R2 et R3 : l'élève et l'encadreur choisissent leur établissement à l'inscription ;
- R4 : un club est rattaché à un établissement, dont il tire sa DRE (Q2) ;
- R6 et suivantes : chaque contenu porte un axe.

Sources : [CDC admin](../../cdc/admin.md) § 4.2 et § 15, [PRD](../../PRD.md) Q1, Q2 et Q28.

## Comportement attendu

**Le découpage**

- Le découpage a trois niveaux : DRE, puis IESG, puis établissement. Un établissement appartient à une
  seule IESG, une IESG à une seule DRE.
- La DRE d'un établissement se déduit de son IESG ; elle n'est jamais saisie à part.
- Une DRE a un code stable, par exemple `grand-lome` ou `kara`. Le périmètre des collaborateurs (spec 015)
  et les URL l'utilisent. Il ne change pas quand on renomme la DRE.
- Chaque élément est actif ou inactif. Un élément inactif disparaît des listes publiques et des formulaires,
  mais reste attaché à tout ce qui le référence déjà.
- On ne supprime rien : on désactive. Une faute de frappe se corrige en renommant.

**Chargement initial**

- Au déploiement de la spec, la base reçoit les 7 DRE, les 19 IESG et les établissements de l'annuaire
  du site, avec leur type (lycée, collège, complexe scolaire, autre). C'est le choix validé en Q28.
- Les 7 axes d'intervention sont créés en même temps, dans l'ordre de la page `/les-7-axes` (décision 1).
- L'annuaire du site contient 6 doublons dans une même IESG : 5 à Aného (par exemple « CEG Adeho » et
  « CEG Adého ») et 1 à Dapaong (« CEG Babigou »). Le chargement n'en garde qu'un, la base reçoit donc
  838 établissements.
- Relancer le chargement ne crée aucun doublon.

**Listes publiques** (sans compte)

- Les DRE actives, dans l'ordre de la carte, avec leurs IESG actives.
- Les établissements actifs d'une IESG ou d'une DRE, et une recherche par nom : quelques lettres suffisent,
  sans tenir compte des accents ni des majuscules (« lycee tokoin » trouve « Lycée de Tokoin I »).
- Les axes actifs, dans leur ordre d'affichage, avec leur libellé et leur description courte.
- Ces listes ne contiennent aucune donnée personnelle.

**Sur le site**

- La carte des clubs (`/carte-des-clubs`) lit les établissements et leurs nombres par DRE et par IESG dans
  l'API. Les contours et les couleurs des régions restent dans le site : ce sont du dessin, pas des
  données. La carte affiche toujours des établissements, en attendant les vrais clubs en R4.
- Le sélecteur de DRE du formulaire d'inscription au Génie Imhotep lit la liste de l'API.
- Le Hall of Fame garde les noms des régions tels qu'ils étaient pendant le championnat : un palmarès ne
  se réécrit pas si une DRE est renommée. Seules leurs couleurs viennent du dessin de la carte.
- Les fichiers en dur `etablissements.ts` et la partie données de `togo-dre.ts` disparaissent.

**Dans l'espace admin** (`/admin/referentiel`, module « Clubs et DRE »)

1. Un onglet **DRE et IESG** liste les DRE, chacune avec ses IESG et son nombre d'établissements actifs.
   - On peut renommer une DRE (nom court et nom complet) ou changer son ordre.
   - On peut créer une DRE, avec un code unique, et la désactiver.
   - On peut créer une IESG dans une DRE, la renommer, la déplacer vers une autre DRE ou la désactiver.
   - Déplacer une IESG fait changer de DRE tous ses établissements ; l'écran le dit et demande confirmation.
2. Un onglet **Établissements** liste les établissements, avec une recherche par nom et des filtres par DRE,
   IESG, type et statut.
   - On peut créer un établissement : nom, type, IESG, localité facultative.
   - On peut le modifier, le changer d'IESG, le désactiver ou le réactiver.
3. Un onglet **Axes** liste les 7 axes.
   - On peut modifier le libellé, la description courte et l'ordre d'un axe.
   - On peut créer un axe ou le désactiver.
   - Un axe a lui aussi un code stable, qui ne change pas quand on le renomme.
4. Toute création, modification, désactivation ou réactivation est inscrite au journal d'audit, avec la
   valeur avant et après.
5. Un collaborateur limité à une DRE ne voit et ne modifie que les IESG et les établissements de sa DRE.
6. Le tableau de bord admin affiche le nombre de DRE actives et d'établissements actifs. Les « DRE
   couvertes », celles qui ont au moins un club, attendent R4.
7. Le choix du périmètre d'un collaborateur propose les DRE actives de la base, et non plus une liste
   écrite dans le code.

## Critères d'acceptation

**Chargement initial**

- [ ] Étant donné une base vide, quand les migrations sont appliquées, alors elle contient 7 DRE, 19 IESG
      et 838 établissements actifs, chacun dans l'IESG et la DRE de l'annuaire du site.
- [ ] Étant donné le chargement déjà fait, quand on le relance, alors aucun élément n'est ajouté en double.
- [ ] Étant donné les collaborateurs existants, quand la migration passe, alors leur périmètre DRE est
      conservé.

**Listes publiques**

- [ ] Étant donné une DRE désactivée, quand un visiteur demande la liste des DRE, alors elle n'y figure pas.
- [ ] Étant donné « lycee tokoin », quand un visiteur cherche un établissement, alors les établissements
      actifs dont le nom contient ces mots sont renvoyés, accents et majuscules ignorés.
- [ ] Étant donné une recherche de moins de 2 lettres, quand elle est envoyée, alors l'API la refuse avec
      un message clair.
- [ ] Étant donné un établissement inactif, quand on liste les établissements de son IESG, alors il
      n'y figure pas.
- [ ] Les listes publiques ne renvoient aucun champ réservé à l'administration (auteur, dates de
      modification).

**Modification par l'admin**

- [ ] Étant donné un collaborateur sans le droit de modifier le module « Clubs et DRE », quand il tente de
      créer ou modifier un élément du référentiel, alors l'API refuse (403) et rien n'est écrit.
- [ ] Étant donné un collaborateur limité à la DRE Kara, quand il tente de modifier un établissement de la
      DRE Savanes, alors l'API refuse (403).
- [ ] Étant donné un collaborateur limité à la DRE Kara, quand il liste les établissements dans l'espace
      admin, alors il ne reçoit que ceux de la DRE Kara.
- [ ] Étant donné un établissement « Lycée X » dans une IESG, quand on en crée un second de même nom dans
      la même IESG (accents, majuscules et espaces ignorés), alors l'API refuse le doublon.
- [ ] Étant donné deux établissements de même nom dans deux IESG différentes, alors les deux sont acceptés.
- [ ] Étant donné une IESG déplacée de la DRE A vers la DRE B, alors tous ses établissements apparaissent
      dans la DRE B et le journal enregistre l'ancienne et la nouvelle DRE.
- [ ] Étant donné une DRE renommée, alors son code ne change pas et le périmètre des collaborateurs qui la
      référencent reste valide.
- [ ] Étant donné une modification réussie, alors une entrée du journal d'audit contient l'auteur, l'élément,
      la valeur avant et la valeur après.
- [ ] Étant donné un axe renommé, alors son code ne change pas.

**Garde-fous**

- [ ] Étant donné une DRE qui a encore des IESG actives, quand on la désactive, alors l'API refuse et
      indique qu'il faut d'abord déplacer ou désactiver ses IESG.
- [ ] Étant donné une IESG qui a encore des établissements actifs, quand on la désactive, alors l'API
      refuse de la même façon.
- [ ] Étant donné une DRE qui est le périmètre d'un collaborateur actif, quand on la désactive, alors l'API
      refuse et indique quels collaborateurs changer d'abord.
- [ ] Étant donné une DRE désactivée, quand on invite un collaborateur, alors on ne peut pas la choisir
      comme périmètre.
- [ ] Il n'existe aucune route de suppression du référentiel.

**Site**

- [ ] La carte des clubs affiche les mêmes nombres d'établissements par DRE et par IESG qu'avant la spec,
      moins les 6 doublons retirés (5 dans l'IESG Aného, 1 dans l'IESG Dapaong).
- [ ] Le formulaire du Génie Imhotep propose les DRE actives venues de l'API.
- [ ] Le site ne contient plus de liste d'établissements ni de liste de DRE écrite en dur. Seuls restent
      les contours et les couleurs de la carte, repérés par le code de DRE, et les noms des régions dans
      les résultats historiques du Génie Imhotep.

## Cas limites et erreurs

- **Nom vide, ou fait seulement d'espaces** : refusé. Les espaces en trop autour du nom sont retirés.
- **Nom trop long** : au-delà de 150 caractères, refusé.
- **Code de DRE ou d'axe** : en minuscules, chiffres et tirets, unique. Il ne se modifie pas après la
  création.
- **Doublons**
  - Deux DRE de même nom : refusé.
  - Deux IESG de même nom dans une DRE : refusé.
  - Deux axes de même libellé : refusé.
- **Deux collaborateurs modifient le même élément en même temps** : le second reçoit une erreur
  « modifié entre-temps, recharge la page » plutôt que d'écraser le premier.
- **Déplacement vers une DRE ou une IESG inactive** : refusé.
- **Réactiver un établissement dont l'IESG est inactive** : refusé tant que l'IESG n'est pas réactivée.
- **Désactiver un axe** : autorisé. Les contenus déjà classés le gardent, mais on ne peut plus le choisir.
  Aucun contenu n'existe encore, le cas sera testé avec R6.
- **Désactiver le dernier axe actif** : refusé, il en faut au moins un.
- **API indisponible pendant le chargement de la carte** : la carte affiche ses contours et un message
  « liste momentanément indisponible », sans planter la page.
- **Gros volume** : la liste admin des établissements est paginée (50 par page). La recherche publique
  renvoie au plus 20 résultats.

## Hors périmètre

- **Les clubs eux-mêmes** : création, code unique, président, statut et carte des vrais clubs (R4).
- **L'établissement proposé par un président** lors de la création de son club, puis validé avec lui : c'est
  le circuit décrit en Q28, il arrive avec R4. R1 prévoit seulement un statut « proposé » qui n'apparaît pas
  dans les listes publiques.
- **Les filtres par DRE, établissement ou club** de l'annuaire des inscrits et des exports : ils arrivent avec
  R2, quand les comptes ont un établissement.
- **L'import d'un fichier CSV** pour remplacer ou compléter l'annuaire : la saisie dans l'espace admin
  suffit pour l'instant.
- **La suppression définitive** d'un élément du référentiel.
- **Les coordonnées GPS des établissements** et la géolocalisation sur la carte.
- **Les « univers » de l'accueil et le contenu de la page `/les-7-axes`** restent éditoriaux. La page n'est
  pas générée à partir de la base (décision 1).
- **Le responsable DRE avec délégation sur des clubs désignés** (CDC admin, § 12A) : les périmètres plus fins
  que la DRE attendront R4.

## Décisions

Tranchées par l'utilisateur le 2026-11-04.

1. **Les 7 axes sont les axes d'intervention de la page `/les-7-axes` (Q1).** Ce sont :
   - Génie Imhotep ;
   - Santé sexuelle et EVSS ;
   - Production TV et médias ;
   - Sport et secourisme ;
   - Bourses et excellence ;
   - Leadership et mentorat ;
   - Santé et environnement.

   Ils remplacent les 7 axes de santé publique du cahier des charges initial. La page `/les-7-axes`
   garde son contenu éditorial (slogans, activités, mascottes), présenté dans le même ordre que les axes en
   base. La liste reste modifiable dans l'espace admin.

2. **Les droits sont partagés.**
   - Les DRE, les IESG et les axes sont réservés au super-administrateur. Ce sont des paramètres nationaux
     (CDC admin, § 3).
   - Les établissements se créent et se modifient avec le droit « Clubs et DRE », dans le périmètre du
     collaborateur.
3. **Les établissements importés sont actifs tout de suite.** L'annuaire vient du répertoire officiel ;
   l'admin corrige ensuite ce qui doit l'être.

## Questions ouvertes

Aucune : la spec est prête pour le plan.
