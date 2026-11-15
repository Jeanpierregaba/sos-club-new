# 038 — Rapports d'activité, rapports mensuels et bilans semestriels (R12)

Sources : PRD « Rapports d'activités » et barème des encadreurs ; CDC encadreur § 9, CDC président § 7, CDC
admin (file de validation, rapports) ; cahier des charges « Gestion, activation et suivi des Clubs Santé » § 6
(circuit des rapports, statut « reçu / consulté ») ; spec 033 (hors périmètre, point 1) ; ADR-0004, ADR-0005,
ADR-0009 et ADR-0012 ; Q22 et Q29.

Décisions du porteur du projet (2026-11-15) :

- les encadreurs du club **reçoivent** chaque rapport et voient un statut « reçu / consulté » ; ils ne le
  cosignent pas : seule l'équipe (DRE ou nationale) l'approuve, le renvoie en correction ou le refuse ;
- deux rapports sur la **même activité** : le second est approuvé « comme doublon » du premier, lié à lui et
  archivé, **sans aucun point** ; le club n'est crédité qu'une fois ;
- le **résumé public** d'un rapport viendra plus tard, avec les pages publiques des clubs (R21) : ici, tout reste
  privé ;
- le **rapport mensuel** et le **bilan semestriel** entrent dans cette spec, avec le même circuit et leurs
  formulaires propres.

## Objectif

Le rapport d'activité est la fonction centrale de l'encadreur (CDC encadreur § 9) : il prouve qu'une activité a eu
lieu, la documente pour le programme et, une fois approuvé, crédite les points du barème à son auteur et au club.
Le président du club peut aussi en déposer. L'équipe contrôle chaque rapport avant tout crédit. Rien n'est public :
le rapport approuvé rejoint l'archive privée du club.

## Comportement attendu

### 1. Trois modèles de rapport

| Modèle                 | Qui le dépose                  | Champs propres                                                                                                                                                             | Points à l'approbation                                                   |
| ---------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **Rapport d'activité** | Encadreur du club ou président | Titre, type d'activité, axe, date, lieu, responsable ; contexte, objectifs, déroulement, résultats, difficultés, recommandations ; participants ; justificatifs            | Encadreur auteur +100 ; club +50 ; président auteur : club +50 seulement |
| **Rapport mensuel**    | Encadreur du club              | Mois ; synthèse des activités du mois, analyse, difficultés, perspectives ; justificatifs facultatifs. L'écran rappelle les rapports d'activité du mois, sans les recopier | Encadreur auteur +75, une fois par mois                                  |
| **Bilan semestriel**   | Encadreur du club              | Semestre ; synthèse, résultats, analyse, recommandations, perspectives ; participants cumulés ; justificatifs facultatifs                                                  | Encadreur auteur +200, une fois par semestre ; club +100, une fois       |

1. Les montants sont ceux du barème (montants « proposés », Q22) et restent réglables par l'admin ; une ligne
   déjà écrite ne change pas (ADR-0004).
2. Le président n'a pas de point personnel pour un rapport : le barème des élèves n'en prévoit pas.
3. Le mensuel et le bilan synthétisent : ils ne redonnent jamais les points des rapports d'activité du mois ou du
   semestre (CDC encadreur § 9).
4. **Types d'activité** : une liste fermée et modifiable par l'admin (référentiel), par exemple causerie
   éducative, sensibilisation, dépistage, campagne, concours, sortie, autre.
5. **Participants** : nombre total obligatoire ; répartition agrégée facultative (filles, garçons, élèves du club,
   autres). Aucun nom d'élève n'est demandé ; le formulaire rappelle de ne pas en écrire dans les textes.
6. **Justificatifs** (Q29) : photos JPEG, PNG ou WebP ; documents PDF ou Word (`.docx`) ; vidéos par lien YouTube
   seulement (ADR-0005). Au plus 5 photos de 8 Mo (limite des photos de la spec 024) et 5 documents de
   10 Mo, soit 10 fichiers, et 5 liens par rapport. Joindre une photo exige de
   cocher « Les personnes photographiées, ou leurs parents pour les mineurs, ont accepté la prise de vue ».

### 2. Cycle d'un rapport

États : **brouillon → soumis → approuvé / à corriger / refusé**. « Soumis » couvre l'attente et l'examen : il n'y
a pas d'état « en examen » distinct (le circuit de la modération, ADR-0009).

1. L'auteur crée un **brouillon**, le complète en plusieurs fois et le supprime s'il le veut. Un brouillon n'est
   vu que par son auteur.
2. À la **soumission**, l'API vérifie les champs obligatoires, donne au rapport une **référence unique** lisible
   (`RA-2026-000123`, `RM-…`, `BS-…`) et le fige : la version soumise ne change plus.
3. Chaque encadreur du club (et le président pour un rapport d'activité) reçoit une **notification** sur le site.
4. L'équipe examine le rapport et décide, avec un motif sauf pour approuver :
   - **approuver** : les points sont crédités dans la même transaction, une seule fois par rapport ;
   - **approuver comme doublon** d'un rapport approuvé du même club : aucun point, lien visible des deux côtés ;
   - **demander une correction** : l'auteur modifie et soumet une nouvelle version ; l'ancienne reste dans
     l'historique ;
   - **refuser** : définitif, sans point.
5. L'auteur, les encadreurs du club et le président (pour un rapport d'activité) reçoivent chaque décision, avec
   son motif.
6. Un rapport approuvé ne se modifie plus. Ses points peuvent être annulés par l'équipe depuis le registre (spec
   036), motif journalisé, par exemple en cas de fraude ; le rapport reste dans l'archive.

### 3. Doublons

1. Est un **doublon probable** un rapport d'activité du même club, du même type d'activité et à la même date
   qu'un autre rapport soumis ou approuvé, quel que soit l'auteur. Il en va de même pour un deuxième mensuel du
   même encadreur et du même mois, et un deuxième bilan du même encadreur et du même semestre.
2. L'auteur est prévenu au moment de soumettre (« Un rapport du même jour et du même type existe déjà : RA-… »),
   sans être bloqué : deux activités différentes peuvent avoir lieu le même jour.
3. L'examinateur voit l'alerte et les rapports concernés. Il approuve le second comme doublon (aucun point), ou l'approuve
   normalement s'il s'agit d'une autre activité (points habituels).
4. Garde-fou de la base, quelle que soit la décision : un mensuel ne crédite qu'une fois par encadreur et par
   mois, un bilan qu'une fois par encadreur et par semestre, et les +100 du bilan qu'une fois par club et par
   semestre.

### 4. Espace de l'encadreur : « Mes rapports »

1. Un onglet **Rapports** dans l'espace de l'encadreur liste ses brouillons et ses rapports, avec leur état, leur
   référence, la date de la dernière décision et les points obtenus.
2. Un second onglet **Rapports du club** liste les rapports soumis par les autres responsables du club, avec le
   statut « reçu » ou « consulté » de chaque encadreur. Ouvrir un rapport le marque « consulté » pour soi.
3. Les blocs « À faire » de l'accueil encadreur montrent les brouillons à finir et les corrections demandées.
4. **Export** : un rapport approuvé se télécharge en PDF (texte, participants, liste des justificatifs, historique
   des décisions), pour l'archive de l'établissement.

### 5. Espace du président

Le président dépose et suit ses rapports d'activité depuis l'espace du club (spec 026), avec les mêmes écrans. Il
voit les rapports d'activité du club, mais pas les mensuels ni les bilans des encadreurs.

### 6. Admin : examen et archive

1. Les rapports soumis arrivent dans la **file de modération** (ADR-0009), filtrables par modèle, DRE, club, axe
   et date. Un collaborateur de DRE ne voit que les clubs de sa région.
2. L'écran d'examen montre la version soumise, les justificatifs (aperçu des photos, téléchargement des
   documents), les versions précédentes et leurs décisions, l'alerte de doublon et les points qui seront crédités.
3. Un onglet **Rapports** de l'admin sert d'archive : recherche par référence, club, DRE, modèle, état, période ;
   export CSV de la liste, sans nom d'élève.
4. Chaque décision est journalisée : auteur, date, motif, version.

### 7. Club suspendu ou auteur parti

1. Un club suspendu (spec 033) ne dépose plus de rapport ; ses rapports déjà soumis restent examinables, et leurs
   points de club ne sont pas crédités tant qu'il est suspendu (règle actuelle du registre).
2. Un encadreur qui quitte le club garde ses rapports : ils restent rattachés à leur auteur historique et visibles
   dans l'archive du club (cahier « Gestion » § 6).

## Critères d'acceptation

### Dépôt

- [x] Étant donné un encadreur vérifié d'un club en service, quand il soumet un rapport d'activité complet, alors
      le rapport passe « soumis » avec une référence unique et chaque encadreur du club reçoit une notification.
- [x] Étant donné un président, quand il soumet un rapport d'activité, alors il est soumis au nom du club ; il ne
      peut pas créer de mensuel ni de bilan.
- [x] Étant donné un élève qui n'est pas président, un visiteur ou un encadreur d'un autre club, alors le dépôt
      est refusé.
- [x] Étant donné un champ obligatoire manquant ou un nombre de participants négatif, alors la soumission est
      refusée avec un message clair, et le brouillon reste enregistré.
- [x] Étant donné un fichier d'un autre type, de plus de 10 Mo, un sixième document ou une sixième photo, un PDF ou un Word au contenu
      non conforme, ou un lien qui n'est pas YouTube, alors il est refusé.
- [x] Étant donné une photo jointe sans l'attestation cochée, alors la soumission est refusée.
- [x] Une version soumise ne se modifie plus ; un brouillon n'est visible que par son auteur.

### Lecture et confidentialité

- [x] Les encadreurs du club voient les rapports du club ; ouvrir un rapport le marque « consulté » pour celui qui
      l'ouvre, et le statut de chacun est visible des autres.
- [x] Le président voit les rapports d'activité du club, pas les mensuels ni les bilans.
- [x] Un justificatif ne se télécharge que pour l'auteur, les encadreurs du club, le président (rapport d'activité)
      et l'équipe habilitée ; toute autre demande reçoit 404.
- [x] Aucune route publique ne renvoie un rapport ou un justificatif.

### Examen et points

- [x] Étant donné un rapport d'activité d'un encadreur approuvé, alors l'encadreur reçoit +100 et le club +50, une
      seule fois, même si l'approbation est rejouée.
- [x] Étant donné un rapport d'activité du président approuvé, alors le club reçoit +50 et le président aucun
      point.
- [x] Étant donné un rapport approuvé comme doublon, alors aucun point n'est écrit et les deux rapports affichent
      leur lien.
- [x] Étant donné un deuxième mensuel du même encadreur pour le même mois, approuvé, alors il ne crédite rien.
- [x] Étant donné deux bilans du même semestre approuvés pour deux encadreurs du club, alors chacun reçoit +200
      et le club +100 une seule fois.
- [x] Étant donné un rapport à corriger, quand l'auteur soumet sa nouvelle version, alors l'ancienne version et la
      décision restent dans l'historique.
- [x] Étant donné un rapport refusé, à corriger, soumis ou en brouillon, alors aucun point n'est écrit.
- [x] Refuser ou demander une correction sans motif de 10 caractères au moins est refusé.
- [x] Un auteur ne décide jamais de son propre rapport ; un collaborateur de DRE ne voit ni ne décide les rapports
      d'une autre région.
- [x] Deux décisions simultanées sur le même rapport : une seule passe, l'autre reçoit 409.

### Doublons

- [x] Étant donné un rapport d'activité du même club, du même type et de la même date déjà soumis, alors l'auteur
      est prévenu à la soumission sans être bloqué, et l'examinateur voit l'alerte avec la référence de l'autre.

### Export

- [x] Un rapport approuvé s'exporte en PDF avec son historique ; un rapport non approuvé ne s'exporte pas.
- [x] L'export CSV de l'archive admin ne contient aucun nom d'élève et respecte le périmètre du collaborateur.

## Cas limites et erreurs

- **Auteur qui modifie pendant l'examen** : la version soumise est figée ; une modification n'est possible qu'après
  une demande de correction.
- **Deux examinateurs simultanés** : verrou du rapport, le second reçoit 409 (ADR-0009).
- **Encadreur non encore vérifié** (spec 018) : il ne dépose pas de rapport tant que son compte n'est pas vérifié.
- **Club en constitution** : un club pas encore en service peut-il déposer ? Non : le dépôt exige un club en
  service, comme les points de club (spec 033).
- **Rapport approuvé dont le club est ensuite suspendu** : les points déjà écrits restent ; l'annulation passe par
  le registre (spec 036).
- **Changement de barème entre soumission et approbation** : le montant crédité est celui du jour de
  l'approbation.
- **Doublon dont l'original est ensuite annulé** : le doublon ne récupère pas les points ; l'équipe corrige par une
  correction motivée au registre si nécessaire.
- **Fichier envoyé puis brouillon supprimé** : les fichiers du brouillon sont supprimés avec lui.
- **Date d'activité dans le futur** : refusée ; date de plus d'un an : refusée (l'archive des années passées
  viendra avec l'année académique).
- **Mois ou semestre pas encore terminé** : un mensuel se soumet à partir du dernier jour du mois, un bilan à
  partir du dernier jour du semestre.
- **Auteur suspendu ou encadreur plus vérifié avant l'examen** : l'approbation est refusée (règle du moteur) ;
  l'équipe refuse le rapport avec un motif ou attend le retour du compte.
- **Club sans encadreur vérifié** : le rapport du président part à l'équipe, sans autre destinataire.
- **Texte qui contient un nom d'élève** : la plateforme ne peut pas le détecter ; le formulaire le rappelle et
  l'examinateur demande une correction.

## Hors périmètre

- Le **résumé public** d'un rapport approuvé et sa page publique : avec les pages publiques des clubs (R21).
- Le **lien avec un événement de l'agenda** : avec l'agenda du club (R16, spec suivante de la spec 033) ; le
  rapprochement par club, date et type en tient lieu d'ici là.
- Les **archives par année académique** et leur export annuel : avec l'année académique (suites de la spec 033).
- La cosignature des rapports par les encadreurs.
- Les actions « projet d'élèves accompagné » (+150) et « mobilisation de 10 participants » (+50) : elles
  demandent leur propre preuve.
- Les **rapports de dépistage MNT** : données de santé de mineurs, exclus du MVP (PRD).
- La détection automatique de fraude : R22.
- Les e-mails : les notifications restent sur le site (ADR-0009).

## Questions ouvertes

Aucune pour le comportement : les quatre questions ont été tranchées le 2026-11-15.

À régler dans le plan : le compte collectif du club n'a pas encore de ligne propre dans le registre (chaque ligne
porte une personne, et la part d'un club est la moitié du gain d'un élève, ADR-0012). Les +50 et +100 du club
demandent d'amender l'ADR-0012.
