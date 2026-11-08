# 025 — Commentaires prémodérés (R7)

## Objectif

Permettre aux membres connectés de réagir à un article publié (PRD, Q13 : « oui, après modération, +5 points »),
sans que rien ne s'affiche avant qu'un modérateur l'ait approuvé (`docs/RULES.md`). Les commentaires passent par
le moteur de modération de la spec 023 (ADR-0009), comme les articles : même file, mêmes décisions, mêmes
notifications. Le barème de la spec 022 fixe les points : +5 pour l'auteur, +20 pour son club s'il est élève
(enregistré pour R13), dans la limite de 5 commentaires rémunérés par jour et par personne (Q22).

## Comportement attendu

**Écrire un commentaire**

1. Sous un article publié, un élève ou un encadreur actif connecté voit un champ « Ton commentaire ». Un
   visiteur non connecté voit les commentaires publiés et une invitation à se connecter.
2. Il écrit un texte simple (1 à 1 000 caractères, sans HTML ni lien cliquable) et l'envoie. Un élève choisit, comme pour un article, d'afficher ou non son club (affiché par défaut). Le site confirme :
   « Merci ! Ton commentaire sera visible après sa validation. » Le commentaire apparaît pour lui seul, marqué
   « En attente ».
3. Un commentaire envoyé ne se modifie plus. Son auteur peut le retirer à tout moment, en attente ou publié :
   il disparaît du public ; les points déjà acquis restent.

**Modérer**

4. Le commentaire arrive dans le centre de modération (spec 023) avec le titre de l'article, le texte et la
   signature de l'auteur. Le périmètre est le même que pour les articles : national ou DRE de l'établissement de
   l'auteur.
5. Le modérateur l'approuve, le refuse (motif obligatoire) ou dépublie un commentaire publié (motif obligatoire).
   Il n'y a pas de « à corriger » : un commentaire est court, l'auteur en écrit un autre.
6. L'auteur reçoit une notification du résultat, avec le motif en cas de refus ou de dépublication. À la première
   publication, l'auteur de l'article reçoit « Nouveau commentaire sur ton article » (pas pour son propre
   commentaire).

**Lire**

7. Sous l'article, les commentaires publiés s'affichent du plus ancien au plus récent, avec la signature (un
   élève par son pseudonyme et son club, un encadreur par son prénom, l'initiale de son nom et sa fonction, comme
   les articles) et la date de publication.
8. « Mes commentaires » (espace connecté) liste les commentaires de l'auteur, leur état, l'article concerné et le
   motif d'un refus.

**Points**

9. À la première approbation, l'auteur reçoit les points du barème (`eleve.commentaire` ou
   `encadreur.commentaire`), une seule fois par commentaire, si moins de 5 de ses commentaires envoyés le même
   jour ont déjà été rémunérés. Au-delà, le commentaire est publié sans points. Le club bénéficiaire d'un élève
   est enregistré pour R13.

## Critères d'acceptation

- [ ] Étant donné un article publié, quand un élève ou un encadreur actif envoie un commentaire valide, alors il
      est enregistré « en attente », absent de la liste publique, visible par son auteur, et il entre dans la
      file de modération.
- [ ] Étant donné un visiteur non connecté, un compte non actif, un article non publié (brouillon, en attente,
      refusé, dépublié) ou inexistant, quand on envoie un commentaire, alors l'API refuse (401, 403 ou 404) et rien
      n'est enregistré.
- [ ] Étant donné un texte vide, de plus de 1 000 caractères ou composé seulement d'espaces, alors l'API répond 422. Un texte contenant du HTML ou un lien est affiché tel quel, jamais interprété.
- [ ] Étant donné un commentaire en attente, refusé, retiré ou dépublié, alors il n'apparaît pas dans les
      commentaires publics de l'article ; son texte n'est lisible que par son auteur et les modérateurs habilités
      de son périmètre.
- [ ] Étant donné un commentaire approuvé, alors il apparaît sous l'article avec la signature attendue, sans nom
      complet ni contact d'élève.
- [ ] Étant donné un article dépublié, alors ses commentaires ne sont plus lisibles publiquement.
- [ ] Étant donné un commentaire, quand il est approuvé, refusé ou dépublié, alors son auteur reçoit une
      notification, et un motif est exigé pour le refus et la dépublication.
- [ ] Étant donné la première publication d'un commentaire d'un autre que l'auteur de l'article, alors l'auteur
      de l'article reçoit une notification ; une republication n'en envoie pas de nouvelle.
- [ ] Étant donné un modérateur auteur du commentaire ou hors du périmètre DRE, alors il ne peut pas décider.
- [ ] Étant donné la première approbation d'un commentaire, alors l'auteur reçoit +5 une seule fois (clé
      `commentaire:<id>`), et la ligne reste après une dépublication (un commentaire dépublié ne revient pas en file) ; le club d'un élève affilié
      est enregistré.
- [ ] Étant donné 5 commentaires d'un même auteur envoyés le même jour et déjà rémunérés, quand un sixième envoyé
      ce jour-là est approuvé, alors il est publié sans points.
- [ ] Étant donné plus de 20 commentaires envoyés par une personne dans la journée, alors l'API répond 429 avec un
      message clair.
- [ ] Étant donné un commentaire de son auteur, quand il le retire, alors il disparaît du public et de la file ;
      un autre compte ne peut pas le retirer.
- [ ] Le site affiche le champ, la confirmation, la liste publique, « Mes commentaires » et la file de
      modération, lisibles sur téléphone.

## Cas limites et erreurs

- **Article dépublié pendant l'attente** : le commentaire reste en file ; s'il est approuvé, il ne s'affiche
  qu'avec l'article republié.
- **Deux modérateurs simultanés** : le verrou et la version du moteur donnent un 409 au second.
- **Retrait pendant la décision** : même verrou ; le retrait ou la décision arrive en second et reçoit un 409.
- **Double clic sur « Envoyer »** : le bouton est désactivé pendant l'envoi ; deux textes identiques envoyés par
  la même personne sur le même article en moins d'une minute ne font qu'un commentaire.
- **Compte désactivé après l'envoi** : le commentaire reste en file ; publié, il garde sa signature.
- **Élève sans club** : il commente ; aucun club bénéficiaire n'est enregistré.
- **Caractères spéciaux et emojis** : acceptés ; les retours à la ligne sont gardés, au plus deux d'affilée.

## Hors périmètre

- Réponses à un commentaire, mentions, « j'aime ».
- Commentaires des visiteurs (R19) et sur d'autres contenus que les articles (actualités du club en R8).
- Signalement d'un commentaire par les lecteurs.
- Crédit des points du club (R13 : seul le club bénéficiaire est enregistré).
- Commentaires de l'équipe nationale.

## Questions ouvertes

Tranchées le 2026-11-08 :

1. Élèves et encadreurs actifs seulement ; les visiteurs viendront avec R19.
2. Liste à plat, sans réponse.
3. Au-delà de 5 commentaires rémunérés par jour : publiés sans points ; plafond dur de 20 envois par jour.
4. L'auteur de l'article est notifié à la première publication d'un commentaire.
