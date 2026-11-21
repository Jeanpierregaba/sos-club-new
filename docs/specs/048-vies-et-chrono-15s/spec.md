# 048 — Vies quotidiennes et chrono de 15 secondes

## Objectif

Rendre les quiz plus exigeants et inciter à la régularité : chaque joueur dispose de **7 vies par jour**, communes aux
quiz des jeux et à la certification, et le temps pour répondre passe de **20 à 15 secondes** par question, dans les
deux parcours. Décisions du 2026-11-21 :

- les 7 vies se comptent sur la journée, tous quiz confondus ;
- une seule réserve pour les jeux et la certification ;
- seule une partie **ratée** (ou abandonnée sans réussite) retire une vie : réussir ne coûte rien ;
- 15 s par question dans les jeux et dans la certification.

## Comportement attendu

- Le joueur voit ses vies (7 cœurs) sur la page des jeux, sur la page de la certification et à la fin de chaque
  partie : « Il te reste 5 vies aujourd'hui ».
- Lancer un quiz est possible tant qu'il reste au moins une vie. Une partie en cours **réserve** une vie : avec une
  seule vie, on ne peut pas lancer deux quiz en même temps.
- À la fin d'une partie ratée, une vie est perdue ; une partie réussie la rend.
- À 0 vie, le bouton de lancement est désactivé : « Tu as utilisé tes 7 vies aujourd'hui. Reviens demain, elles se
  rechargent à minuit. » L'API refuse aussi le lancement (le site ne fait que l'annoncer).
- Les vies se rechargent à minuit, heure de Lomé (UTC+0), comme le plafond actuel.
- Chaque question laisse 15 s (plus la tolérance réseau de 2 s, inchangée) ; le chrono affiché suit.

## Critères d'acceptation

- [ ] Un joueur qui a raté 7 parties aujourd'hui (jeux et certification confondus) ne peut plus lancer de quiz ;
      l'API répond 409 avec un message clair.
- [ ] Une partie réussie ne retire aucune vie.
- [ ] Une partie abandonnée et close sans réussite retire une vie.
- [ ] Avec 1 vie, une partie en cours empêche d'en lancer une seconde.
- [ ] Le lendemain, le joueur a de nouveau 7 vies.
- [ ] Les parties d'essai de l'équipe ne comptent pas.
- [ ] Les nouvelles parties ont 15 s par question, dans les jeux et la certification ; une partie commencée avant
      garde son temps.
- [ ] Le site affiche les vies restantes et bloque le lancement à 0.

## Cas limites et erreurs

- Deux lancements simultanés : sérialisés par le verrou du joueur déjà en place ; un seul passe s'il ne reste
  qu'une vie.
- Partie lancée avant minuit et ratée après : elle compte pour le jour de son lancement.
- Le plafond par quiz réglable dans l'admin (parties par quiz et par jour) reste en place et s'ajoute aux vies.

## Hors périmètre

- Racheter ou gagner des vies (bonus, publicité) : non.
- Invités sans compte : ils gardent leur limite actuelle de 3 quiz au total (spec 031).
- Modifier le nombre de vies depuis l'admin : 7 est fixé dans le code (voir le plan).

## Questions ouvertes

Aucune.
