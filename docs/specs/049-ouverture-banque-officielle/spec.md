# 049 — Ouverture au public : banque officielle de 1 000 questions, remise à zéro, 3 vies, favicon

## Objectif

Les tests sont finis : la prod ouvre au grand public le 2026-11-24. Avant l'ouverture :

1. **remettre à zéro** les Jeux et la certification : points, étoiles, places, badges et certificats gagnés pendant
   les tests ;
2. **remplacer les quiz** par la banque officielle « Banque de 1 000 questions – Quiz santé des Clubs Santé »
   (document Word du 2026-11-23) ;
3. passer à **3 vies par jour** au lieu de 7 ;
4. changer le **favicon** par le logo « CLUB SANTÉ ».

Sources : [spec 034](../034-gamification-eleve-4-niveaux/spec.md) (Jeux), [spec 029](../029-certification/spec.md)
et [spec 043](../043-banque-1000-et-certification-expert/spec.md) (certification),
[spec 048](../048-vies-et-chrono-15s/spec.md) (vies), [ADR-0004](../../decisions/) (registre des points),
[RULES](../../RULES.md).

## Comportement attendu

### 1. La banque officielle

Le document a 4 parties. Chaque question a 3 propositions, la bonne réponse est en gras, et chaque partie sépare les
questions « moyennement difficiles » (M) des « très difficiles » (D).

| Partie                                  | M   | D   | Axe                    |
| --------------------------------------- | --- | --- | ---------------------- |
| 1 — Santé publique (1 à 300)            | 180 | 120 | Sport et secourisme    |
| 2 — Santé sexuelle et reproductive      | 150 | 100 | Santé sexuelle (EVSS)  |
| 3 — Journées mondiales de la santé      | 120 | 80  | Santé et environnement |
| 4 — EVSS (751 à 1000)                   | 150 | 100 | Santé sexuelle (EVSS)  |

- **200 questions D sont réservées à la certification** (50 par partie, prises à intervalles réguliers dans
  l'ordre du document) : elles ne sont jamais posées dans les Jeux.
- Les **800 autres** forment **80 quiz Jeux de 10 questions**. Un quiz ne mêle ni deux parties ni deux
  difficultés.
- Les questions n'ont pas d'explication : le document n'en donne pas.

### 2. Les 80 quiz Jeux

- 60 quiz M et 20 quiz D, répartis en 4 niveaux dans la proportion d'aujourd'hui (4/3/2/1) :
  **32 Débutant, 24 Intermédiaire, 16 Avancé, 8 Expert**. Les quiz M remplissent Débutant, Intermédiaire et
  4 Avancé ; les quiz D remplissent les 12 autres Avancé et les 8 Expert. Les parties sont alternées dans chaque
  niveau.
- Titre : « <Partie> — quiz <k> » (par exemple « Santé publique — quiz 3 »), numéro 1 à 80 dans le parcours.
- Un quiz pose ses 10 questions dans un ordre tiré au hasard, avec 15 secondes par question (spec 048).
- Les gains par niveau et les étoiles ne changent pas. Une étoile s'obtient en réussissant tous les quiz du niveau.
- Les quiz sont publiés au nom d'AIMES-AFRIQUE, comme aujourd'hui.

### 3. Les 20 quiz de certification

| Places  | Badge                               | Questions D de la partie       |
| ------- | ----------------------------------- | ------------------------------ |
| 1 à 4   | Ambassadeur Santé Junior            | 1 — Santé publique             |
| 5 à 8   | Pair Éducateur Santé et Citoyenneté | 2 — Santé sexuelle et reprod.  |
| 9 à 12  | Sentinelle de la Prévention         | 3 — Journées mondiales         |
| 13 à 16 | Champion de la Santé et EVSS        | 4 — EVSS                       |
| 17 à 20 | Maître Génie Imhotep                | mélange : 10 de chaque partie  |

- 10 questions par quiz, toutes différentes ; les règles du parcours ne changent pas (10/10, arrêt à la première
  erreur, places dans l'ordre, +50 par place, +500 par badge, +1 000 pour le certificat).

### 4. Les anciens quiz

- Tous les quiz Jeux et de certification d'aujourd'hui (100 défis, réserves des lots 1 à 7, 20 quiz de
  certification) passent à **dépublié**, avec un motif. Rien n'est supprimé : les parties jouées restent dans
  l'historique et les fiches des inscrits.
- Les quiz de la page d'accueil et le défi du jour ne changent pas.

### 5. La remise à zéro

- Pour les **élèves et les encadreurs** : chaque gain des Jeux (quiz, étoiles) et de la certification (places,
  badges, certificat) est **annulé au registre** par une ligne négative avec le motif « Remise à zéro avant
  l'ouverture au public ». L'annulation retire aussi la part du club (50 %).
- Les points de la **vie du club** (actions de terrain, articles, bienvenue, corrections de l'équipe…) ne
  changent pas.
- Les **étoiles, places réussies et badges** sont déplacés dans des tables d'archive, avec la date de la remise à
  zéro : ils disparaissent des profils et du suivi, et l'historique est gardé.
- Les **certificats** valides passent à « révoqué » avec le même motif. La vérification publique d'un ancien numéro
  répond « révoqué ».
- Après la remise à zéro, chacun peut regagner normalement quiz, étoiles, places, badges et certificat.
- Les clôtures de semestre et les classements annuels déjà publiés ne changent pas.

### 6. Les vies

- **3 vies par jour**, communes aux Jeux et à la certification. Le reste de la règle (spec 048) ne change pas.
  Tous les textes du site qui parlent de 7 vies parlent de 3.

### 7. Le favicon

- Le logo « CLUB SANTÉ » (bleu et rouge), détouré de la capture fournie et centré sur un carré blanc, en
  `favicon.ico` (16, 32, 48 px) et en icône Apple (180 px).

## Critères d'acceptation

- [ ] L'outil de lecture du document en tire 1 000 questions de 3 propositions, une seule en gras chacune, rangées
      par partie et difficulté (180/120, 150/100, 120/80, 150/100) ; un document ambigu est refusé.
- [ ] Le fichier de données compte 80 quiz Jeux de 10 questions (32/24/16/8 par niveau) et 20 quiz de
      certification de 10 questions ; les 1 000 énoncés sont tous utilisés, une seule fois.
- [ ] Aucun quiz Jeux ne contient une question de la certification.
- [ ] Les places 1 à 16 ont des questions D de leur partie ; les places 17 à 20 en ont 10 de chaque partie.
- [ ] Après la migration, seuls les 80 nouveaux quiz Jeux et les 20 nouveaux quiz de certification sont publiés ;
      les anciens sont dépubliés, aucun quiz ni partie n'est supprimé.
- [ ] Après la migration, chaque élève et chaque encadreur a 0 point Jeux et 0 point de certification, et aucun
      club n'a de point venu des quiz ; les points de la vie du club ne changent pas.
- [ ] Les étoiles, places et badges sont dans les tables d'archive, plus dans les tables en service ; les
      certificats sont révoqués avec le motif.
- [ ] Après la remise à zéro, un élève réussit la place 1 et gagne +50, gagne un badge et une étoile comme
      avant (les anciennes clés d'idempotence ne bloquent pas).
- [ ] Relancer la migration ne change rien ; une base sans quiz (celle des tests) passe la migration sans erreur.
- [ ] Un joueur a 3 vies par jour ; la 4e partie du jour est refusée.
- [ ] Le site montre 3 vies, et le favicon est le logo.

## Cas limites et erreurs

- **Partie en cours pendant la migration** : elle se termine normalement sur l'ancien quiz dépublié, sans points
  (le quiz n'est plus publié), ou elle est close comme abandonnée.
- **Gain déjà annulé** avant la remise à zéro : il n'est pas annulé une seconde fois.
- **Correction de l'équipe** (spec 036) sur des points de quiz : elle reste, elle n'est pas un gain des Jeux.
- **Certificat déjà révoqué ou remplacé** : il reste tel quel.
- **Élève suspendu ou ancien élève** : ses gains sont annulés comme les autres.
- **Base de préprod** : la même migration la remet à zéro au déploiement de `develop`.

## Hors périmètre

- Les explications des questions (absentes du document).
- Un nouveau barème ou de nouveaux noms de badges.
- Le défi du jour et les quiz sans compte de la page d'accueil.
- Un fichier de logo vectoriel : le favicon vient de la capture ; un fichier propre pourra le remplacer.

## Questions ouvertes

Aucune. Décisions du 2026-11-23 : remise à zéro des élèves, des encadreurs et des parts de club ; quiz Jeux de
10 questions par partie ; questions de certification réservées ; logo entier sur fond blanc.
