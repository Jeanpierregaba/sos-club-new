# 027 — Quiz chronométrés et banque de quiz (R9)

## Objectif

Ouvrir les quiz de santé (PRD, « Quiz et certification » : « Un élève ou un encadreur passe un quiz chronométré
par le serveur ; seule la première réussite rapporte des points » et « Aucun encadreur, président ou élève ne
peut créer ni modifier un quiz, même par l'API »). Le serveur arbitre tout : il envoie une question à la fois,
sans sa réponse, mesure le temps et calcule seul le résultat (ADR-0004).

Deux publics :

- l'équipe nationale : le gestionnaire pédagogique prépare les quiz dans l'espace admin, un autre collaborateur
  les publie après validation médicale nommée (Q11, CDC admin § 7) ;
- les joueurs : élèves et encadreurs actifs. L'élève gagne +50 à sa première réussite d'un quiz (barème
  harmonisé, spec 022) ; l'encadreur joue sans points (barème proposé à 0).

Cette spec pose la banque de quiz « jeux libres ». Le parcours de certification Génie Imhotep (12 quiz, badges,
certificat) suit en R11 et réutilisera ce moteur.

## Comportement attendu

**Paramètres du parcours**

1. Le parcours « jeux libres » a des paramètres réglables dans l'espace admin, par un collaborateur qui a le droit
   de publier (ils changent la difficulté, donc les points) : nombre de questions par
   tentative (15 par défaut), temps affiché par question (5 s ; 20 s pour les jeux depuis le 2026-11-10), tolérance réseau (2 s), seuil de réussite
   (12 bonnes réponses) et plafond de tentatives par joueur et par quiz sur une journée (10).
2. Modifier un paramètre crée une nouvelle version ; l'ancienne reste lisible. Une tentative garde la version
   avec laquelle elle a commencé. Le seuil ne peut dépasser le nombre de questions.

**Préparer un quiz (gestionnaire pédagogique, droits `quiz` créer / modifier / soumettre)**

3. Le gestionnaire crée un quiz en brouillon : titre, courte description, axe (un des 7). Il y ajoute une réserve
   de questions : énoncé (300 caractères au plus), 2 à 4 choix, une seule bonne réponse, une explication
   facultative réservée à l'équipe.
4. Il teste le quiz depuis l'espace admin : une partie complète, dans les conditions réelles (chrono, tirage),
   sans rien enregistrer ni créditer.
5. Il soumet le quiz quand sa réserve compte au moins autant de questions que le paramètre en cours (15). Un quiz
   soumis n'est plus modifiable ; le gestionnaire peut le retirer pour le reprendre en brouillon.

**Publier (droits `quiz` approuver / dépublier, double authentification)**

6. Un collaborateur qui a le droit d'approuver voit la file des quiz soumis, lit toutes les questions avec leurs
   bonnes réponses, et :
   - approuve en nommant la personne qui a validé le contenu médical (nom et qualité, obligatoires) : le quiz
     est publié ;
   - ou refuse avec un motif : le quiz revient en brouillon.
     Il ne peut pas approuver un quiz qu'il a lui-même créé, modifié ou soumis.
7. Il peut dépublier un quiz publié avec un motif : le quiz disparaît pour les joueurs ; les tentatives et les
   points acquis restent. Pour le modifier, le gestionnaire le reprend en brouillon, puis le soumet de nouveau.
8. Le gestionnaire est prévenu de chaque décision par une notification (spec 023). Chaque action (création,
   soumission, approbation, refus, dépublication, changement de paramètres) entre au journal d'audit.

**Jouer (élève ou encadreur actif)**

9. Le joueur ouvre « Quiz » (`/quiz`) : la liste des quiz publiés, filtrable par axe, avec pour chacun son état
   pour lui (jamais joué, réussi, meilleur score).
10. Il lance une tentative. Le serveur tire au hasard le nombre de questions du paramètre dans la réserve, mélange
    les choix, et envoie la première question seule, sans sa réponse.
11. Il répond. Le serveur enregistre la réponse si elle arrive dans le temps affiché plus la tolérance (7 s au
    total) après l'envoi de la question ; sinon la question compte comme ratée. Il envoie la question suivante
    sans dire si la précédente était juste.
12. Après la dernière question, le serveur donne le score (ex. 13/15) et la réussite, sans les bonnes réponses.
13. Si un élève réussit un quiz pour la première fois, il gagne +50 (`eleve.quiz`, clé `quiz:<quiz>:<élève>`),
    quel que soit le nombre de ses tentatives. Les reprises restent libres dans le plafond quotidien, sans
    nouveaux points. Les +25 du club (`club.quiz_eleve`) seront crédités avec R13, comme les autres parts Club.
14. La page « Quiz » montre aussi ses résultats (« Mes quiz » : quiz réussis, meilleurs scores), et « Mon espace »
    y mène.

## Critères d'acceptation

- [x] Étant donné un élève, un encadreur ou un président, quand il appelle une route de la banque de quiz
      (création, modification, soumission, approbation, paramètres), alors l'API répond 403, et rien ne change.
- [x] Étant donné un collaborateur sans le droit `quiz` voulu, quand il appelle la route correspondante, alors
      l'API répond 403 ; l'approbation et la dépublication exigent la double authentification.
- [x] Étant donné un quiz dont la réserve compte 14 questions et un paramètre à 15, quand le gestionnaire le
      soumet, alors l'API refuse (422).
- [x] Étant donné une question avec 1 ou 5 choix, ou sans bonne réponse unique, alors l'API la refuse (422).
- [x] Étant donné un quiz soumis, quand on tente de modifier une question, alors l'API refuse (409).
- [x] Étant donné un collaborateur qui a créé, modifié ou soumis un quiz, quand il l'approuve, alors l'API
      refuse (403), même s'il a le droit d'approuver.
- [x] Étant donné une approbation sans nom ou sans qualité du validateur médical, alors l'API refuse (422).
- [x] Étant donné un quiz approuvé, alors il apparaît dans `/quiz` ; un brouillon, un quiz soumis ou dépublié
      n'y apparaît pas et ne se lance pas (404).
- [x] Étant donné une tentative, aucune réponse de l'API au joueur ne contient la bonne réponse ni l'explication
      d'une question avant qu'elle soit tranchée, ni dans la liste des quiz. Depuis le 2026-11-10, un quiz des
      jeux corrige chaque question tranchée et récapitule les erreurs à la fin (amendement de l'ADR-0004).
- [x] Étant donné une question envoyée, quand la réponse arrive 6,9 s plus tard, alors elle compte ; à 7,1 s,
      elle compte comme ratée, quel que soit le choix.
- [x] Étant donné 11 bonnes réponses sur 15, alors la tentative est ratée ; avec 12, elle est réussie.
- [x] Étant donné la même réponse envoyée deux fois, ou deux réponses simultanées à la même question, alors une
      seule est comptée.
- [x] Étant donné un élève actif qui réussit un quiz pour la première fois, alors une seule ligne de +50 est
      écrite au registre ; une deuxième réussite, ou deux fins de tentative simultanées, n'en ajoutent pas.
- [x] Étant donné un encadreur qui réussit un quiz, alors aucune ligne de points n'est écrite.
- [x] Étant donné un joueur qui a atteint le plafond de tentatives du jour sur un quiz, quand il en lance une
      autre, alors l'API répond 429.
- [x] Étant donné une tentative commencée avec la version 1 des paramètres, quand l'admin passe à la version 2,
      alors la tentative se termine avec les règles de la version 1.
- [x] Étant donné un visiteur, un compte en attente ou retiré, ou un collaborateur, quand il lance une tentative
      hors du mode test, alors l'API répond 401 ou 403.
- [x] Étant donné un test lancé par le gestionnaire, alors il n'entre ni dans les résultats, ni dans le plafond, ni au
      registre des points ; la partie de test est effacée à sa fin.
- [x] Étant donné un quiz dépublié, alors les tentatives et les points déjà acquis restent intacts.

## Cas limites et erreurs

- **Coupure réseau** : la question en cours compte comme ratée si son délai expire ; au retour, le joueur reçoit
  la question suivante, chronométrée à partir de son envoi. Une tentative sans activité pendant 10 minutes est
  close : les questions restantes comptent comme ratées, la réussite se calcule sur le score acquis.
- **Nouvelle tentative pendant une autre** : lancer un quiz clôt la tentative en cours sur ce quiz (score
  acquis), pour ne pas cumuler les essais en parallèle.
- **Réponse à une question qui n'est pas la question en cours**, ou à une tentative d'un autre joueur : 404.
  Un choix hors limites : 422.
- **Compte suspendu pendant une tentative** : le joueur n'a plus accès aux quiz ; la tentative reste en cours et
  se clôt s'il revient. Les points ne sont crédités qu'à un élève actif au moment du crédit.
- **Partie abandonnée** : le joueur la retrouve sur la page du quiz (« Reprendre ma partie ») ; sans activité
  depuis 10 minutes, elle est close à la prochaine lecture de la liste des quiz, et une réussite y est créditée.
- **Quiz dépublié pendant une tentative** : la tentative peut se terminer, sans points.
- **Paramètres incohérents** (seuil supérieur au nombre de questions, temps nul, plafond nul) : 422.
- **Question modifiée après avoir été tirée** (essai ou partie d'un quiz repris en brouillon) : elle n'est pas
  réécrite ; elle est désactivée et remplacée par une copie modifiée, à la même place. Les parties en cours et
  l'historique gardent la question jouée.
- **Essai abandonné** : effacé au prochain essai de son auteur, ou au premier essai de quiconque après un jour.
- **Changement de paramètres pendant une publication** : les deux opérations se suivent ; la publication vérifie
  la réserve contre le nombre de questions en vigueur.
- **Réserve réduite après la publication** : impossible, un quiz publié ne se modifie pas ; il faut le
  dépublier.
- **Nombre de questions relevé au-dessus de la réserve d'un quiz publié** : le changement de paramètres est
  refusé (422), avec la liste des quiz à compléter.
- **Contenus de test** : les quiz chargés par `seed_dev` sont marqués « Contenu de test » et ne sont jamais
  chargés en prod (RULES : pas de contenu médical inventé présenté comme réel).
- **Course entre deux collaborateurs** (deux approbations, approbation pendant un retrait) : une seule décision
  passe, l'autre reçoit 409.

## Hors périmètre

- Le parcours Génie Imhotep, les 5 badges et le certificat (R11), les fascicules (R10).
- Les points du club pour un quiz réussi (`club.quiz_eleve`, R13) et les classements.
- Les quiz des visiteurs, avec ou sans compte léger (R19).
- La correction détaillée des questions pour le joueur (ajoutée le 2026-11-10 pour les quiz des jeux : ADR-0004).
- L'import de quiz depuis un fichier, la planification d'une publication, les images dans les questions.
- La détection automatique des anomalies (réponses automatisées, comptes multiples) : les tentatives et
  leurs horaires sont conservés pour la permettre plus tard.
- Les défis inter-clubs (hors scope du PRD).

## Questions ouvertes

Aucune. Décisions prises le 2026-11-08 : publication à deux personnes avec validateur médical nommé ; joueurs
connectés seulement (élèves et encadreurs actifs) ; tirage dans une réserve d'au moins 15 questions ; le joueur
ne voit que son score final. Valeurs par défaut retenues sans question : plafond de 10 tentatives par quiz et
par jour (réglable), seuil à 12/15 (Q12, à confirmer par l'équipe pédagogique avec Q24).
