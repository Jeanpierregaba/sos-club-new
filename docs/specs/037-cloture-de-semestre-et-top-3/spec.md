# 037 — Clôture de semestre et Top 3 (R14)

Source : `docs/PRD.md`, section « Classements », Q21 et Q25, vocabulaire « Top 3 semestriel » et « Hall of Fame » ;
`docs/cdc/eleve.md`, § 8 ; `docs/cdc/admin.md`, § 9 ; `docs/cdc/encadreur.md`, § 11.2 ; `docs/ROADMAP.md`, R14 ;
spec 036 (classements, registre, corrections) et spec 034 (clôture de l'année académique) ; ADR-0004, ADR-0012 et
ADR-0013.

Décisions déjà prises :

- le Top 3 est **national** et ne concerne que les **élèves** (Q25) ; les distinctions des encadreurs viendront
  plus tard, si les organisateurs les approuvent ;
- les distinctions sont **Grand Champion**, **Vice-Champion** et **Jeune Talent** du semestre (CDC élève, § 8) ;
- la plateforme ne gère que des **points virtuels** et des **palmarès** ; les lots et dotations relèvent d'un
  règlement distinct, hors de la plateforme (PRD) ;
- un élève n'apparaît publiquement que par son **pseudonyme** et son club (`docs/RULES.md`, voir la question
  ouverte de la spec 036) ;
- le semestre suivant **repart de zéro** : c'est déjà le cas, le classement du semestre est une somme filtrée par
  semestre ; l'historique est conservé (ADR-0004).

Décisions du porteur du projet (2026-11-15) :

- l'ex æquo se tranche par une **règle publiée et automatique** : à points égaux, l'élève qui a atteint ce total
  le **premier** passe devant ;
- un **seul admin** peut geler, valider et publier : pas de contrôle à quatre yeux ;
- une distinction ne rapporte **aucun point** : le titre seul ; les lots relèvent du règlement ;
- avant publication, l'admin peut **annuler une validation**, avec un motif, pour revenir à l'état gelé.

Choix de mise en œuvre proposés avec le plan :

- le contrôle antifraude est **manuel** : l'admin examine les candidats et peut en **écarter** un avec un motif ;
  la détection automatique d'anomalies reste R22 ;
- le gel est **déclenché par l'admin** après la date de fin du semestre, pas par une tâche planifiée.

## Objectif

À la fin de chaque semestre, l'équipe nationale fige le classement national des élèves, le contrôle, tranche les
égalités selon une règle publiée, valide puis publie le Top 3. Le palmarès reste consultable pour toujours sur le
Hall of Fame, et chaque lauréat voit sa distinction dans son espace. Cela couvre la ligne du PRD « En fin de
semestre, l'admin gèle le classement, le contrôle, tranche les ex æquo et publie le Top 3 des élèves ».

## Comportement attendu

### 1. Cycle d'une clôture

Une clôture de semestre passe par quatre états, toujours dans cet ordre :

| État       | Ce qui se passe                                                                                   |
| ---------- | ------------------------------------------------------------------------------------------------- |
| **Ouvert** | Le semestre est en cours ou terminé, rien n'est figé. C'est l'état de tous les semestres actuels. |
| **Gelé**   | Le classement national des élèves est **photographié** : rang, pseudonyme, club, DRE, points.     |
| **Validé** | L'admin a contrôlé les candidats et confirmé le Top 3. Rien n'est encore public.                  |
| **Publié** | Le palmarès est public sur le Hall of Fame, les lauréats sont notifiés. Il ne change plus jamais. |

1. Le **gel** n'est possible qu'**après la date de fin** du semestre (heure de Lomé, UTC). Il enregistre le
   classement national des élèves du semestre tel que calculé par la spec 036, au moment du clic, avec les points
   et le rang de chacun. Les **50 premiers** sont enregistrés, pour que l'admin ait des remplaçants s'il écarte des
   candidats.
2. Après le gel, les points du registre peuvent encore bouger (correction, annulation d'une fraude). La photo, elle,
   ne bouge pas. L'admin peut **regeler** tant que la clôture n'est pas publiée : la nouvelle photo remplace
   l'ancienne, et la page signale l'écart entre la photo et le classement actuel.
3. Le **Top 3 proposé** est calculé à partir de la photo : les trois premiers candidats **non écartés**, dans
   l'ordre du classement figé, égalités tranchées par la règle publiée (§ 3).
4. La **validation** confirme ce Top 3. Elle exige que chaque place soit pourvue, sauf si moins de trois élèves
   sont classés (§ cas limites). Tant que la clôture n'est pas publiée, l'admin peut **annuler la validation**
   avec un motif (10 à 500 caractères) : la clôture revient à l'état gelé, et il peut de nouveau écarter,
   réintégrer ou regeler.
5. La **publication** rend le palmarès public, notifie les lauréats dans leur espace et fige la clôture
   définitivement. Après publication, une erreur se signale hors de la plateforme ; aucune route ne modifie un
   palmarès publié.

### 2. Contrôle des candidats (antifraude manuel)

1. Sur une clôture gelée, l'admin voit les candidats en tête du classement figé avec, pour chacun : rang, points,
   pseudonyme, identifiant, club, DRE, statut du compte, nombre de corrections et d'annulations du semestre, et un
   lien vers ses lignes dans le registre (spec 036, filtre du semestre).
2. Il peut **écarter** un candidat avec un **motif** obligatoire (10 à 500 caractères), par exemple fraude avérée,
   compte suspendu, inéligibilité au règlement. Le candidat suivant monte d'un cran dans le Top 3 proposé.
3. Il peut **réintégrer** un candidat écarté tant que la clôture n'est pas validée.
4. Un élève suspendu, ancien élève ou supprimé au moment du gel n'est pas dans la photo, comme dans le classement
   public de la spec 036.
5. Écarter un candidat ne retire aucun point : pour retirer des points frauduleux, l'admin passe par le registre
   (annulation ou correction de la spec 036), puis regèle.

### 3. Ex æquo : règle publiée

1. Les classements courants (spec 036) montrent les égalités telles quelles : même rang partagé.
2. Pour le Top 3, les égalités sont tranchées **automatiquement** : à points égaux, passe devant l'élève dont le
   total du semestre a été **atteint le plus tôt** (date de la ligne qui l'a porté à ce total). À date identique,
   ce qui n'arrive qu'en théorie, l'ordre alphabétique du pseudonyme tranche.
3. La règle est écrite en clair sur la page publique du palmarès et sur l'écran de l'admin.
4. La photo enregistre, pour chaque candidat, son rang départagé et son rang brut, pour que l'égalité reste
   visible dans l'archive.

### 4. Palmarès public (`/hall-of-fame`)

1. La page `/hall-of-fame` gagne une section **Palmarès des semestres** : pour chaque semestre publié, du plus
   récent au plus ancien, le libellé et les dates du semestre, puis les trois lauréats avec leur distinction,
   leur **pseudonyme**, leur **club** (s'ils en ont un) et leur **DRE**, et leurs points du semestre.
2. Aucun nom complet, identifiant, e-mail, téléphone ou photo n'apparaît. Les candidats écartés et les motifs ne
   sont jamais publics.
3. Un semestre gelé ou validé mais non publié n'apparaît pas. Sans aucun palmarès publié, la section affiche un
   état vide (« Le premier palmarès sera publié à la fin du semestre. »).
4. Le palmarès publié reste tel quel même si l'élève change de pseudonyme, de club ou devient ancien élève : la
   photo garde les valeurs du gel.

### 5. Espace du lauréat

1. À la publication, chaque lauréat reçoit une **notification** (centre de notifications, spec 023) : « Tu es
   Grand Champion du semestre … ».
2. Son espace élève affiche ses distinctions dans un bloc **Mes distinctions** (distinction, semestre, points).
3. Aucun point n'est accordé pour une distinction : le barème actuel ne prévoit rien. Les lots relèvent du
   règlement.

### 6. Admin (`/admin/points/clotures`)

1. Un onglet **Clôtures** rejoint Semestres, Barème, Années, Gold, Registre et Classements.
2. Il liste les semestres avec leur état de clôture et l'action possible : **Geler** (semestre terminé, ouvert),
   **Contrôler** (gelé), **Publier** (validé), **Voir** (publié).
3. L'écran d'une clôture montre la photo, le Top 3 proposé, les candidats écartés avec leur motif, l'auteur et la
   date de chaque étape, et l'écart éventuel avec le classement actuel.
4. Chaque étape (gel, regel, écart, réintégration, validation, publication) est écrite au **journal d'audit**.
5. Toutes ces actions exigent le droit `points:modifier`, le **périmètre national** et la **double
   authentification** ; la consultation exige `points:consulter`, national, double authentification (mêmes
   droits que le registre).
6. Un même admin peut faire toutes les étapes (décision du 2026-11-15) ; le journal garde l'auteur de chacune.

## Critères d'acceptation

### Gel

- [ ] Étant donné un semestre dont la date de fin n'est pas passée, quand l'admin demande le gel, alors l'API
      refuse avec un message clair.
- [ ] Étant donné un semestre terminé avec des élèves classés, quand l'admin gèle, alors la photo contient les 50
      premiers élèves du classement national du semestre, avec rang, rang brut, pseudonyme, club, DRE et points.
- [ ] Étant donné un élève suspendu ou ancien élève, alors il n'est pas dans la photo.
- [ ] Étant donné une clôture gelée, quand une correction change les points d'un candidat, alors la photo ne
      change pas et l'écran signale l'écart ; un regel prend la correction en compte.
- [ ] Étant donné deux gels simultanés du même semestre, alors une seule clôture existe.
- [ ] Étant donné une clôture validée ou publiée, alors le regel est refusé.

### Ex æquo

- [ ] Étant donné deux élèves à égalité de points, alors celui qui a atteint ce total le plus tôt passe devant
      dans le Top 3, et la photo garde leur rang brut identique.
- [ ] Étant donné une égalité à la même seconde, alors l'ordre alphabétique du pseudonyme tranche.

### Contrôle

- [ ] Étant donné un candidat du Top 3 proposé, quand l'admin l'écarte avec un motif, alors le candidat suivant
      entre dans le Top 3 proposé et le motif est journalisé.
- [ ] Étant donné un motif de moins de 10 caractères, alors l'écart est refusé.
- [ ] Étant donné un candidat écarté, quand l'admin le réintègre avant validation, alors il retrouve sa place.
- [ ] Étant donné une clôture validée, alors écarter ou réintégrer est refusé.

### Validation et publication

- [ ] Étant donné une clôture gelée, quand l'admin valide, alors le Top 3 est figé dans l'ordre proposé.
- [ ] Étant donné une clôture validée, quand l'admin publie, alors le palmarès apparaît sur `/hall-of-fame` et
      chaque lauréat reçoit une notification ; aucun point n'est écrit au registre.
- [ ] Étant donné une clôture validée, quand l'admin annule la validation avec un motif, alors elle revient à
      l'état gelé et l'annulation est journalisée ; sans motif valable, elle est refusée.
- [ ] Étant donné une clôture publiée, alors l'annulation de la validation est refusée.
- [ ] Étant donné une clôture publiée, alors aucune route ne permet de la modifier, de la regeler ou de la
      supprimer.

### Public et espace élève

- [ ] La réponse publique du palmarès ne contient ni nom complet, ni identifiant, ni e-mail, ni téléphone, ni
      candidat écarté, ni motif.
- [ ] Un semestre gelé ou validé mais non publié n'apparaît pas dans le palmarès public.
- [ ] Étant donné un lauréat qui change ensuite de pseudonyme ou de club, alors le palmarès publié garde les
      valeurs du gel.
- [ ] Un lauréat voit sa distinction dans son espace ; un autre élève ne la voit pas dans le sien.
- [ ] Sans palmarès publié, la section affiche un état vide.

### Droits

- [ ] Chaque route admin de clôture exige le droit attendu, le périmètre national et la double
      authentification ; un collaborateur de DRE est refusé.
- [ ] Chaque étape est écrite au journal d'audit avec son auteur, sa date et le semestre.

## Cas limites et erreurs

- **Moins de trois élèves classés** : le Top 3 n'a que les places pourvues ; la validation est possible ; les
  places vides ne sont ni affichées ni notifiées.
- **Aucun élève classé** : le gel est possible, la photo est vide ; la validation et la publication sont refusées
  (rien à publier) ; la clôture reste gelée.
- **Tous les candidats écartés** : même règle que « moins de trois » ; si plus aucun candidat ne reste, la
  validation est refusée.
- **Égalité à la 3e place qui déborde** : seuls trois lauréats sont publiés, l'égalité étant tranchée par la
  règle ; les autres ex æquo restent dans la photo.
- **Semestre modifié après le gel** : les dates d'un semestre gelé ne se modifient plus (la spec 034 bloque déjà
  les semestres passés ; à vérifier dans le plan).
- **Ligne ajoutée au semestre après sa fin** : une modération tardive crédite le semestre en cours au moment de
  l'approbation (ADR-0004), donc le semestre clos ne bouge pas ; une annulation de la spec 036, elle, vise le
  semestre d'origine : c'est l'écart que signale l'écran.
- **Lauréat suspendu entre la validation et la publication** : la publication est refusée tant que le Top 3
  contient un compte suspendu ; l'admin annule la validation, puis écarte le lauréat ou regèle.
- **Deux admins en même temps** : chaque étape vérifie l'état attendu ; la seconde action reçoit un conflit
  explicite.
- **Notification qui échoue** : la publication est une seule transaction avec les notifications ; rien n'est publié
  à moitié.

## Hors périmètre

- La détection automatique d'anomalies et les alertes de fraude : R22.
- Les distinctions des encadreurs, des clubs et des DRE : plus tard, si les organisateurs les approuvent (Q25).
- Les lots, dotations et le règlement du concours : hors de la plateforme.
- La voie de contestation en ligne : une contestation se fait hors de la plateforme ; l'admin corrige avant la
  publication.
- Le visuel de partage du palmarès : R17.
- Le gel des classements DRE, encadreurs et clubs : seul le classement national des élèves est figé.
- Les photos des lauréats et leur valorisation sur SOS Docteur TV : hors plateforme, sous autorisation.

## Questions ouvertes

Aucune : les quatre questions ont été tranchées le 2026-11-15. La question du club affiché sans choix de l'élève
(spec 036) vaut aussi pour le palmarès ; sa réponse s'appliquera aux deux.
