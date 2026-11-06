# 022 — Harmonisation du barème de gamification

## Objectif

Appliquer partout le document « Harmonisation de la gamification » (référentiel du 2026-11-05, fourni le
2026-11-06) : un seul barème, le même dans l'API, dans l'admin et sur le site. Décisions prises le 2026-11-06
sur ses contradictions : part du club du quiz +25 et de la question du jour +10 (sections 1, 3, 12) ; +50 au club
pour le compte validé d'un élève affilié (remplace Q7) ; rapport d'activité du club +500 « à valider » ; question
du jour : seule la première réponse du jour compte.

## Comportement attendu

**Barème (API, admin).** Les montants deviennent :

| Action | Élève | Club (élève affilié) |
| --- | --- | --- |
| Compte validé | +100 | +50 (affiliation active au moment du crédit) |
| Commentaire approuvé | +5 | +20 |
| Republication vérifiée | +10 | +2 |
| Article personnel publié | +50 | +20 |
| Partage de son article, par réseau | +50 | +2 |
| Quiz santé réussi, première fois | +50 | +25 |
| Bonne réponse à la question du jour | +20 | +10 |
| Badge de certification (5 au plus) | +500 par badge | +200 par badge |
| Certification obtenue | +1 000 | +500 |

Club, actions propres : rapport d'activité +500 (proposé), bilan semestriel +100 (proposé). Le barème encadreur
reste « proposé » ; le quiz réussi par un encadreur passe à 0 (proposé). Un montant déjà modifié par l'admin n'est
pas écrasé.

**Question du jour.** Un élève actif connecté répond une fois par jour : +20 points si la réponse est juste,
0 sinon ; il voit ensuite la correction et le statut « Déjà répondu aujourd'hui » (et « Déjà récompensée » s'il
a gagné), même après rechargement ou reconnexion. Un visiteur ou un autre profil joue toujours, sans points, avec
l'invitation « Connecte-toi à ton compte Élève pour gagner des points ». La bulle affiche le barème : +20 pour toi,
+10 pour ton club.

**Site.** Toutes les mentions de points suivent le barème :

- Jeux : chaque quiz affiche +50 (et +25 pour le club) ; plus aucun barème variable selon le niveau.
- Certification : +50 / +25 par quiz obligatoire (au lieu de +150 et +250), 5 badges à +500 / +200 chacun, bonus
  final +1 000 / +500 ; plus de « 4 paliers ».
- Accueil : le podium devient « Top 3 des lycées » et annonce « Le classement arrive bientôt » sans chiffres.
- Club Santé, inscription : « 5 badges », sans « paliers ».

## Critères d'acceptation

- [ ] Après la migration, le barème contient les montants ci-dessus ; une ligne modifiée par l'admin garde sa
      valeur.
- [ ] Un élève actif qui répond juste à la question du jour gagne +20, une seule ligne de registre.
- [ ] Une deuxième réponse le même jour (juste ou non, même après reconnexion) ne crédite rien et renvoie la
      première réponse avec « déjà répondu ».
- [ ] Une réponse fausse ne crédite rien et bloque les réponses suivantes du jour.
- [ ] Un visiteur, un encadreur ou un collaborateur reçoit la correction sans aucun point.
- [ ] Répondre à une question qui n'est plus celle du jour ne crédite rien.
- [ ] Le site n'affiche plus +150, +250, +25 par quiz, ni de points variables selon le niveau, ni « 4 paliers ».

## Cas limites et erreurs

- Deux réponses simultanées du même élève : la base n'en garde qu'une (contrainte unique), un seul crédit.
- Ligne du barème désactivée ou à 0 : la réponse est enregistrée, sans point.
- Élève sans affiliation : +20 pour lui ; la part du club n'est créditée par personne tant que R13 n'existe pas.

## Hors périmètre

- Écriture des points des clubs : le registre ne sait pas encore créditer un club (R13). Les montants Club sont
  posés dans le barème, aucun n'est crédité.
- Quiz, badges et certification eux-mêmes (R9, R11) : seuls leurs montants et leurs textes changent.
- Jalons de déblocage, noms et visuels définitifs des 5 badges : à valider par l'équipe nationale.

## Questions ouvertes

- Les 5 badges de la page Certification : noms et jalons provisoires (après 3, 5, 7, 9 et 12 quiz), affichés
  « à confirmer », en attendant la décision de l'équipe nationale.
