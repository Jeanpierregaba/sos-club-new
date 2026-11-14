# 019 — Clubs et présidence

> **Remplacée en partie par la [spec 033](../033-activation-des-clubs/spec.md) (2026-11-10)** : le club ne naît plus d'une demande du président validée par l'admin ; il naît à la première affiliation et s'active au seuil de 3 encadreurs et 21 élèves. La présidence et la passation restent.

## Objectif

Roadmap R4, phase 1 (P0, jalon A — démo pilote). Un élève désigné président demande la création de
l'espace officiel du Club Santé de son établissement ; l'admin (ou le collaborateur de sa DRE) vérifie
et valide ; le club devient visible sur la carte. Le président gère l'espace du club avec son compte
élève. Le club n'a pas de compte (Q3 ; ADR-0003, amendé par cette spec).

Questions liées, toutes tranchées : Q5 (les clubs s'enregistrent eux-mêmes — les chiffres du site sont
provisoires), Q6 (l'admin valide chaque nouveau club après vérification du président, de l'établissement
et des doublons), Q16 (un seul club par établissement ; un encadreur peut encadrer plusieurs clubs, sujet
de R5), Q19 (un encadreur rattaché confirmera le président une fois R5 livré ; pour le premier club d'un
établissement, la vérification se fait par l'admin/la DRE auprès de l'établissement).

Cette spec prépare R5 (affiliations et rattachements) et R8 (espace du président). Elle ne crée ni
affiliation, ni publication, ni points de club.

## Comportement attendu

**Demande de création (élève connecté)**

1. Depuis son espace `/mon-espace`, un élève voit un bloc « Ouvrir l'espace de mon club » tant qu'aucun
   club actif n'existe pour son établissement.
2. Le formulaire affiche :
   - son établissement, lu sur son profil, non modifiable ;
   - le **nom officiel du club** (obligatoire, validé : longueur, unicité normalisée au sein de l'établissement) ;
   - une **description courte** du club (facultative, bornée) ;
   - jusqu'à **3 axes privilégiés**, parmi les 7 axes du référentiel ;
   - des **encadreurs associés**, à titre déclaratif uniquement : pour chaque personne, un nom et un e-mail
     ou un téléphone facultatif — l'admin s'en sert pour vérifier, aucun compte ni rattachement n'est créé ;
   - une case **obligatoire** : « Je confirme être désigné président de ce club par mon établissement ».
3. L'élève valide. Il est connecté et arrive sur son espace : sa demande est « en attente de vérification »,
   rien n'est visible publiquement, aucun point n'est crédité. Son rôle de compte reste `eleve`.
4. Un élève ne peut avoir qu'une demande en attente et ne peut être président actif que d'un seul club.

**Vérification et activation (espace admin)**

5. Une file **« Clubs à valider »** dans l'espace admin : les demandes en attente, des plus anciennes aux
   plus récentes, avec le nom du club, l'établissement et sa DRE, le pseudonyme du demandeur, la date de la
   demande et les encadreurs associés cités. Un compteur apparaît dans le menu et sur le tableau de bord.
   Filtrage par périmètre : national ou DRE de l'établissement (comme la file des encadreurs) ; exiger le
   droit `clubs : approuver` (droit sensible, double authentification requise).
6. **Activer** : le club devient actif ; le demandeur devient le président du club (le rôle de son compte ne
   change pas — le lien club ↔ président est une donnée du club) ; un journal `club_active` est inscrit avec
   l'auteur et la cible.
7. **Refuser** : un motif **obligatoire** (comme pour les encadreurs), que le demandeur lit dans son espace ;
   il peut corriger sa demande et la **renvoyer**, qui repasse en attente, le motif précédent restant au
   journal (`club_redemande`).
8. Un club par établissement :
   - si l'établissement a déjà un club actif, l'activation est refusée (409) ;
   - s'il existe une autre demande en attente pour le même établissement, les deux peuvent coexister jusqu'à
     la première activation ; l'activation de la première refuse l'autre (409), le motif restant visible par
     l'admin. Le refus de la doublure par l'élève est propagé en « refusée » avec un motif automatique ou un
     refus manuel.

**Carte et fiche publique**

9. Un club actif apparaît sur la **carte des clubs** avec sa fiche publique minimale, accessible sans
   compte : nom officiel, établissement (IESG, DRE), axes privilégiés. Rien (ni description riche, ni
   membres, ni actualités) n'est public avant activation. Les compteurs du tableau de bord et de la carte
   (« clubs actifs ») affichent les vrais clubs.
10. La carte n'affiche plus des établissements sans clubs comme si c'en était : les établissements non
    rattachés à un club sont indiqués comme tels (libellé « Aucun club enregistré pour cet établissement »).

**Passation de présidence**

11. Le président d'un club actif voit dans son espace un bouton **« Passer la présidence »**. Il désigne un
    successeur : un élève du même établissement, recherché par pseudonyme (unique, conformément à la spec 017) ;
    lui-même exclu, un élève d'un autre établissement exclu.
12. Le président sortant valide sa proposition ; elle part « en attente » chez l'admin (même file que les
    clubs à valider, ou un onglet « Passations »).
13. **L'admin valide** la passation : l'ancien président perd la gestion du club, le nouveau la reçoit ;
    le club, ses points et son historique (quand ils existeront) restent au club ; l'opération est journalisée
    avec l'auteur, l'avant et l'après (`club_passation`). L'admin peut **refuser** la passation, avec un motif
    obligatoire que le président sortant lit.
14. La passation ne change ni le rôle ni le statut des comptes. Un seul président actif par club, garanti par
    la base au moment de l'activation.

## Critères d'acceptation

- [x] Étant donné un élève connecté dont l'établissement n'a pas de club, quand il envoie une demande valide,
      alors un club « en attente » est créé avec lui comme demandeur, rien n'est publié, et aucun point n'est
      crédité.
- [x] Étant donné un établissement qui a déjà un club actif, quand un élève demande la création d'un club, alors
      l'API répond 409 avec un message indiquant que l'établissement a déjà un club ; rien n'est créé.
- [x] Étant donné deux demandes en attente pour le même établissement, quand l'admin en active une, alors l'autre
      est refusée (409 ou état « refusée ») et le refus se voit dans la file des refusés avec la date et le motif.
- [x] Étant donné une demande valide, quand un collaborateur national ou de la DRE de l'établissement l'active,
      alors le club devient actif, le demandeur devient président, un journal `club_active` est inscrit avec
      l'auteur, et le club apparaît sur la carte avec sa fiche publique minimale.
- [x] Étant donné un étranger à la DRE ou sans le droit `clubs : approuver`, quand il lit la file ou décide,
      alors l'API répond 403 (ou lui cache la demande, 404), comme pour les encadreurs.
- [x] Étant donné un collaborateur avec le droit `clubs : approuver` mais sans double authentification active,
      quand il tente une action, alors l'API répond 403.
- [x] Étant donné deux activations simultanées d'un même club, alors une seule réussit ; un seul président existe.
- [x] Étant donné un refus sans motif, alors l'API répond 422.
- [x] Étant donné un club refusé, quand le demandeur corrige et renvoie sa demande, alors elle repasse en
      attente, le motif précédent reste au journal (`club_redemande`).
- [x] Étant donné un club actif et un élève successeur du même établissement, quand le président propose la
      passation et que l'admin la valide, alors l'ancien président n'a plus accès à la gestion du club, le
      nouveau oui, et le journal `club_passation` enregistre l'avant et l'après ; les données du club
      (y compris futures) restent au club.
- [x] Étant donné une passation vers un élève d'un autre établissement, ou vers soi-même, alors l'API répond
      422 ; la version conservée côté client évite les passations sur un profil modifié entre-temps (comme 018).
- [x] Étant donné une passation refusée par l'admin avec motif, alors le président sortant voit le motif dans
      son espace et reste président.
- [x] Étant donné un visiteur sans compte, quand il ouvre la fiche publique minimale d'un club actif, alors il
      voit nom, établissement (IESG, DRE) et axes ; aucun téléphone, e-mail ou nom complet d'élève n'apparaît ;
      un club en attente est introuvable dans le public.
- [x] Le site affiche le formulaire de demande, l'état de la demande dans l'espace du demandeur (en attente /
      refusée avec motif / actif), la file de validation admin, la carte et les passations — lisibles sur
      téléphone.

## Cas limites et erreurs

- **Demande en double du même élève** : un élève ne peut avoir qu'une demande en attente et ne peut être
  président que d'un seul club. Une nouvelle demande renvoie 409.
- **Établissement proposé** : son club peut être demandé ; l'activation reste possible (comme spec 017/018).
  Si l'établissement est désactivé ou remplacé entre la demande et la décision, la demande est bloquée (409)
  jusqu'à ce que l'établissement soit actif ou remplacé.
- **Nom du club en double** pour le même établissement : refusé (409), après normalisation.
- **Élève président suspendu** avant l'activation : la suspension prime ; l'activation d'un compte suspendu
  est refusée (409). Un club actif dont le président est suspendu reste actif, sans président gestionnaire,
  jusqu'à ce que l'admin décide (passation).
- **Activation concurrente** : verrouillage et idempotence à la ligne, comme pour les encadreurs.
- **Renvoyer une demande refusée** : même circuit que les encadreurs (motif précédent au journal, demande en
  fin de file).
- **Successeur** : pseudonyme inexistant, élève hors de l'établissement, le président lui-même, élève d'un
  club en attente de président → 422. Un élève suspendu ne peut devenir président (409).
- **Refus de passation** : le président sortant reste président.
- **Case du consentement non cochée** : 422 (le consentement à l'espace du club, demandé au formulaire).

## Hors périmètre

- **Affiliations et liste des membres** (R5) : les membres rejoignent le club dans une spec dédiée ; la liste
  n'existe pas encore.
- **Points du club** : le barème les prévoit ; leur attribution sur des actions validées viendra avec les
  specs concernées (quiz, publications, rapports). Aucun point n'est crédité par la création du club.
- **Espace du président** : tableau de bord du club, fiche gérée, actualités, notifications — R8.
- **Rattachements encadreurs** : R5 ; dans cette spec, les encadreurs associés restent déclaratifs.
- **Classements du club** (R13), **fusion/scission de clubs**, **changement d'établissement d'un club**.
- **Photo/logo du club** : aucun stockage de fichiers n'existe encore (ADR-0005) ; ce sera traité avec les
  médias.
- **Le multi-clubs par établissement** : écarté par Q16.

## Questions ouvertes

Aucune. Tranchées le 2026-11-04 :

1. **Vérification du président** : pour le premier club d'un établissement, l'admin (ou la DRE) vérifie par
   l'établissement (téléphone si besoin), comme pour les encadreurs ; à partir de R5, un encadreur rattaché
   confirmera le président dans son espace, puis l'admin validera (Q19).
2. **Contenu de la demande** : nom officiel + établissement (son établissement), description et axes
   privilégiés, encadreurs associés déclaratifs ; pas de photo (pas de stockage) ; consentement de
   confirmation président requise.
3. **Passation** : le président sortant propose un successeur (pseudonyme d'un élève du même établissement),
   l'admin valide ou refuse avec motif ; journalisée (`club_passation`).
4. **Carte** : les vrais clubs actifs, partageant la page publique avec un lien vers la fiche minimale ; les
   établissements sans club sont signalés « Aucun club enregistré ».
5. **Journal** : les consultations de la file ne sont pas journalisées ; seules les décisions le sont.
