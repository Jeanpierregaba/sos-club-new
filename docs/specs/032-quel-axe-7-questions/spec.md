# 032 — « Quel axe est fait pour toi ? » : 7 questions, 3 participations

Source : `Cahier_des_charges_Quel_Axe_7_Questions_3_Parties.docx` (porteur du projet, 2026-11-10). Fait évoluer
la [spec 021](../021-accueil-jeux-decouverte/spec.md), qui ne gardait rien en mémoire.

## Objectif

Le mini-jeu de découverte des 7 axes passe de 5 à 7 questions. Chaque élève a **3 participations sur toute la
vie de son compte**. Ses parties sont gardées par l'API : il peut reprendre une partie interrompue, revoir et
partager ses trois résultats. Le jeu reste sans enjeu : pas de bonne réponse, pas de diagnostic, pas
d'affectation, jamais de point, de badge ni de certificat.

## Comportement attendu

1. **Accueil, pour tous.** La carte montre l'accroche « 7 axes. Des talents à révéler. Et toi, où vas-tu
   briller ? », l'introduction « …Réponds à sept questions… », le bouton « Commencer le jeu » et les mentions
   « Réservé aux élèves inscrits » et « 3 participations maximum ».
2. **Visiteur sans compte.** « Connecte-toi à ton compte Élève », avec la connexion et la création du compte. Après
   la connexion, il revient au jeu (comme en 021).
3. **Autre profil** (encadreur, admin, visiteur inscrit). Il voit la présentation mais pas le questionnaire, avec un
   message « réservé aux élèves ».
4. **Élève connecté.** Il voit « Participations utilisées : X/3 » et « Participations restantes : Y », puis l'un de
   ces boutons :
   - « Commencer » s'il lui reste une participation et qu'aucune partie n'est en cours ;
   - « Reprendre la partie » si une partie est en cours.
5. **Démarrage.** La partie n'est décomptée que quand l'élève confirme « Commencer » et que l'API crée la partie
   (1/3, 2/3, 3/3). Regarder la page ne coûte rien.
6. **Questionnaire.**
   - Une question par écran, avec 4 cartes cliquables et « Question X sur 7 ».
   - On navigue avec Précédent et Suivant.
   - Chaque réponse est enregistrée par l'API dès qu'elle est choisie, et l'élève peut la changer tant que la
     partie n'est pas terminée.
   - S'il quitte la page, se déconnecte ou change d'appareil, il reprend la même partie au même endroit.
7. **Résultat.** Il apparaît une fois la 7e réponse validée et comprend :
   - l'axe principal, avec sa mascotte et sa couleur officielles, son titre, son explication et « Ta force » ;
   - 2 axes complémentaires ;
   - les boutons « Découvrir cet axe » et « Partager mon résultat » ;
   - « Rejouer (Y partie(s) restante(s)) » seulement s'il reste une participation.
8. **Après la 3e partie terminée.** Le message « Tu as utilisé tes 3 participations ! Tu peux revoir tes
   résultats et découvrir les 7 axes des Clubs Santé. » s'affiche. Il n'y a plus de « Rejouer » ; il reste « Voir
   mes résultats » et « Découvrir les axes ».
9. **Historique.** Dans le jeu et dans « Mon espace », l'élève voit ses parties terminées, chacune avec sa date,
   son axe principal et ses deux axes complémentaires, ainsi que le compteur X/3. Il peut revoir et partager
   chaque résultat.
10. **Partage.** Le texte et la carte ne contiennent ni nom, ni pseudonyme, ni téléphone, ni e-mail. Partager ne
    consomme pas de participation et ne rapporte rien.
11. **Information.** Une ligne explique que les réponses et les résultats sont gardés pour l'historique et le
    compteur, et qu'ils sont effacés avec le compte.

## Critères d'acceptation

- [ ] Le questionnaire de l'API a 7 questions de 4 réponses, conformes au cahier des charges (textes, ordre et
      barème +3 / +1 des 28 réponses). Chaque axe est axe principal exactement 4 fois.
- [ ] Le calcul se fait sur 7 réponses avec le départage suivant : total, puis nombre de fois en axe principal,
      puis axe principal de la question 1 s'il est ex æquo, puis l'ordre GI, EVSS, TV, SS, GB, LM, SE. Des cas
      d'égalité sont testés.
- [ ] Étant donné un élève actif sans partie, quand il commence, alors l'API crée la partie n° 1 et répond
      « 1 utilisée, 2 restantes ».
- [ ] Étant donné une partie en cours, quand l'élève demande à commencer, alors l'API renvoie cette partie
      sans en créer une autre.
- [ ] Étant donné une partie interrompue après la question 3, quand l'élève revient (même sur un autre appareil),
      alors il retrouve ses 3 réponses et le compteur n'a pas changé.
- [ ] Quand l'élève change une réponse avant la fin, le résultat est calculé avec la nouvelle réponse.
- [ ] Une partie ne se termine qu'avec 7 réponses (400 sinon). Une partie terminée ne peut plus être modifiée (409).
- [ ] Une partie terminée ne crée aucun mouvement de points, aucun badge et aucun certificat.
- [ ] Après 3 parties commencées, une 4e est refusée par l'API (403), même par appel direct. Les résultats
      restent lisibles et la 3e partie en cours peut toujours être terminée.
- [ ] Deux démarrages simultanés pour le même élève ne créent ni partie n° 4 ni doublon ni deuxième partie en
      cours.
- [ ] Toutes les routes refusent : un compte non connecté ou non actif (401, sa session ne vaut plus) ; un autre
      profil qu'élève (403) ; la partie d'un autre élève ou inexistante (404).
- [ ] L'identifiant de l'élève vient toujours de la session, jamais de la requête.
- [ ] Le site n'affiche plus « 5 » ni « cinq questions » pour ce jeu. « Refaire le test » est remplacé par
      « Rejouer (Y partie(s) restante(s)) », qui disparaît après la 3e partie.
- [ ] « Mon espace » d'un élève montre le compteur et l'historique.
- [ ] Les parties d'un élève sont effacées avec son compte.

## Cas limites et erreurs

- **Double clic, deux onglets ou deux appareils au même instant.** Le démarrage verrouille le compte et la base
  refuse un doublon (numéro unique par élève, une seule partie en cours). Le deuxième appel reçoit la partie
  déjà créée, ou un refus s'il n'en reste plus.
- **Réponse invalide** (lettre hors A–D, numéro de question hors 1–7). La requête est refusée avec un 422.
- **Partie terminée.** Une réponse envoyée après la fin est refusée avec un 409.
- **Élève suspendu en cours de partie.** Sa session ne vaut plus : toutes les routes répondent 401 et la partie
  reste en l'état.
- **Rechargement, déconnexion, effacement des cookies.** Rien ne change, car le compteur est en base.
- **Questionnaire modifié plus tard.** Chaque partie note la version du questionnaire. Une partie en cours sur une
  ancienne version est terminée avec la table de sa version (la version 1 = 7 questions).
- **Réseau coupé pendant la sauvegarde d'une réponse.** Le site affiche une erreur et l'élève peut réessayer.
  On ne passe à la question suivante qu'une fois la réponse enregistrée.

## Hors périmètre

- Bouton « Abandonner cette partie » (décision du 2026-11-10). Une partie commencée se reprend toujours, donc il
  n'y a pas de statut « abandonnée ».
- Correction exceptionnelle du compteur par un administrateur (décision du 2026-11-10). Elle sera ajoutée si le
  besoin se présente. Aucune remise à zéro automatique n'existe, ni par semestre ni autrement.
- Statistiques des résultats dans l'espace admin.
- Jeu pour les visiteurs ou les encadreurs.

## Décisions (2026-11-10)

- Il n'y a pas de bouton d'abandon.
- La correction par un administrateur viendra plus tard.
- Les réponses et les résultats sont gardés tant que le compte existe.
- Le compteur démarre à 0/3 pour tous les élèves, car l'ancienne version n'enregistrait rien.

## Questions ouvertes

Aucune.
