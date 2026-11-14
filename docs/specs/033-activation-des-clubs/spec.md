# 033 — Activation automatique des clubs, régularisation et carte nationale

Source : `Cahier_des_charges_Gestion_Activation_Clubs_Sante.docx` (porteur du projet, 2026-11-10), sections 1 à 4,
7, 10 et 11. Arbitrages du porteur le 2026-11-10 :

| Question                                | Décision                                                                          |
| --------------------------------------- | --------------------------------------------------------------------------------- |
| Que devient la demande du président ?   | **Tout automatique** : le club naît et s'active seul ; le président vient ensuite |
| Qui confirme l'affiliation d'un élève ? | Un encadreur vérifié du même établissement                                        |
| Club actif qui passe sous 21 élèves     | Même délai de 15 jours que le désistement, puis « Suspendu »                      |
| Club suspendu                           | Gel léger, retour automatique à « Actif » quand le seuil revient                  |

Cette spec remplace la naissance des clubs de la [spec 019](../019-clubs-et-presidence/spec.md) (demande du président
validée par l'admin) et le circuit d'affiliation de la [spec 020](../020-affiliations-et-rattachements/spec.md)
(président puis collaborateur). Elle amende Q5, Q6, Q16 et Q19 du PRD.

Le reste du cahier des charges fait l'objet de specs suivantes (voir « Hors périmètre »).

## Objectif

Le Club Santé est un compte collectif rattaché à un établissement. Trois informations sont distinctes et ne se
confondent jamais : son **existence sur le terrain** (club déclaré), son **activation sur la plateforme** (seuil de
3 encadreurs et 21 élèves atteint) et, plus tard, ses **performances annuelles**. L'activation est calculée par
l'API seule, à partir des affiliations confirmées, et chaque changement de statut est tracé.

## Comportement attendu

### Référentiel

1. La géographie scolaire devient **Région → DRE → Inspection → Établissement**. Chaque DRE est rattachée à une des
   5 régions du Togo (Maritime, Plateaux, Centrale, Kara, Savanes). Rien d'autre ne change dans le référentiel.
2. L'élève et l'encadreur choisissent leur établissement à l'inscription, dans la liste contrôlée (déjà le cas).

### Affiliations

3. **Élève.** À l'inscription, ou quand il change d'établissement, son affiliation à l'établissement est créée
   « à confirmer ». Un encadreur **vérifié** du même établissement la confirme ou la refuse (motif obligatoire) depuis
   son espace. Tant qu'elle n'est pas confirmée, l'élève ne compte pas dans le seuil. L'élève voit l'état de son
   affiliation et le statut du club de son établissement.
4. **Encadreur.** Un encadreur dont le compte est vérifié par l'équipe (spec 018) est affilié à l'établissement de
   son profil : la vérification de l'équipe vaut confirmation.
5. **Un seul club à la fois.** Un élève ou un encadreur n'est membre actif que d'un seul club. Un changement
   d'établissement clôt l'affiliation précédente (date de sortie) et en ouvre une nouvelle : l'historique garde les
   deux.
6. **Comptes qui sortent du compte.** Un compte suspendu, supprimé ou dont l'encadreur n'est plus vérifié ne compte
   plus, sans effacer son historique d'affiliation.

### Statuts du club

7. Chaque établissement a au plus un Club Santé. Le club existe dès la première affiliation enregistrée sur
   l'établissement, sous le nom « Club Santé — _nom de l'établissement_ ».

   | Statut            | Quand                                                                   |
   | ----------------- | ----------------------------------------------------------------------- |
   | En constitution   | Des affiliations existent, le seuil 3 + 21 n'est pas atteint            |
   | Actif             | Au moins 3 encadreurs et 21 élèves confirmés, uniques, comptes actifs   |
   | En régularisation | Était actif, passe sous l'un des seuils ; échéance à J+15 (calendaires) |
   | Suspendu          | Échéance passée sans retour au seuil                                    |

   Indépendamment de ces statuts, un club peut être **déclaré sur le terrain** : c'est une information à part, posée
   par l'équipe, qui ne donne aucun accès.

8. **Recalcul.** À chaque événement qui change les effectifs (confirmation, refus, retrait, changement
   d'établissement, vérification ou refus d'un encadreur, suspension ou suppression d'un compte, désistement
   confirmé), l'API recompte les membres éligibles du club concerné et applique les transitions :
   - en constitution → actif quand les deux seuils sont atteints ;
   - actif → en régularisation quand l'un passe dessous ; l'échéance est posée à J+15 ;
   - en régularisation → actif si les deux seuils reviennent avant l'échéance ;
   - en régularisation → suspendu à l'échéance ;
   - suspendu → actif dès que les deux seuils reviennent.
9. **Journal.** Chaque changement de statut est enregistré avec sa date, l'ancien et le nouveau statut, la cause
   (événement déclencheur) et les effectifs du moment. Rien n'est effacé ; la date de première activation reste.
10. **Notifications.** À l'activation, à l'ouverture d'une régularisation (avec la date limite), à J+7, à J+14 et à
    la suspension : notification interne aux encadreurs du club et au président s'il y en a un ; l'équipe voit les
    mêmes événements dans son suivi.

### Désistement d'un encadreur

11. Un encadreur affilié au club peut signaler qu'un autre encadreur du club s'est désisté, avec un motif
    obligatoire. Il ne peut pas se signaler lui-même par ce biais (il quitte le club en changeant d'établissement ou
    en demandant la fermeture de son compte).
12. Le signalement ne retire personne. L'équipe le confirme ou le rejette (motif). Un seul signalement en attente par
    encadreur visé.
13. Confirmé, l'encadreur visé n'est plus membre actif du club (date de sortie) ; son compte et ses contributions
    restent. Le recalcul (point 8) ouvre la régularisation si le club passe à 2 encadreurs.

### Président

14. Un club actif sans président peut en recevoir un : un encadreur affilié propose un élève affilié confirmé, puis
    l'équipe valide, comme la passation actuelle (Q19). Les droits du président (spec 026) ne changent pas.
15. Un président dont le club est suspendu garde son titre mais ne peut rien publier tant que dure la suspension.

### Club suspendu (gel léger)

16. Un club suspendu ne publie plus (actualités, rapports quand ils existeront), ne gagne plus de points de club et
    sort des classements de clubs. Ses membres gardent leurs comptes, leurs points personnels et leur historique.
    La carte l'affiche « suspendu ». Il redevient actif automatiquement quand le seuil revient (point 8).

### Carte nationale

17. La page « Carte des Clubs Santé » affiche trois chiffres calculés à partir des données réelles :
    - **Établissements** : établissements actifs du référentiel ;
    - **Clubs Santé** : clubs déclarés sur le terrain **ou** actifs, en régularisation ou suspendus sur la plateforme,
      chacun compté une seule fois ;
    - **Clubs actifs** : clubs au statut « Actif » ou « En régularisation ».
18. Filtres : région, DRE, inspection, et recherche par nom d'établissement. Chaque fiche montre le nom de
    l'établissement, sa localisation et le statut du club (« Référencé », « En constitution », « Actif »…). Jamais de
    contact, jamais de nom d'élève, jamais d'effectif nominatif.
19. Sans donnée, la carte affiche un état neutre (« Aucun club pour l'instant »), jamais de chiffre fictif. Les
    chiffres provisoires actuels (844 clubs…) disparaissent.

### Espace des encadreurs (minimum de cette spec)

20. Dans son espace, l'encadreur voit une rubrique **« Mon Club Santé »** : établissement et rattachements
    (région, DRE, inspection), statut, date d'activation, échéance éventuelle, effectifs (encadreurs et élèves
    confirmés, sans liste nominative d'élèves), liste des encadreurs du club, file des affiliations d'élèves à
    confirmer, et le signalement de désistement. Les blocs agenda, rapports, chiffres d'activité et archives
    viendront avec leurs specs.

### Équipe nationale (espace admin)

21. Un écran « Suivi des clubs » liste les clubs avec leur statut, leurs effectifs, l'échéance éventuelle et le
    marqueur « déclaré sur le terrain » ; filtres par statut, région, DRE, inspection. La fiche d'un club montre les
    membres pris en compte (encadreurs nommés ; élèves par pseudonyme), le journal des statuts et les signalements.
22. L'équipe confirme ou rejette les désistements, marque ou retire « déclaré sur le terrain » (avec une note), et
    consulte les seuils (3 encadreurs, 21 élèves, 15 jours), fixés dans le code. Les droits suivent l'ADR-0008 :
    un collaborateur de DRE n'agit que dans sa DRE.

## Critères d'acceptation

- [ ] Étant donné 2 encadreurs et 21 élèves confirmés, alors le club reste « en constitution ».
- [ ] Étant donné 3 encadreurs et 20 élèves confirmés, alors le club reste « en constitution ».
- [ ] Étant donné 3 encadreurs et 20 élèves confirmés, quand un encadreur confirme le 21e élève, alors le club passe
      « actif », le journal enregistre l'activation (date, 3, 21, cause) et les encadreurs sont notifiés.
- [ ] Un élève dont l'affiliation n'est pas confirmée, ou dont le compte est suspendu, ne compte pas.
- [ ] Un même élève ne compte qu'une fois, même après deux demandes ou un aller-retour entre établissements.
- [ ] Un élève qui change d'établissement quitte le décompte de l'ancien club et entre « à confirmer » dans le
      nouveau ; l'historique garde les deux affiliations.
- [ ] Un encadreur d'un autre établissement ne peut ni voir ni confirmer les affiliations d'un club (404, comme
      une affiliation inexistante : rien ne révèle qu'elle existe).
- [ ] Un signalement de désistement non confirmé ne change ni les effectifs ni le statut.
- [ ] Désistement confirmé sur un club actif à 3 encadreurs : statut « en régularisation », échéance J+15, alertes.
- [ ] Un 3e encadreur vérifié avant l'échéance : retour à « actif ».
- [ ] Échéance passée sans régularisation : « suspendu » ; publications et points de club refusés ; comptes,
      historique et points personnels intacts.
- [ ] Un club suspendu qui retrouve 3 + 21 redevient « actif » sans intervention.
- [ ] Un club actif qui passe à 20 élèves entre en régularisation.
- [ ] Deux confirmations simultanées qui franchissent le seuil ne créent qu'une activation dans le journal.
- [ ] La carte renvoie trois chiffres distincts, sans double compte, et zéro sur une base vide ; aucune donnée
      personnelle ni contact dans la réponse publique.
- [ ] Les filtres région, DRE et inspection de la carte renvoient les bons établissements.
- [ ] Un collaborateur de DRE ne voit et ne traite que les clubs de sa DRE.

## Cas limites et erreurs

- **Concurrence** : deux confirmations ou un désistement et une confirmation en même temps → le recalcul se fait sous
  verrou du club ; le statut final est le même quel que soit l'ordre.
- **Échéance sans visite** : personne n'ouvre la plateforme le jour J+15 → le statut « suspendu » est quand même
  appliqué (tâche quotidienne, et vérification à la lecture).
- **Encadreur seul de son établissement** : il ne peut confirmer que des élèves de son établissement ; sans encadreur
  vérifié, les affiliations restent à confirmer (l'équipe peut confirmer à sa place).
- **Encadreur qui se désiste en étant le dernier confirmateur** : les affiliations en attente restent en attente.
- **Signalement abusif** : rejeté par l'équipe avec motif ; l'encadreur visé n'est jamais notifié d'un signalement
  rejeté.
- **Clubs existants (spec 019)** : les clubs actifs et en attente sont repris sous le nouveau modèle ; leurs
  adhésions actives deviennent des affiliations confirmées ; leur statut est recalculé à la migration (un club actif
  sous le seuil passe en constitution, sans délai) — voir décision 3.
- **Établissement désactivé** : son club garde son historique mais n'apparaît plus sur la carte.
- **Retrait d'un élève** : seul un encadreur du club peut retirer un élève (motif obligatoire) ; le président ne le
  peut plus, pour qu'un élève ne puisse pas faire basculer son club sous le seuil. Le retrait par l'équipe, depuis la
  fiche de suivi, reste à faire (suite signalée par la relecture du 2026-11-10).
- **Affiliation refusée ou retirée** : l'élève peut la redemander depuis son espace ; elle repart « à confirmer ».
- **Établissement proposé remplacé** (spec 016) : les affiliations et rattachements de son club passent, dans leur
  état, au club du bon établissement, et le club de la proposition est clos.

## Hors périmètre

Specs suivantes, à écrire dans cet ordre :

1. **Rapports d'activité (R12 amendé)** : circuit, notification aux encadreurs du club, statut « reçu / consulté »,
   modération, points sans double crédit.
2. **Agenda du club (R16 amendé)** : propositions des encadreurs, validation avant publication.
3. **Année académique** : calendrier configurable, remise à zéro annuelle des compteurs et classements, semestres en
   sous-périodes (amende ADR-0004, R13 et R14), bonus renouvelables.
4. **Archives par année** : rapports, membres avec dates d'entrée et de sortie, agenda, performances ; export annuel
   pour l'équipe.
5. **Chiffres clés de « Mon Club Santé »** (activités, rapports, points annuels, position), qui dépendent de 1 à 3.

Aussi hors périmètre : la procédure d'appel d'une suspension, la déclaration des clubs de terrain par les
établissements eux-mêmes (ici seule l'équipe la pose), le compte « secrétaire » du club.

## Décisions (validées le 2026-11-10)

1. **Encadreur sur un seul club (amende Q16).** Celui de l'établissement de son profil ; les rattachements
   supplémentaires existants sont clos à la migration, avec leur historique.
2. **Élève sans encadreur vérifié dans son établissement.** Un collaborateur de la DRE (ou l'équipe nationale) peut
   confirmer ou refuser l'affiliation à la place d'un encadreur.
3. **Clubs actifs sous le seuil à la migration.** Ils passent « en constitution » sans délai ; l'équipe peut les
   marquer « déclarés sur le terrain » pour qu'ils restent comptés sur la carte.
4. **Ce que voit l'encadreur des élèves.** Pseudonyme et classe des élèves à confirmer et confirmés, jamais la fiche
   d'adhésion (spec 030) ni le nom complet.

## Questions ouvertes

Aucune.
