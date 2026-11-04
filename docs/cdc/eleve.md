<!-- Transcription de « Cahier_des_charges_Compte_Eleve_Club_Sante_Version_Moderation.docx », reçu le 2026-11-04. Ne pas modifier : le PRD fait foi en cas d'écart. -->

DOCUMENT DE CADRAGE • ESPACE ÉLÈVE

# Compte élève & système de gamification

Fonctionnement du compte, carte membre numérique, activités, points, certification, classements et récompenses semestrielles.

Version de travail destinée à l’équipe projet et aux développeurs. Les barèmes ci-dessous reprennent les choix du programme ; les modalités de vérification restent à formaliser.

## 1. Principe général

Chaque élève peut créer gratuitement un compte personnel sur la plateforme des Clubs Santé SOS Docteur TV pour apprendre, participer aux quiz, publier des contenus, échanger et contribuer à la vie de son Club Santé. Les actions éligibles rapportent des points personnels ; certaines rapportent aussi des points au club auquel l’élève est affilié.

Promesse élève : « Apprends. Participe. Partage. Progresse. Fais briller ton Club Santé ! »

## 2. Création du compte et affiliation

Inscription et validation du compte : bonus de bienvenue de 100 points, attribué une seule fois.

Profil : identité, pseudonyme affiché publiquement, niveau/classe, établissement, club affilié (si applicable) et informations de connexion.

Affiliation : seuls les élèves rattachés à un Club Santé reconnu génèrent des points pour ce club.

Accès : un élève sans club peut participer aux fonctionnalités individuelles de la plateforme.

## 3. Carte membre numérique du Club Santé

Dès que son compte est créé et validé, chaque élève reçoit automatiquement une carte membre numérique des Clubs Santé SOS Docteur TV. Cette carte est nominative et accessible à tout moment dans son espace personnel ; elle permet de matérialiser son adhésion à la communauté.

### 3.1. Émission et contenu de la carte

Génération automatique et attribution gratuite après validation de la première inscription ; une seule carte active par compte.

Éléments affichés : identité ou nom d’usage selon les règles du programme, photo de profil si autorisée, numéro d’adhérent unique, établissement, Club Santé d’affiliation (le cas échéant) et statut de la carte.

Identité graphique : logo officiel, intitulé « Carte membre – Club Santé SOS Docteur TV », design lisible et cohérent avec la plateforme.

Un QR code ou code de vérification peut être prévu pour vérifier le statut de la carte ; il ne doit donner accès à aucune donnée personnelle sensible.

### 3.2. Fonctions disponibles dans le compte élève

Rubrique « Ma carte membre » directement accessible depuis le menu, avec aperçu recto et, si retenu, verso.

Téléchargement de la carte au format PDF ou image, pour conservation sur téléphone ou impression.

Actualisation automatique des informations autorisées après modification validée du profil ou de l’affiliation.

Possibilité de partager volontairement une version publique limitée de la carte, sans identifiants privés ni données sensibles.

### 3.3. Gestion, confidentialité et cas particuliers

Une carte est associée à un compte élève et à un identifiant unique non réutilisé.

Le statut doit pouvoir être actif, suspendu ou désactivé ; une carte désactivée ne doit pas être considérée comme valide.

Un élève sans Club Santé affilié reçoit sa carte ; la zone « Club affilié » affiche « Non affilié » jusqu’à validation du rattachement.

En cas de changement d’établissement ou de Club Santé, la carte est actualisée après contrôle sans création d’un second compte.

Le QR code, s’il existe, affiche uniquement les données nécessaires à la vérification de validité ; l’accès aux autres informations exige une authentification et des droits adaptés.

La délivrance de la carte ne génère pas de points supplémentaires : elle accompagne les 100 points de bienvenue déjà attribués pour la création et la validation du compte.

## RÈGLE OBLIGATOIRE — Validation préalable des contenus des élèves

Aucun contenu créé ou envoyé par un élève ne peut apparaître publiquement sur la plateforme sans validation préalable et explicite de l’administrateur (ou d’un modérateur auquel ce droit a été délégué). Cette règle s’applique à toutes les zones participatives du site.

Périmètre : articles du blog, textes, photographies, commentaires, publications communautaires, questions et réponses du forum et toute autre contribution visible des élèves.

À l’envoi, le contenu reçoit le statut « En attente de validation ». Il est visible uniquement par son auteur et les personnes habilitées à modérer ; il n’apparaît ni dans le blog, ni sur le forum, ni dans les flux publics, ni dans les recherches publiques.

L’administrateur dispose d’une file de modération pour consulter le contenu et ses médias, puis l’approuver, le refuser avec motif ou demander une correction. Les décisions sont enregistrées (date, personne responsable, motif).

Après approbation, le contenu passe au statut « Publié » et peut être affiché sur le site. En cas de refus ou de demande de correction, l’élève reçoit une notification et peut modifier puis soumettre à nouveau son contenu.

Les points de publication (+50 élève et +20 club) et de commentaire (+5 élève) ne sont crédités qu’après approbation. Aucun point n’est attribué à un contenu refusé, en attente ou supprimé pour infraction ; un retrait motivé peut entraîner l’annulation des points associés.

Les points de partage ne peuvent être accordés que pour un article préalablement approuvé et publié, après la vérification de l’action correspondante. Le partage d’un contenu non approuvé n’ouvre aucun droit à points.

Des filtres automatiques de sécurité peuvent assister l’équipe, mais ils ne remplacent pas l’approbation humaine exigée avant mise en ligne. Les photos impliquant des mineurs doivent respecter les autorisations et règles de confidentialité applicables.

Le développeur doit empêcher techniquement l’accès public aux brouillons et contenus en attente, y compris via lien direct, recherche, API, fil d’actualité ou notification publique.

Parcours de modération : Brouillon → Soumis / En attente → Approuvé et publié OU Refusé / À corriger. Toute modification substantielle d’un contenu déjà approuvé entraîne un retour en validation avant l’affichage de la nouvelle version.

## 4. Barème des points

| Action                                                       | Points élève | Points club |
| ------------------------------------------------------------ | ------------ | ----------- |
| Création et validation du compte                             | +100         | —           |
| Commentaire pertinent et validé sur un article               | +5           | —           |
| Republication d’un article de la plateforme                  | +10          | —           |
| Article personnel publié (texte et photos), après modération | +50          | +20         |
| Partage de son propre article : Facebook                     | +50          | —           |
| Partage de son propre article : Instagram                    | +50          | —           |
| Partage de son propre article : TikTok                       | +50          | —           |
| Partage de son propre article : LinkedIn                     | +50          | —           |
| Quiz réussi                                                  | +25          | +10         |
| Certification Génie Imhotep obtenue                          | +1 000       | +100        |

Exemple : un article validé (+50) partagé ensuite sur trois réseaux distincts (+150) rapporte 200 points à l’élève et 20 points à son club.

## 5. Activités accessibles depuis le tableau de bord

### 5.1. Mon tableau de bord

Vue synthétique : points du semestre et cumul historique, rang individuel, points et rang du club, dernières actions, progression de certification et prochains événements. Un module « Ma carte membre » affiche l’aperçu de la carte, son statut et les actions « Voir » / « Télécharger ».

### 5.2. Actualités et publications

L’élève peut consulter, commenter, relayer les articles et soumettre ses propres contenus (textes et photos). Aucun article ni commentaire d’élève ne devient public avant approbation explicite d’un administrateur ou modérateur autorisé. Les points correspondants sont accordés seulement à la validation.

### 5.3. Partages sur les réseaux sociaux

L’élève peut republier un article de la plateforme (+10 points) ou partager son propre article publié (+50 points par réseau social distinct : Facebook, Instagram, TikTok, LinkedIn). Un partage doit être vérifiable ; l’ouverture du bouton de partage seule ne valide pas la récompense. Pour son propre article, un même réseau ne rapporte les 50 points qu’une seule fois.

### 5.4. Quiz et jeux

Accès sans restriction à l’ensemble des quiz et jeux. Les tentatives peuvent être répétées pour apprendre ; les points de réussite (+25 élève / +10 club) ne sont accordés qu’une seule fois pour un même quiz réussi afin de préserver l’équité du classement.

### 5.5. Certification Génie Imhotep

Parcours progressif avec fascicules pédagogiques et 12 Quiz Santé obligatoires. Après validation : Certificat Officiel Génie Imhotep, cinq badges et bonus de +1 000 points pour l’élève et +100 points pour son club. Le bonus de certification est attribué une seule fois et compté au semestre de son obtention.

Les lots pouvant aller jusqu’à 1 MILLION FCFA relèvent du dispositif de certification et de son règlement ; ils sont distincts des récompenses du Top 3 semestriel.

### 5.6. Forum et chatbot SOS

Le forum permet de proposer des questions et réponses autour des sept axes. Tous les messages, réponses et contenus joints envoyés par les élèves restent invisibles aux autres utilisateurs jusqu’à validation par un administrateur ou modérateur autorisé. Le chatbot aide à naviguer, apprendre et trouver des ressources ; il ne remplace pas un professionnel de santé.

## 6. Classements individuels et collectifs

Deux niveaux de score doivent être visibles : (1) le total historique de l’élève et (2) les points gagnés pendant le semestre en cours, qui déterminent le Top 3 semestriel. Les clubs disposent d’un classement collectif alimenté par les articles validés, les quiz réussis et les certifications de leurs membres affiliés.

## 7. Partager son classement sur les réseaux sociaux

Depuis son tableau de bord ou la page « Classements », l’élève peut sélectionner « Partager mon classement » et générer une carte visuelle prête à publier sur ses réseaux sociaux.

La carte de partage présente le pseudonyme de l’élève, sa position actuelle, ses points du semestre, une mention « Clubs Santé SOS Docteur TV » et, si souhaité, le nom de son club.

L’élève peut choisir de partager son classement général ou son classement au sein de son club, lorsque ces deux vues existent.

La carte peut être téléchargée au format image et/ou partagée via les options natives du téléphone ou du navigateur.

Par défaut, aucune donnée sensible (nom complet, âge, classe précise, coordonnées) ne doit apparaître sur le visuel public.

Le partage du classement ne rapporte pas de points supplémentaires pour le moment : aucun bonus n’a été fixé pour cette action.

## 8. Récompenses semestrielles : Top 3 des élèves

À la fin de chaque semestre, les trois élèves ayant obtenu le plus de points pendant la période sont distingués et récompensés, après contrôle et validation du classement.

| Rang | Distinction                |
| ---- | -------------------------- |
| 1er  | Grand Champion du semestre |
| 2e   | Vice-Champion du semestre  |
| 3e   | Jeune Talent du semestre   |

Un nouveau classement semestriel démarre à zéro au début de chaque période.

Les points historiques, badges et réalisations restent visibles sur le profil.

Les récompenses et éventuelles dotations sont annoncées dans un règlement distinct.

Un règlement précise les dates, l’éligibilité, le traitement des ex æquo, la fraude et les vérifications.

Sous réserve d’autorisations adéquates, les lauréats peuvent être valorisés sur la plateforme et SOS Docteur TV.

## 9. Rubriques du compte élève

Mon tableau de bord • Mon profil • Ma carte membre • Actualités et publications • Publier un article • Quiz et jeux • Ma certification • Classements et récompenses • Mon Club Santé • Forum de discussion • Agenda • Ressources • Chatbot SOS.

## 10. Garde-fous et règles à préciser avant développement

Validation du compte et prévention des comptes multiples ; protection des données des mineurs.

Modération préalable obligatoire de toute contribution des élèves (articles, commentaires, posts et réponses de forum, textes, photos et autres pièces jointes), avec possibilité de signalement, retrait et suspension. Aucune publication automatique.

Vérification des partages selon les limites techniques des réseaux sociaux.

Définition d’une politique anti-spam pour les commentaires et les publications.

Historisation de chaque attribution ou retrait de points, avec motif et date.

Choix des dates exactes des semestres et validation officielle du règlement des prix.

### Critères de validation de la carte membre

Une inscription validée crée exactement une carte et crédite une seule fois le bonus de bienvenue de 100 points.

L’élève retrouve sa carte sur son tableau de bord et dans « Ma carte membre » ; le téléchargement fonctionne sur ordinateur et smartphone.

Le numéro d’adhérent reste unique ; les changements d’affiliation mettent à jour la carte sans créer de doublon.

Une carte suspendue apparaît comme non valide lors de toute vérification ; aucune donnée sensible n’est exposée par un QR code public.

Finalité : transformer la plateforme en espace d’apprentissage, d’expression et de mobilisation, où les efforts individuels contribuent également à la dynamique collective des Clubs Santé.

### Critères de recette — Modération obligatoire

Un article, commentaire ou message de forum soumis par un élève n’est pas visible par un autre élève tant qu’aucun administrateur ne l’a approuvé.

L’administrateur peut approuver, refuser et demander une correction depuis une interface de modération centralisée.

Les points élève et club liés aux publications et commentaires ne sont ajoutés qu’une fois le contenu approuvé ; les actions rejetées ne génèrent aucun point.

Une modification de contenu approuvé est masquée tant que la nouvelle version n’est pas revalidée.

Les contenus en attente ne sont accessibles par aucun lien public, API publique, moteur de recherche ou flux social intégré.
