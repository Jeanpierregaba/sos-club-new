# CAHIER DES CHARGES TECHNIQUE ET FONCTIONNEL
## Plateforme Nationale Interactive des Clubs Santé SOS DOCTEUR TV - Togo
### *Sous le parrainage de AIMES-AFRIQUE*

---

## 📌 1. INTRODUCTION ET CONTEXTE

### 1.1 Contexte du Projet
Sous le parrainage de l'organisation humanitaire **AIMES-AFRIQUE** et en partenariat avec **SOS DOCTEUR TV**, la plateforme nationale interactive des **Clubs Santé** a pour vocation de digitaliser, structurer et dynamiser l'action des clubs de santé scolaires à travers tout le Togo. 

Les clubs santé jouent un rôle clé dans la sensibilisation des élèves aux problématiques de santé publique : hygiène et assainissement, nutrition, santé sexuelle et de reproduction, prévention des grossesses précoces, lutte contre les Maladies Non Transmissibles (MNT) et protection de l'environnement.

### 1.2 Objectifs de la Plateforme
1. **Éduquer et Informer** : Fournir une bibliothèque de ressources multimédias validée médicalement (articles, vidéos, fiches pratiques).
2. **Collaborer et Communiquer** : Offrir une visibilité nationale aux activités menées localement par chaque club.
3. **Valoriser et Responsabiliser (Gamification)** : Stimuler l'engagement des élèves et valoriser l'accompagnement des enseignants.
4. **Générer des défis et dynamiser l'émulation inter-écoles** : Permettre aux clubs de se défier mutuellement sur des thématiques de santé publique.

---

## 🌐 2. VUE D'ENSEMBLE DE L'ARCHITECTURE

La plateforme est construite sur une architecture moderne de type **Single Page Application (SPA)** fluide, robuste et entièrement typée en **TypeScript**.

### Schéma Conceptuel & Interface Visualisée
Ci-dessous l'organisation conceptuelle de l'interface utilisateur, des rôles et des données de la plateforme :

![Maquette & Architecture Système](/src/assets/images/architecture_mockup_1783105269994.jpg)

### 2.1 Stack Technique
* **Frontend** : React 18+ (avec Vite)
* **Langage** : TypeScript (Typage strict pour la robustesse et la maintenabilité)
* **Design & Styles** : Tailwind CSS (Approche utilitaire, responsive, thémée avec une charte émeraude/teal moderne et épurée)
* **Librairie d'icônes** : `lucide-react` (Usage unique de ce set pour la cohérence visuelle)
* **Animations** : `motion/react` (Animations d'entrées fluides, transitions de routes légères)
* **Persistence** : État React local enrichi et synchronisé, prêt pour une connexion d'API REST/Firebase ou PostgreSQL.

---

## 👥 3. GESTION DES 4 ROLES CLÉS (PERSONAS)

La plateforme sépare de manière stricte et étanche les profils d'utilisateurs pour répondre aux besoins spécifiques de chaque acteur de l'écosystème scolaire :

### 3.1 L'Élève (Rôle "Visiteur/Élève")
* **Rôle** : Membre actif d'un club santé au sein de son établissement scolaire.
* **Conditions d'inscription** : Doit obligatoirement s'enregistrer sous l'égide d'un Club Santé existant.
* **Fonctionnalités** :
  * Possède son propre **Passeport Santé & Compétences** qui affiche ses badges (ex: `'🌱 Membre Novice'`, `'🥇 Secouriste Certifié'`) et ses points individuels.
  * Participe aux quiz interactifs (Grand concours "Génie Imhotep") pour accumuler des points.
  * Rédige et soumet des témoignages/articles d'initiatives locales dans la section "Paroles aux Élèves" (soumis à modération).
* **Impact collectif** : Chaque nouvelle inscription d'un élève fait automatiquement gagner des points de bonus collectifs au club qu'il a rejoint.

### 3.2 L'Encadreur / L'Animateur (Rôle "Responsable")
* **Rôle** : Enseignant (souvent de SVT ou d'Éducation Civique) encadrant les activités de santé.
* **Parcours et Actions** :
  * Il possède son propre compte individuel distinct du Club.
  * Il supervise l'activité des jeunes, lit les productions littéraires et commente sous les articles de son club ou des jeunes de la plateforme.
  * **Valorisation et Points** : Pour récompenser son implication active et son mentorat, l'encadreur gagne des points personnels à chaque interaction constructive, réponse pédagogique aux élèves, ou validation d'activité. Un classement national des "Meilleurs Encadreurs" est disponible pour valoriser son statut professionnel.

### 3.3 Le Club (La Console Collective)
* **Rôle** : L'entité collective représentant l'établissement scolaire (ex: "Club Santé Lycée Tokoin").
* **Fonctionnalités de la Console du Club** :
  * **Suivi des Points** : Visualisation du score global du club, incluant la somme des points d'activités collectives et les points générés par ses élèves membres.
  * **Publication d'Activités** : Rédaction d'articles d'initiatives de terrain avec chargement de photos, obligatoirement classés sous l'un des **7 axes de santé publique**.
  * **Publication de l'Agenda** : Ajout de leurs propres programmes, séances de sensibilisation et événements locaux directement dans le calendrier partagé.
  * **Suivi de Modération** : Interface de contrôle permettant de voir si leurs articles soumis ont été approuvés par l'administrateur national et sont en ligne.
  * **Interactions et Réponses** : Réception de notifications en temps réel lors de commentaires sur leurs articles et outil de réponse pour entretenir la discussion communautaire.
  * **Bouton de Défi** : Un bouton d'action unique **"Défier un autre club"** permettant de lancer des olympiades ou des concours inter-écoles sur des sujets de santé publique.

### 3.4 L'Administrateur (Rôle "Admin")
* **Rôle** : Équipe de supervision nationale d'AIMES-AFRIQUE et SOS DOCTEUR TV.
* **Fonctionnalités** :
  * **Modération A Priori** : Validation/rejet des articles soumis par les clubs et les élèves avant publication publique.
  * **Attribution de Distinctions** : Octroi manuel de badges d'excellence nationale.
  * **Statistiques Globales** : Suivi des indicateurs d'engagement (nombre de membres, progression des scores) et traitement des rapports de dépistage des maladies non transmissibles (MNT).

---

## 🗺️ 4. ARCHITECTURE DU MENU ET CONTENU DES PAGES

Le menu de navigation a été restructuré pour offrir un parcours utilisateur fluide et une hiérarchie claire :

### 4.1 Accueil (Page Principale)
* **Section Hero** : Introduction de SOS DOCTEUR TV et du parrainage d'AIMES-AFRIQUE.
* **Bandeau d'Actions Rapides** : Boutons de redirection rapide (Défis, Carte, Inscriptions).
* **Aperçu Dynamique** : Les actualités brûlantes, le prochain événement national et le carrousel des 7 axes de la santé publique.

### 4.2 Club Santé (Sous-menu Institutionnel)
* **Vision** : Digitaliser et élever l'éducation pour la santé en milieu scolaire à un niveau d'excellence nationale.
* **But** : Éduquer les jeunes sur les réflexes de santé préventive pour une jeunesse togolaise épanouie.
* **Mission** : Impliquer directement les élèves dans des actions d'assainissement, d'éducation par les pairs et de dépistage précoce.
* **Objectifs** : Élimination des grossesses en milieu scolaire, maîtrise universelle des gestes de premier secours et sensibilisation aux MNT.
* **Slogan** : Recueil des slogans inspirants de la jeunesse ("Notre santé, notre avenir !", "Engagés pour la vie !").
* **Mot du Promoteur** : Message d'encouragement et vision stratégique du Dr Michel KODOM (Promoteur de SOS DOCTEUR TV et Président d'AIMES-AFRIQUE).
* **Carte des Clubs (TogoMap)** : Carte vectorielle stylisée du Togo découpée par régions sanitaires (Savanes, Kara, Centrale, Plateaux, Maritime, Grand Lomé) montrant la localisation et le palmarès de chaque club scolaire.
* **Partenaires** : Valorisation des partenaires techniques et financiers qui soutiennent l'initiative.

### 4.3 Vie du Club (Sous-menu Communautaire)

#### A. S'informer (Espace Pédagogique Interactif)
* **Les Capsules Vidéo SOS DOCTEUR TV** : Une vidéothèque de capsules de sensibilisation médicale produites par SOS DOCTEUR TV et animées par des médecins experts.
* **Classification par les 7 Axes de la Santé Publique** : L'administrateur peut à tout moment importer de nouvelles vidéos via sa console et les ranger rigoureusement sous l'un des 7 axes fondamentaux :
  1. *Éducation pour la Santé*
  2. *Eau, Hygiène et Assainissement*
  3. *Nutrition et Alimentation saine*
  4. *Santé Sexuelle et de Reproduction*
  5. *Prévention des Maladies Non Transmissibles (MNT)*
  6. *Santé Mentale des Jeunes*
  7. *Protection de l'Environnement*

#### B. Hall of Fame (Le Panthéon de la Santé Scolaire)
* **Structure Tripartie** : Affichage dynamique des classements des trois acteurs majeurs :
  * **Top Clubs** (basé sur le score d'actions réelles et d'inscriptions d'élèves).
  * **Top Élèves** (basé sur les scores d'expérience aux quiz et défis).
  * **Top Encadreurs** (basé sur les points d'interactions et de mentorat).
* **Règle des "Top 3 Régionaux"** : La plateforme affiche le **Top 3 par Région Sanitaire** (Maritime, Plateaux, Centrale, Kara, Savanes, Grand Lomé), récompensant équitablement les efforts de tous les établissements à travers le pays.

#### C. Agenda (Planification Sanitaire et Défis)
* Calendrier synchronisé permettant de visualiser les actions prévues à trois niveaux de filtres :
  * **Par Région** : Pour suivre les campagnes régionales organisées par AIMES-AFRIQUE.
  * **Par École / Club** : Pour découvrir les initiatives et événements de chaque établissement.
  * **Par Type d'Activité** : Filtrage par type d'événement (Sensibilisation, Journée de Nettoyage, Olympiade/Défi Inter-Club, Campagne de Dépistage).

### 4.4 Gamification (Défis & Quiz)
La page de Gamification se divise en trois grandes sections :
* **Meilleurs Scores** : Affichage des leaders nationaux et régionaux du concours.
* **Quiz Libres par Thème** :
  * Des quiz thématiques de **15 questions** chacun.
  * **Temps de réponse de 5 secondes maximum par question** pour encourager la spontanéité et ancrer les réflexes d'urgence.
  * Réussir le quiz (au moins 12 bonnes réponses sur 15) débloque **+25 points individuels** (sur son Passeport Santé), **+10 points collectifs pour son Club affilié**, et des badges thématiques exclusifs.
* **Défis Inter-Clubs** : Olympiades scolaires qu'un club peut lancer à un autre club national. Le défi est un parcours d'épreuves combiné comprenant :
  * **1 Quiz** complet de culture générale de santé.
  * **1 Puzzle** médical interactif (gestes de premiers secours).
  * **5 Séries de Jeux de Lettres** (mots fléchés de santé publique).
  * **3 Séries de Calcul Mental** (calcul d'IMC, dosage simple de réhydratation, etc.).
  * *Gain* : +200 points collectifs pour le club gagnant.

### 4.5 Actualités
* **Le Magazine National** : Actualités officielles rédigées par l'équipe nationale ou les clubs approuvés.
* **Paroles aux Élèves** : Espace d'expression libre où les élèves partagent leurs témoignages de santé, soumis à la validation d'AIMES-AFRIQUE.

### 4.6 Bibliothèque (Téléchargements et Magazines SOS DOCTEUR TV)
* **Slider "À la Une"** : Grand carrousel visuel présentant les affiches principales et résumés des **3 derniers magazines** officiels publiés par SOS DOCTEUR TV.
* **Lecture & Téléchargement direct** : Accès direct pour lire et télécharger les magazines en format PDF, ainsi que les guides de premiers secours et fiches pratiques d'assainissement d'AIMES-AFRIQUE.

### 4.7 Rejoindre le Club
* Formulaires de connexion et d'inscription d'élèves, d'encadreurs et de clubs scolaires.

---

## 🔐 5. CONDITIONS ET RÈGLES DE VALIDATION POUR L'INSCRIPTION

### 5.1 Inscription d'un Élève
* L'élève s'inscrit obligatoirement sous l'égide d'un Club existant.
* L'inscription est validée immédiatement et **attribue automatiquement +50 Points au score de son Club**.
* L'élève démarre avec son Passeport Santé crédité de 20 Points d'Engagement personnels.

### 5.2 Inscription d'un Encadreur
* L'enseignant s'inscrit avec ses coordonnées et sa spécialité pédagogique. Il gagne des points personnels de mentorat à chaque commentaire/conseil formulé sous les articles.

### 5.3 Enregistrement d'un Club (La Règle de Sécurité des 3 Encadreurs)
* **CONDITION INCONTOURNABLE** : Pour s'enregistrer, un nouveau Club Santé **doit obligatoirement renseigner exactement 3 encadreurs différents** avec leurs coordonnées complètes (Nom, Email, Téléphone).
* Cette clause garantit :
  1. La **continuité des activités** (si un enseignant est malade ou muté, deux autres prennent le relais).
  2. Une **collégialité sécurisée** dans le contrôle des activités des élèves.

---

## 📋 6. RÈGLES MÉTIER DU SYSTÈME DE POINTS

| Action Déclencheuse | Bénéficiaire | Points Attribués | Impact Écosystème |
| :--- | :--- | :--- | :--- |
| **Inscription d'un Élève** | Le Club Santé affilié | **+50 Pts** | Stimule la promotion locale du club par les pairs. |
| **Réussite d'un Quiz "Génie Imhotep"** | L'Élève (Passeport Santé) & Son Club | **+25 Pts** (Élève) / **+10 Pts** (Club) | Débloque des distinctions individuelles et renforce le score collectif. |
| **Commentaire constructif d'un Encadreur** | L'Encadreur (Profil personnel) | **+10 Pts** | Encourage le mentorat actif des adultes sur la plateforme. |
| **Publication d'activité par un Club** | Le Club Santé | **+100 Pts** | Valorise les séances d'assainissement ou de formation réelles. |
| **Dépistage précoce d'un élève (anonyme)** | Le Club Santé | **+15 Pts / fiche** | Soutient les efforts de prévention sanitaire d'AIMES-AFRIQUE. |
| **Vainqueur d'un Défi Inter-Clubs** | Le Club Santé | **+200 Pts** | Crée un sentiment de fierté et de compétition positive. |
