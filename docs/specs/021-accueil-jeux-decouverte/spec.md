# 021 — Accueil : « Quel axe est fait pour toi ? », défi du jour et podium des clubs

## Objectif

Rendre l'accueil plus vivant avec trois blocs de gamification légère, qui ne rapportent aucun point :

- le jeu de découverte « Quel axe est fait pour toi ? », réservé aux élèves connectés (document fonctionnel
  « Jeu de découverte des 7 axes », fourni le 2026-11-06) ;
- un défi du jour qui change chaque jour, tiré d'une banque de questions en base ;
- un podium des trois clubs qui ont le plus de points, avec un lien vers la page des jeux.

## Comportement attendu

**Quel axe est fait pour toi ?** La section de l'accueil, refaite d'après la maquette (fond clair lilas,
caméléon, titre violet et orange, bulles « Plutôt créatif ? », « Passionné de sport ? »…), reste visible de
tous. « Commencer le test » :

- A. élève actif connecté : la question 1 sur 5 s'ouvre ;
- B. visiteur non connecté : « Connecte-toi à ton compte Élève pour découvrir ton axe ! », avec « Se connecter »
  et « Créer mon compte Élève » ; après la connexion, l'élève revient sur l'accueil et le test s'ouvre ;
- C. autre profil connecté (encadreur, collaborateur) : « Ce jeu est réservé aux élèves inscrits. »

Une question par écran, quatre cartes de réponse, Précédent et Suivant, progression de 1 à 5 ; une réponse
est exigée pour avancer et on peut revenir la changer. Après la 5e, l'API calcule le résultat (table de
correspondance du document : +3 à l'axe principal de la réponse, +1 à l'axe secondaire ; départage : nombre de
fois en axe principal, puis axe principal de la question 1 s'il est ex æquo, puis l'ordre GI, EVSS, TV, SS, GB,
LM, SE). L'écran de résultat montre « Ton axe principal » (couleur, mascotte, titre, texte, « Ta force »),
« Deux autres axes à explorer », et les boutons « Découvrir cet axe », « Partager mon résultat » et « Refaire
le test ». Le texte ne présente jamais le résultat comme un diagnostic. Le mot « univers » n'apparaît pas.

**Défi du jour.** La bulle flottante de l'accueil montre la question du jour : la même pour tous, elle change
à minuit (heure de Lomé). Le visiteur choisit une réponse et la valide ; l'API dit si elle est juste, donne la
bonne réponse et une courte explication. Aucun point, aucun compte nécessaire.

**Podium des clubs.** Après « Trouve toi aussi ton club Santé », une section sombre d'après la maquette
(mascottes bleue et violette, « Et si ton lycée devenait N°1 du Togo ? », deux pastilles « Des quiz santé » et
« Un classement national », bouton « Découvrir les jeux ») montre les trois clubs actifs qui ont le plus de
points, avec leur établissement et leurs points. Tant qu'aucun club n'a de points, elle affiche « Le classement
démarre bientôt » à la place du podium.

## Critères d'acceptation

- [ ] Étant donné un élève actif connecté, quand il demande les questions, alors il reçoit les 5 questions et
      leurs 4 réponses, sans les axes associés.
- [ ] Étant donné un visiteur, un encadreur ou un collaborateur, quand il demande les questions ou un résultat,
      alors l'API répond 401 (non connecté) ou 403 (autre profil, ou élève non actif).
- [ ] Étant donné les réponses [A, A, A, D, B], quand l'élève demande le résultat, alors il obtient TV (11 points),
      puis EVSS (6) et LM (2), identique pour tous.
- [ ] Les 20 réponses de la table sont couvertes par un test, ainsi que chaque règle de départage.
- [ ] Une liste de réponses incomplète ou invalide est refusée (422).
- [ ] Le site affiche les cas A, B et C ; après la connexion (cas B), le test s'ouvre.
- [ ] Le défi du jour est le même pour deux visiteurs le même jour, et change le lendemain.
- [ ] La question du défi arrive sans sa bonne réponse ; la correction vient d'une seconde requête.
- [ ] Une question désactivée n'est plus jamais tirée.
- [ ] Le podium ne montre que des clubs actifs, au plus trois, triés par points ; sans points, l'état vide.
- [ ] Aucune de ces actions n'écrit de ligne dans `mouvement_points`.

## Cas limites et erreurs

- Banque de défis vide : la bulle ne s'affiche pas (l'API répond 404).
- Réponse à un défi qui n'est plus celui du jour (minuit passé) : la correction est donnée quand même pour
  cette question, sans erreur.
- Choix hors des options : 422.
- Session expirée pendant le test : le résultat répond 401 ; le site affiche le cas B.
- API indisponible : la section reste affichée, le bouton montre un message d'indisponibilité ; la bulle du
  défi et le podium ne s'affichent pas (ou l'état vide), sans casser la page.
- Égalité parfaite entre plusieurs axes : départage déterministe du document.

## Hors périmètre

- Écran admin de la banque de défis (ajout, modification, désactivation) : à faire avec les quiz (R9). La
  banque est remplie par une seed et se gère en base d'ici là.
- Calcul des points des clubs : le registre ne sait pas encore créditer un club (R13). La route du podium est
  prête et lit le score depuis un seul point d'entrée, que R13 branchera.
- Image partageable du résultat (carte verticale) : le partage passe par le partage natif du téléphone
  (ou la copie du lien) ; l'image sera faite plus tard.
- Enregistrement des réponses ou des résultats du jeu : rien n'est conservé.

## Questions ouvertes

- Les noms des axes du document (« Gamification & Bourses », « Leadership & Masculinité positive »…) diffèrent
  de ceux du site (« Bourses & excellence », « Leadership & mentorat »…). Le résultat du jeu reprend ceux du
  document ; faut-il aligner tout le site sur eux ?
- Les 30 questions de la seed du défi sont rédigées par l'agent à partir de connaissances de santé publique
  courantes : l'équipe nationale doit les relire avant la prod.
