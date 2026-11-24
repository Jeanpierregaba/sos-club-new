# 052 — Site en anglais et en allemand

## Objectif

Rendre les pages publiques du site lisibles en anglais et en allemand, pour les partenaires, bailleurs et visiteurs
étrangers qui découvrent les Clubs Santé du Togo. Aujourd'hui le bouton « FR / EN » de l'en-tête ne fait rien.

Le PRD classait « autres langues que le français » hors du MVP ; cette spec lève ce point pour l'interface publique
seulement (décision de l'utilisateur, 2026-11-24). Le français reste la langue de référence et la langue par défaut.

## Comportement attendu

1. Le visiteur arrive sur `clubsante.tech` : le site est en français, comme aujourd'hui. Aucune redirection
   automatique selon la langue du navigateur.
2. Dans l'en-tête (et dans le menu mobile), un sélecteur propose **FR / EN / DE**. Choisir « EN » ouvre la même page
   en anglais, à l'adresse préfixée : `/jeux` → `/en/jeux`, `/` → `/en`. « DE » ouvre `/de/jeux`.
3. Sur une page traduite, tout le texte de l'interface est dans la langue choisie : menus, pied de page, titres,
   boutons, textes fixes, formulaires (inscription, connexion, mot de passe oublié), messages de validation et
   d'erreur, page 404, titre et description de la page pour les moteurs de recherche.
4. La langue se garde en naviguant : un lien interne d'une page `/en/...` mène à la page `/en/...` correspondante.
   Un lien partagé `/de/club-sante` s'ouvre directement en allemand.
5. Les contenus saisis par l'équipe ou les clubs (articles, actualités, agenda, témoignages, noms des clubs, quiz,
   questions, livres de la bibliothèque) restent dans leur langue d'origine, le français. Une mention discrète le
   signale dans les pages qui en affichent (« Contenu disponible en français » / « Inhalt auf Französisch »).
6. Les espaces connectés (élève, encadreur, président) et l'espace d'administration restent en français : depuis une
   page `/en/...`, « Mon espace » ou « Se connecter » mène à la page française. Le sélecteur n'y est pas proposé.
7. Les dates et les nombres suivent la langue : « 24 novembre 2026 », « November 24, 2026 », « 24. November 2026 ».
8. Ton : le tutoiement du site devient « you » en anglais et « du » en allemand (registre informel, public jeune).
9. Les traductions sont écrites par Claude puis relues par l'équipe ou un locuteur avant la mise en production ;
   elles vivent dans des fichiers de textes simples à corriger, un par langue.

**Pages traduites** (toutes celles qu'on ouvre sans être connecté) : accueil, Club Santé, les 7 axes, Jeux,
certification, bibliothèque, galerie, magazine, articles (liste et article), agenda (liste et événement), carte des
clubs, fiche d'un club, classements (hall of fame), témoignages, charte, Génie Imhotep (description, inscription,
palmarès, hall of fame), inscription, connexion, activation, mot de passe oublié et nouveau, vérification d'un
certificat, carte de classement partagée, page 404 et page d'erreur.

## Critères d'acceptation

- [ ] Étant donné la page `/`, quand on choisit « EN », alors l'adresse devient `/en` et le titre principal, le menu
      et le pied de page sont en anglais ; avec « DE », `/de` en allemand ; avec « FR », retour à `/`.
- [ ] Étant donné n'importe quelle page publique traduite, quand on change de langue, alors on reste sur la même page
      (mêmes paramètres, par exemple `/en/articles/mon-article` ↔ `/de/articles/mon-article`).
- [ ] Étant donné une page `/en/...`, alors `<html lang="en">` ; `/de/...` → `lang="de"` ; sans préfixe → `lang="fr"`.
- [ ] Chaque page traduite déclare ses versions dans les trois langues (`hreflang` fr, en, de et `x-default` vers le
      français) et a un titre et une description traduits.
- [ ] Un test vérifie que chaque clé de texte existe en français, en anglais et en allemand (aucune clé manquante,
      aucune clé en trop).
- [ ] Étant donné une page `/en/...`, alors chaque lien interne vers une page traduite garde le préfixe `/en`, et
      chaque lien vers un espace connecté ou l'admin pointe vers l'adresse française.
- [ ] Étant donné l'inscription ou la connexion en anglais, quand une erreur survient (champ manquant, identifiants
      faux, trop de tentatives, réseau coupé), alors le message est en anglais.
- [ ] Étant donné une date affichée sur une page traduite, alors elle est écrite selon la langue de la page.
- [ ] Une adresse `/en/<page non traduite>` (par exemple `/en/mon-espace`) redirige vers la page française,
      `/en/<page inconnue>` affiche la 404 en anglais.
- [ ] Le suivi d'activité (spec 051) compte une page vue sous le même gabarit quelle que soit la langue
      (`/en/jeux` et `/jeux` comptent pour `/jeux`).
- [ ] Les pages et parcours existants en français ne changent pas (tests existants verts, adresses inchangées).

## Cas limites et erreurs

- Adresse avec un préfixe inconnu (`/es/jeux`) : traitée comme une page inconnue, 404 en français.
- `/fr/jeux` : redirige vers `/jeux` (le français n'a pas de préfixe, une seule adresse par page).
- Texte d'interface sans traduction (oubli) : impossible à livrer, le test des clés échoue ; à l'exécution, repli sur
  le français plutôt qu'une clé brute.
- Message d'erreur de l'API inconnu du site sur une page traduite : affiché tel quel (en français) plutôt que rien.
- Textes plus longs en allemand : les boutons, menus et cartes ne débordent pas, sur téléphone compris.
- Liens partagés existants (sans préfixe) : inchangés, toujours en français.
- Élève connecté qui navigue sur `/en/...` : les pages publiques sont en anglais, son espace reste en français.
- Page servie pendant la maintenance : la page de maintenance reste en français (hors périmètre).
- Contenus avec nom d'élève : aucun changement des règles de `docs/RULES.md` (pseudonyme et club seulement).

## Hors périmètre

- Traduction des contenus en base (articles, actualités, agenda, quiz, 1 000 questions, livres, témoignages,
  noms des clubs et des établissements, catégories et axes saisis en base).
- Espaces connectés (élève, encadreur, président, Génie Imhotep connecté) et administration.
- E-mails envoyés par la plateforme (codes, activation), certificats PDF, cartes partagées, page de maintenance.
- Choix automatique de la langue selon le navigateur, mémorisation de la langue entre deux visites.
- Autres langues (éwé, kabiyè…) : la mise en place doit permettre de les ajouter plus tard sans refonte.

## Questions ouvertes

Aucune : périmètre (pages publiques), traducteur (Claude puis relecture) et adresses (préfixes `/en`, `/de`)
tranchés par l'utilisateur le 2026-11-24.
