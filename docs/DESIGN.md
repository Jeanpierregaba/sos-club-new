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

| Écran           | Route visée                | But et contenu                                          | Actions                            |
| --------------- | -------------------------- | ------------------------------------------------------- | ---------------------------------- |
| Accueil         | `/`                        | Existant, à brancher sur les vraies données             | Aller aux quiz, carte, inscription |
| Club Santé      | `/club-sante`              | Vision, mission, slogans, mot du promoteur, partenaires | Lire                               |
| Carte des clubs | `/clubs`                   | Carte par région et palmarès                            | Filtrer, ouvrir un club            |
| Page d'un club  | `/clubs/:id`               | Score, articles, événements, sans liste d'élèves        | Lire                               |
| S'informer      | `/videos`                  | Capsules par axe                                        | Filtrer, lire                      |
| Hall of Fame    | `/hall-of-fame`            | Top 3 par région : clubs, élèves, encadreurs            | Changer de région et de catégorie  |
| Agenda          | `/agenda`                  | Calendrier et liste                                     | Filtrer par région, club, type     |
| Gamification    | `/quiz`, `/quiz/:id`       | Meilleurs scores, quiz par thème, partie chronométrée   | Jouer, reprendre                   |
| Actualités      | `/actualites`              | Magazine et Paroles aux Élèves                          | Lire, commenter (encadreur)        |
| Bibliothèque    | `/bibliotheque`            | Les 3 derniers magazines à la une, guides               | Lire, télécharger                  |
| Rejoindre       | `/rejoindre`, `/connexion` | Choix du profil et formulaires                          | S'inscrire, se connecter           |
| Passeport Santé | `/passeport`               | Points, badges, quiz réussis                            | Soumettre un témoignage            |
| Console du club | `/console`                 | Score, élèves, articles et état de modération, agenda   | Publier, retirer un élève          |
| Console admin   | `/admin`                   | Modération, clubs à valider, contenus, badges, chiffres | Approuver, rejeter, publier        |

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
`prefers-reduced-motion`. Le chrono de 5 secondes fait partie de l'épreuve ; il reste visible, annoncé
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
