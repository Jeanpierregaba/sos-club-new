# 0013 — Classements publics DRE et national, et correction motivée des points

- **Statut** : Accepté
- **Date** : 2026-11-14
- **Complète** : ADR-0004 (registre des points), ADR-0011 (clubs en service), ADR-0012 (part du club)
- **Décidé avec** : spec 036 (R13)

## Contexte

R13 doit rendre les points lisibles : la place d'un élève, d'un encadreur et d'un club dans son club, sa DRE et le
pays, pour le semestre en cours et depuis le début. La plateforme accueille des mineurs : la Q20 et `docs/RULES.md`
interdisent de publier le nom complet, les coordonnées ou la liste des membres d'un club. Le registre des points est
immuable (ADR-0004) : une erreur doit pouvoir être corrigée sans réécrire l'historique.

## Options envisagées

1. **Classements publics au niveau du club, de la DRE et du national**, comme le PRD initial. Un classement de club
   public révèle indirectement ses membres et leurs points ; la Q20 réserve la liste des membres au club et à
   l'équipe.
2. **Table de classement matérialisée** : rapide, mais duplique le registre, pose la question de sa fraîcheur et
   anticipe le gel de R14.
3. **Calcul à la demande depuis `mouvement_points`** : un score reste une somme (ADR-0004), les index servent les
   périodes ; une vue matérialisée reste possible plus tard sans changer le registre.
4. **Correction par modification ou suppression d'une ligne** : contraire à l'immuabilité du registre.
5. **Correction par une nouvelle ligne motivée** : traçable, réversible par une annulation, sans toucher au passé.

## Décision

- Les classements **publics** couvrent les élèves, les encadreurs et les clubs aux niveaux **DRE** et **national**,
  pour le **semestre en cours** et le **total historique**. Le niveau **club** reste privé.
- Un élève apparaît par son **pseudonyme** et, s'il en a un, son **club** ; un encadreur par son **prénom** et
  l'**initiale de son nom**, comme les signatures d'articles ; un club par son **nom** et son **établissement**.
  Aucune charge publique ne porte de nom complet, d'e-mail, de téléphone ni d'identifiant utilisateur.
- Les classements sont **calculés à la demande**, sans table dédiée. R14 figera les palmarès de fin de semestre.
- Un club n'apparaît que s'il est **en service** (ADR-0011). Son score est la somme de ses `demi_points_club`
  divisée par 2, affichée avec sa décimale. Un élève ou un club dont le total est exactement zéro n'est pas classé ;
  un total négatif reste possible après correction et s'affiche en bas du classement.
- Le **classement interne** d'un club est lisible par ses **membres affiliés actifs**, ses **encadreurs rattachés
  actifs**, son **président** et l'**admin**. Pour un élève, il additionne les gains **crédités à ce club**
  (`mouvement_points.club_id`) : un changement de club ne transfère donc pas les points de l'ancien. Pour un
  encadreur, il additionne ses gains personnels pendant son rattachement actif.
- Une **correction** est une nouvelle ligne `admin.correction`, avec un **motif** de 10 à 500 caractères, un montant
  **non nul** borné à ±10 000, le semestre et l'année en cours, et **aucune part de club**. Pour retirer une part de
  club, l'admin annule la ligne d'origine, qui la porte.
- Une **annulation** admin écrit une ligne liée (`annule_id`) qui copie le montant, le club, la part de club et le
  **semestre d'origine** : le classement du semestre visé est corrigé, pas celui du semestre où l'annulation est
  saisie. Une ligne d'annulation ne s'annule pas.
- Le **registre** et les **corrections** sont **nationaux** et exigent la **double authentification**
  (`points:consulter` devient un droit sensible, `points:modifier` l'était déjà).
- L'**idempotence** de la correction utilise la clé `correction:<uuid>` fournie par le site : une seconde requête
  renvoie la ligne existante, jamais un doublon.

## Conséquences

- `points:consulter` devient sensible : un collaborateur qui n'a que ce droit doit activer la double authentification
  pour lire les semestres, le barème, les années et les classements. C'est le prix du registre nominatif.
- La contrainte `montant_signe` autorise désormais une annulation positive (celle d'une correction négative) et une
  correction négative motivée. Les gains ordinaires restent strictement positifs.
- La ligne technique `admin.correction` est masquée du barème et refusée à la modification : elle ne peut jamais
  devenir un gain automatique.
- Un total historique peut devenir négatif ; l'espace du bénéficiaire et le registre l'affichent, le classement
  public le place en bas.
- Les classements ne montrent que les totaux non nuls : un compte sans point ou entièrement corrigé n'est pas classé.
- Le retour de la migration refuse de s'exécuter si des motifs ou des corrections existent : ces données
  n'existaient pas avant R13 et ne peuvent pas être représentées par l'ancien schéma.
