# DESIGN — Interface et expérience

## Intention

Joyeux, énergique, digne de confiance : un univers de jeunes, porté par une institution médicale.
Références : la page d'accueil actuelle du site et ses mascottes caméléons. Le ton reste ludique pour
les élèves, mais les contenus de santé restent sobres et lisibles.

## Design system

shadcn/ui sur Radix (`src/components/ui/`), icônes `lucide-react` uniquement (plus `TikTokIcon`, absent
de cette bibliothèque). On n'invente pas de composant si un équivalent existe. Les animations
d'apparition passent par `SiteMotion` et les classes `btn-fx`, `card-fx` et `data-reveal`.

Règles visuelles fixées par le porteur du projet :

- Boutons principaux en vert du logo (`primary`).
- Titres de section en minuscules, en deux couleurs : bleu du logo puis vert.

## Tokens

Une seule source : `src/styles.css`. Ne pas écrire de couleur en dur.

- **Marque** : `primary` (vert du logo), `logo-blue`, `logo-red`.
- **Univers et catégories** : `sun`, `tangerine`, `leaf`, `sky`, `rose`, `bark`, `grape`.
- **Fonds** : `background`, `card`, `mist`, `mist-soft`, `lilac` ; texte sur fond sombre et pied de page : `night`.
- **Typographie** : Lilita One pour les titres, Outfit pour le texte, Caveat Brush pour les touches manuscrites.
- **Formes** : rayon de base 1rem, cartes en `rounded-3xl`, ombre `shadow-card`.

## Écrans principaux

Navigation : Accueil, Club Santé, Vie du Club (S'informer, Hall of Fame, Agenda), Gamification,
Actualités, Bibliothèque, Rejoindre le Club. Elle remplacera le menu actuel de l'accueil, qui pointe
encore vers des pages absentes.

| Écran           | Route visée                | But et contenu                                                                                                                                                                   | Actions                                              |
| --------------- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Accueil         | `/`                        | Existant, à brancher sur les vraies données                                                                                                                                      | Aller aux quiz, carte, inscription                   |
| Club Santé      | `/club-sante`              | Vision, mission, slogans, mot du promoteur, partenaires                                                                                                                          | Lire                                                 |
| Carte des clubs | `/clubs`                   | Carte par région et palmarès                                                                                                                                                     | Filtrer, ouvrir un club                              |
| Page d'un club  | `/clubs/:id`               | Score, articles, événements, sans liste d'élèves                                                                                                                                 | Lire                                                 |
| S'informer      | `/videos`                  | Capsules par axe                                                                                                                                                                 | Filtrer, lire                                        |
| Hall of Fame    | `/hall-of-fame`            | Classements DRE et national : élèves, encadreurs, clubs ; semestre ou historique ; palmarès des semestres publiés (Top 3, spec 037) ; lien vers le Hall of Fame du Génie Imhotep | Changer de DRE, de catégorie et de période ; paginer |
| Agenda          | `/agenda`                  | Calendrier et liste                                                                                                                                                              | Filtrer par région, club, type                       |
| Gamification    | `/quiz`, `/quiz/:id`       | Meilleurs scores, quiz par thème, partie chronométrée                                                                                                                            | Jouer, reprendre                                     |
| Actualités      | `/actualites`              | Magazine et Paroles aux Élèves                                                                                                                                                   | Lire, commenter (encadreur)                          |
| Bibliothèque    | `/bibliotheque`            | Les 3 derniers magazines à la une, guides                                                                                                                                        | Lire, télécharger                                    |
| Rejoindre       | `/rejoindre`, `/connexion` | Choix du profil et formulaires                                                                                                                                                   | S'inscrire, se connecter                             |
| Passeport Santé | `/passeport`               | Points, badges, quiz réussis                                                                                                                                                     | Soumettre un témoignage                              |
| Console du club | `/console`                 | Score, élèves, articles et état de modération, agenda                                                                                                                            | Publier, retirer un élève                            |
| Console admin   | `/admin`                   | Modération, suivi des clubs, contenus, badges, chiffres                                                                                                                          | Approuver, rejeter, publier                          |

Le **classement interne d'un club** n'a pas de page publique : il s'affiche dans « Mon espace » (élève), « Mon Club
Santé » (encadreur) et l'espace du président, avec deux onglets Élèves et Encadreurs et la ligne du lecteur mise en
évidence. L'admin le consulte depuis `/admin/points/classements`, avec le registre dans
`/admin/points/registre` (lecture seule, correction et annulation motivées). La clôture d'un semestre (gel,
contrôle des candidats, validation, publication du Top 3) se fait dans `/admin/points/clotures` (spec 037).

Les routes publiques sont rendues côté serveur ; le menu masque ce qui ne concerne pas le rôle.

## États à toujours prévoir

- Chargement
- Vide (aucune donnée)
- Erreur (avec message compréhensible et action possible)
- Succès / confirmation
- En attente de modération et rejeté avec motif (article, témoignage, club)
- Connexion perdue pendant un quiz

## Accessibilité

WCAG 2.2 AA : navigation au clavier, contrastes, textes alternatifs, respect de
`prefers-reduced-motion`. Le chrono (20 secondes pour les jeux, 5 pour la certification) fait partie de l'épreuve ; il reste visible, annoncé
aux lecteurs d'écran, et n'est jamais indiqué par la seule couleur. Le MVP ne propose pas de quiz sans
chrono : à revoir si des élèves en sont exclus.

## Responsive

Mobile d'abord, à partir de 320 px, sur des Android modestes en 3G. Images en WebP avec dimensions,
chargement différé sous le premier écran, vidéos chargées au clic seulement. Cibles tactiles de 44 px
au minimum. Les consoles restent utilisables sur téléphone, la console admin est pensée d'abord pour
un ordinateur.

## Ton et microcopie

Français, tutoiement partout (élèves, encadreurs, admin), sans exception. Phrases courtes et
encourageantes. Les messages d'erreur disent quoi faire ensuite. Les contenus médicaux restent factuels,
sans dramatiser. Aucun texte en anglais visible, y compris les pages d'erreur.

## Statuts des clubs (spec 033)

Une pastille arrondie, toujours accompagnée de son libellé (jamais la couleur seule) :

| Statut            | Libellé           | Classes                         |
| ----------------- | ----------------- | ------------------------------- |
| Sans club         | Référencé         | `bg-mist text-muted-foreground` |
| En constitution   | En constitution   | `bg-sun/30 text-ink`            |
| Actif             | Club actif        | `bg-primary/10 text-primary`    |
| En régularisation | En régularisation | `bg-sun/60 text-ink`            |
| Suspendu          | Suspendu          | `bg-logo-red/10 text-logo-red`  |

Sur la carte publique, un club en régularisation se montre « Club actif ». Les effectifs face aux seuils (3
encadreurs, 21 élèves) se lisent sur des jauges avec `role="progressbar"` dans « Mon Club Santé ».

## Rapports d'activité (spec 038)

- **Encadreur** : « Mes rapports » avec deux onglets, _Mes rapports_ (état, référence, points) et _Rapports du
  club_ (qui l'a reçu, qui l'a consulté). Un bouton « Nouveau rapport » propose les trois modèles : rapport
  d'activité, rapport mensuel, bilan semestriel. Le formulaire est découpé en sections (identification,
  description, participants, justificatifs) et rappelle de n'écrire aucun nom d'élève.
- **Président** : la même liste et le même formulaire depuis l'espace du club, rapport d'activité seulement.
- **États** : badges _Brouillon_ (gris), _Soumis_ (bleu), _À corriger_ (soleil), _Approuvé_ (vert), _Refusé_
  (rouge) ; un doublon approuvé affiche « Lié à RA-… ».
- **Admin** : l'aperçu de modération montre les champs, les justificatifs et, en haut, l'alerte de doublon
  probable ; l'archive « Rapports » filtre et exporte.

## Mot de passe (spec 039)

- **Encadreur** : dans « Mon Club Santé », chaque membre confirmé a « Réinitialiser son mot de passe ». Le dialogue
  demande un motif, puis montre une seule fois le mot de passe provisoire, en gros caractères, avec « Copier » et la
  consigne de le donner à l'élève en main propre.
- **Élève** : après une réinitialisation, un bandeau soleil dans son espace conseille de choisir son propre mot de
  passe ; il n'empêche rien.
- **Connexion** : « Mot de passe oublié ? » mène à une page qui dit à l'élève de s'adresser à un encadreur de son
  club, et propose aux encadreurs et visiteurs de recevoir un lien par e-mail. Le message de confirmation est le même
  que l'adresse existe ou non.

## Cartes numériques (spec 040)

- **Ma carte** : la carte au format carte bancaire, en couleurs du programme, avec le prénom et le nom, le rôle, le
  numéro, l'établissement, le club (ou « Non affilié ») et le QR code. Une pastille dit « Valide » (vert) ou
  « Non valide » (rouge) avec la marche à suivre. Deux boutons : « Télécharger en PDF » et « Télécharger en image ».
  Un avertissement rappelle que la carte porte ton nom : ne la publie pas sur les réseaux.
- **Vérification** (`/carte/<code>`, ouverte par le QR) : une seule carte centrée, très lisible sur un téléphone :
  type, numéro, club, grand statut « Valide » ou « Non valide », heure de la vérification. Aucun nom.
