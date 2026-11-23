# 051 — Suivi d'activité de la plateforme (super-administrateur)

## Objectif

Donner au super-administrateur une vue d'ensemble, chiffrée et à jour, de l'usage de la plateforme : combien de
personnes viennent, d'où elles arrivent, combien commencent une inscription et où elles abandonnent, comment sont
joués les Jeux et la certification. Demande du porteur du projet le 2026-11-23.

La plateforme accueille surtout des **mineurs** (`docs/SECURITY.md`) : la mesure se fait **chez nous**, sans service
tiers, sans profil individuel et sans rien qui permette de suivre une personne d'un jour à l'autre.

## Comportement attendu

**Une nouvelle page « Activité »** dans l'espace admin (`/admin/activite`), visible du seul super-administrateur. En
haut, un choix de période (aujourd'hui, 7 jours, 30 jours, 90 jours, ou deux dates) ; chaque chiffre est comparé à la
période précédente de même durée (« +12 % »). Les dates sont celles de Lomé (UTC+0).

**1. Audience**

- Visiteurs uniques par jour et pages vues, en courbe sur la période.
- Pages les plus vues (chemins regroupés : `/quiz/<id>` compte comme « un quiz »).
- Provenance : accès direct, moteurs de recherche, réseaux sociaux (Facebook, WhatsApp, TikTok, YouTube…), autres
  sites ; et les campagnes marquées d'un `?utm_source=`.
- Appareil (téléphone, tablette, ordinateur) et navigateur, sans version précise.
- Part des visites connectées et anonymes.

**2. Inscription : l'entonnoir et les abandons**

- Clics sur les boutons « S'inscrire » / « Rejoindre », avec l'endroit du site où ils ont été faits (accueil, Jeux,
  certification, menu…).
- Étapes de l'inscription par profil (élève, encadreur, visiteur) : formulaire ouvert → première étape remplie →
  formulaire envoyé → compte créé → e-mail confirmé (visiteur). Le retour des inscrits se lit dans la rétention.
- Taux de passage d'une étape à la suivante, et **abandon** : ouvert sans envoi, envoyé mais refusé (avec la catégorie
  du refus : doublon, saisie invalide, inscriptions fermées, trop d'essais… ; jamais le message, qui peut citer une
  saisie), créé mais jamais confirmé. Un formulaire refusé avant d'atteindre la route (champ mal formé) n'est pas
  compté « envoyé ».

**3. Jeux**

- Parties lancées, terminées, réussies, abandonnées (lancées et jamais finies), par niveau et par quiz.
- Les quiz les plus joués, avec leur taux de réussite et de parties jamais finies (toujours en cours une heure après
  la dernière réponse) ; les questions les plus ratées.
- Joueurs actifs par jour, part des joueurs sans compte (spec 031), vies épuisées (spec 048), défi du jour joué.

**4. Certification**

- Entonnoir des 20 places : combien atteignent chaque place, où l'on décroche le plus.
- Tentatives et taux d'échec par place, temps moyen, badges et certificats délivrés sur la période.

**5. Contenus**

- Lectures et téléchargements de la bibliothèque, par document.
- Articles les plus lus, partages (spec 044).

**6. Régions et clubs** (retenu le 2026-11-23)

- Carte du Togo : par DRE, inscriptions, joueurs actifs, certifiés et clubs sur la période.
- Clubs en service, clubs dormants (aucun de leurs membres n'a joué dans les 30 jours avant la fin de la période).

**7. Rétention et moments d'usage** (retenu le 2026-11-23)

- Part des comptes créés une semaine donnée qui reviennent la semaine suivante, puis après 4 semaines (calculé sur
  les connexions en base ; seule la part s'affiche, jamais la liste des personnes).
- Heatmap jour × heure des pages vues et des parties lancées.

**8. Erreurs et recherches** (retenu le 2026-11-23)

- Pages introuvables (404) les plus demandées, avec leur provenance ; nombre d'erreurs serveur par jour.
- Recherches sans résultat : établissements introuvables à l'inscription, recherches de la carte des clubs. Le mot
  cherché n'est affiché que s'il a été cherché par au moins 3 visiteurs différents le même jour ; sinon il est effacé
  dès le lendemain, pour ne jamais garder un nom de personne tapé une fois.

**Export** : chaque bloc s'exporte en CSV (chiffres agrégés seulement, jamais de ligne par personne).

## Comment on mesure (principes, détaillés dans le plan)

- **Ce qui est déjà en base n'est pas recompté** : comptes, parties, certification, points, publications se lisent
  dans leurs tables (comme le tableau de bord actuel).
- **Ce qui ne laisse pas de trace** (pages vues, clics, abandons de formulaire) est envoyé par le site à notre API,
  sous forme d'**événements anonymes** : un type (`page_vue`, `clic_inscription`, `etape_inscription`…), un chemin,
  une provenance, un appareil, une date. Aucun identifiant de compte, aucun nom, aucune saisie de formulaire.
- **Visiteur unique sans cookie** : une empreinte du jour calculée par l'API à partir de l'adresse IP, du navigateur
  et d'un sel tiré au hasard chaque jour puis détruit, à la manière de Plausible. On peut compter les visiteurs d'une
  journée, jamais reconnaître quelqu'un le lendemain ni retrouver son adresse IP. L'adresse IP n'est stockée nulle
  part, pas même pour limiter le débit (compté en mémoire) ; l'heure d'un événement est arrondie à l'heure, et le sel
  n'entre jamais dans les sauvegardes.
- Pas de bandeau de cookies nécessaire, puisqu'aucun traceur n'est déposé. Un navigateur réglé sur « Ne pas me
  suivre » (`Sec-GPC` / `DNT`) n'est pas compté.
- Le trafic de l'équipe (comptes admin) et des robots n'est pas compté.
- Les événements bruts sont gardés **90 jours**, puis seuls les totaux par jour restent.

## Critères d'acceptation

- [ ] Étant donné un collaborateur national qui n'est pas super-administrateur, quand il ouvre `/admin/activite` ou
      appelle son API, alors il reçoit 403, et le menu ne lui montre pas la page.
- [ ] Étant donné deux pages vues le même jour depuis la même adresse et le même navigateur, alors elles comptent pour
      un visiteur ; le lendemain, la même personne compte pour un nouveau visiteur.
- [ ] Aucune table du suivi ne contient d'adresse IP, d'identifiant de compte, d'e-mail ni de texte saisi (test sur
      le schéma et sur un événement enregistré).
- [ ] Le sel d'un jour passé n'existe plus en base.
- [ ] Une requête avec `Sec-GPC: 1` ou `DNT: 1`, un robot connu ou une session admin n'enregistre rien.
- [ ] Un événement inconnu, trop gros ou mal formé est refusé (422) sans erreur visible pour le visiteur ; l'envoi
      est limité par adresse IP.
- [ ] L'entonnoir d'inscription d'une période donne, pour chaque profil, le nombre à chaque étape et le taux
      d'abandon entre deux étapes.
- [ ] Les chiffres des Jeux et de la certification égalent ceux calculés directement sur `tentative_quiz` et les
      places de la certification.
- [ ] Les événements de plus de 90 jours sont agrégés par jour puis effacés ; les totaux de la période restent
      identiques avant et après.
- [ ] L'export CSV ne contient que des totaux.

## Cas limites et erreurs

- **Période vide** : chaque bloc affiche « Pas encore de données sur cette période », jamais une erreur ni une
  division par zéro.
- **Bloqueur de publicités** : les événements du site peuvent être bloqués ; les chiffres tirés de la base (comptes,
  parties) restent justes. La page l'indique sous la courbe d'audience.
- **Rafale ou faux trafic** : débit limité par adresse (3 000 événements par quart d'heure, large pour les réseaux
  mobiles partagés) et par jour ; au-delà, l'événement est ignoré sans erreur. Les chemins hors du site sont ramenés
  à « autre ».
- **Classe derrière une même adresse IP** : plusieurs élèves sur le même navigateur d'école comptent pour un
  visiteur. Le chiffre est donc un minimum ; la page le dit.
- **Paramètres sensibles dans l'URL** (code de vérification de carte, lien de mot de passe) : le chemin enregistré
  est retiré de ses paramètres, et les chemins de ces pages sont remplacés par leur gabarit.
- **Le site fonctionne sans le suivi** : si l'API du suivi échoue, la navigation n'est jamais bloquée.

## Hors périmètre

- Aucun outil tiers (Google Analytics, Meta Pixel, Hotjar…) et aucun enregistrement de session ou de clics à la
  souris.
- Aucun suivi individuel : on ne peut pas voir « ce qu'a fait l'élève X ». La fiche d'un inscrit (specs 045, 046)
  reste le seul endroit où l'on voit l'activité d'une personne, avec ses droits et son journal.
- Pas d'alertes automatiques ni de rapport envoyé par e-mail dans cette version.
- Pas d'accès aux DRE dans cette version.

## Décisions

- 2026-11-23 : visiteurs comptés sans cookie, par l'empreinte du jour ; événements bruts gardés 90 jours ; idées
  retenues : régions et clubs, rétention et moments d'usage, erreurs et recherches.

## Questions ouvertes

Aucune : prêt pour le plan.

## Idées pour plus tard

- **Étapes « compte vérifié » (encadreur) et « première connexion »**, **demandes de club abandonnées**, **capsules
  les plus vues** et **quiz les plus abandonnés** en tableau à part : écartés de la version du 2026-11-23 (relecture).
- **Campagnes** : liens marqués (`?utm_source=affiche-lome`) avec leur propre tableau, pour mesurer une affiche, une
  émission de SOS Docteur TV ou une publication Facebook. (La provenance par `utm_source` reste comptée dans
  l'audience.)
- **Temps réel** : visiteurs des 5 dernières minutes, pour suivre l'effet d'une émission en direct.
- **Rapport hebdomadaire** par e-mail au super-administrateur, et alertes (chute des inscriptions, pic d'erreurs).
- **Accès des DRE** à leurs propres chiffres.
