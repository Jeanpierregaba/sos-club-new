# 028 — Bibliothèque : ressources et fascicules (R10)

## Objectif

Rendre réelle la bibliothèque (`/bibliotheque`), aujourd'hui remplie de documents d'exemple aux liens vides
(CDC § 4.6, PRD : « les ressources validées médicalement sont difficiles à trouver »). L'équipe nationale y
publie des PDF : magazines SOS Docteur TV, guides d'action, fiches pratiques, affiches et fascicules
pédagogiques (Q11 : préparés par les gestionnaires pédagogiques, depuis l'espace admin).

Deux publics :

- l'équipe nationale : un collaborateur prépare et soumet la ressource ; un autre la publie en nommant la
  personne qui a validé le contenu médical (même règle à deux personnes que les quiz, spec 027) ;
- tout le monde : la bibliothèque est publique, visiteurs compris. Les fichiers ne contiennent aucune donnée
  d'élève.

Les fascicules sont posés ici comme une catégorie de ressource ; le parcours Génie Imhotep (R11) les reliera à
ses quiz.

## Comportement attendu

**Préparer une ressource (droits `bibliotheque` créer / modifier / soumettre)**

1. Le collaborateur crée une ressource en brouillon : titre (150 caractères au plus), courte description
   (500 au plus), catégorie (magazine, guide d'action, fiche pratique, affiche, fascicule), axe facultatif (un des
   7), et pour un magazine son numéro ou sa date de parution.
2. Il dépose le fichier : un PDF de 20 Mo au plus. L'API vérifie que c'est un vrai PDF et refuse un PDF qui
   contient du JavaScript, une action de lancement ou un fichier joint. Il peut remplacer le fichier tant que la
   ressource est en brouillon.
3. Il dépose une image de couverture (JPEG, PNG ou WebP, 8 Mo au plus), recompressée en WebP sans métadonnées
   comme les photos des articles (spec 024). Elle est facultative, sauf pour un magazine. Sans couverture, la
   carte garde le visuel de sa catégorie (couleur et icône).
4. Il soumet la ressource quand elle a un fichier (et une couverture pour un magazine). Une ressource soumise
   n'est plus modifiable ; il peut la reprendre en brouillon.

**Publier (droits `bibliotheque` approuver / dépublier, double authentification)**

5. Un collaborateur qui a le droit d'approuver voit la file des ressources soumises, ouvre le PDF et :
   - approuve en nommant la personne qui a validé le contenu (nom et qualité, obligatoires) : la ressource est
     publiée ;
   - ou refuse avec un motif : la ressource revient en brouillon.
     Il ne peut pas approuver une ressource qu'il a lui-même créée, modifiée ou soumise.
6. Il peut dépublier une ressource publiée avec un motif : elle disparaît de la bibliothèque et son fichier
   n'est plus servi. Pour la corriger, on la reprend en brouillon, puis on la soumet de nouveau.
7. Le préparateur est prévenu de chaque décision par une notification (spec 023). Chaque action (création,
   dépôt de fichier, soumission, approbation, refus, dépublication, suppression) entre au journal d'audit.
8. Une ressource jamais publiée peut être supprimée en brouillon : ses fichiers sont effacés. Une ressource
   déjà publiée ne se supprime pas ; elle se dépublie.

**Consulter (tout le monde)**

9. La bibliothèque montre :
   - en tête, le carrousel « À la Une » : les 3 derniers magazines publiés, avec leur couverture ;
   - la liste des ressources publiées, des plus récentes aux plus anciennes, filtrable par catégorie et par axe ;
   - pour chacune : couverture ou visuel de catégorie, titre, description, catégorie, taille du fichier, date de
     publication, nombre de téléchargements et validateur médical (« Validé par Dr … »).
10. « Lire » ouvre le PDF dans le navigateur ; « Télécharger » l'enregistre. Chaque téléchargement ou ouverture
    ajoute 1 au compteur de la ressource ; on ne garde pas qui a téléchargé.
11. Les chiffres de la page (nombre de documents, téléchargements) sont calculés sur les ressources publiées.
12. Les ressources de test chargées par `seed_dev` portent la mention « Contenu de test » (RULES : pas de contenu
    médical inventé présenté comme réel) ; elles ne sont jamais chargées en prod.

## Critères d'acceptation

- [ ] Étant donné un élève, un encadreur, un président ou un visiteur, quand il appelle une route de gestion de
      la bibliothèque, alors l'API répond 401 ou 403, et rien ne change.
- [ ] Étant donné un collaborateur sans le droit `bibliotheque` voulu, quand il appelle la route
      correspondante, alors l'API répond 403 ; l'approbation et la dépublication exigent la double
      authentification.
- [ ] Étant donné un fichier qui n'est pas un PDF (même renommé en `.pdf`), ou un PDF de plus de 20 Mo, alors
      l'API le refuse (422 ou 413).
- [ ] Étant donné un PDF qui contient du JavaScript, une action de lancement ou un fichier joint, alors l'API le
      refuse (422).
- [ ] Étant donné une ressource sans fichier, ou un magazine sans couverture, quand on la soumet, alors l'API
      refuse (422).
- [ ] Étant donné une ressource soumise ou publiée, quand on tente d'en changer le fichier ou les informations,
      alors l'API refuse (409).
- [ ] Étant donné un collaborateur qui a créé, modifié ou soumis une ressource, quand il l'approuve, alors l'API
      refuse (403), même s'il a le droit d'approuver.
- [ ] Étant donné une approbation sans nom ou sans qualité du validateur, alors l'API refuse (422).
- [ ] Étant donné une ressource publiée, alors un visiteur la voit dans la liste et en télécharge le fichier ;
      un brouillon, une ressource soumise ou dépubliée n'apparaît pas, et son fichier répond 404 au public.
- [ ] Étant donné un collaborateur qui a le droit de consulter la bibliothèque, alors il ouvre le fichier d'une
      ressource soumise pour la relire.
- [ ] Étant donné 4 magazines publiés, alors « À la Une » montre les 3 plus récents.
- [ ] Étant donné un téléchargement, alors le compteur de la ressource augmente de 1 ; aucune donnée sur la
      personne n'est enregistrée.
- [ ] Étant donné une ressource jamais publiée, quand on la supprime, alors ses fichiers sont effacés du
      stockage ; une ressource déjà publiée ne se supprime pas (409).
- [ ] Étant donné le fichier PDF servi, alors la réponse porte le bon type, un nom de fichier tiré du titre, et
      des en-têtes qui empêchent son exécution comme page du site.

## Cas limites et erreurs

- **Lecture par morceaux** : l'API envoie toujours le fichier entier (pas de demande par morceaux) ; chaque
  ouverture ou téléchargement compte une fois. Le compteur n'est qu'un indicateur : recharger la page le fait
  monter, et il ne rapporte rien.
- **Fichier remplacé** : l'ancien fichier est effacé du stockage ; l'adresse change, aucun cache ne sert
  l'ancien.
- **Dépublication pendant un téléchargement** : le téléchargement en cours peut finir ; les suivants
  répondent 404.
- **Course entre deux collaborateurs** (deux approbations, approbation pendant une reprise en brouillon) : une
  seule décision passe, l'autre reçoit 409.
- **Stockage indisponible** au dépôt ou à la lecture : 503 avec un message clair (comme la spec 024).
- **Nom de fichier** : le nom proposé au téléchargement est tiré du titre (sans accent ni caractère spécial) ;
  aucun nom choisi par l'utilisateur n'arrive sur le disque (ADR-0010).
- **Liste vide** : la bibliothèque affiche un message d'attente au lieu des documents d'exemple.

## Hors périmètre

- Les vidéos (R20, sur YouTube) et les pages institutionnelles (R21).
- Le lien entre fascicules et quiz du parcours Génie Imhotep (R11).
- Les points pour une lecture ou un téléchargement (aucun au barème).
- Le dépôt de ressources par les encadreurs ou les clubs.
- La recherche plein texte dans les PDF, les versions successives d'une même ressource, les langues.
- Les statistiques de téléchargement par jour ou par public.

## Questions ouvertes

Aucune : accès public, publication à deux personnes, PDF et couverture, compteur agrégé (tranchés le
2026-11-09).
