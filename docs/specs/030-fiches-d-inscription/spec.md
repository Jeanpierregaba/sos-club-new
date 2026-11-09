# 030 — Fiches d'inscription : élève, encadreur et visiteur

## Objectif

Aligner l'inscription en ligne sur les fiches réelles du réseau, et ouvrir le compte visiteur (R19, avancé) :

- **Élève** : la fiche d'adhésion papier « Club Santé SOS Docteur TV » est reprise en entier. Elle sert à
  l'équipe nationale, notamment au soutien des membres actifs dans l'octroi des bourses.
- **Encadreur** : téléphone obligatoire et discipline ; région et ville déduites de l'établissement.
- **Visiteur** (grand public, étudiant, parent, professionnel) : un compte léger confirmé par un code reçu par
  e-mail, pour jouer aux quiz « jeux » sans points.
- **E-mails** : l'envoi SMTP est mis en service en préproduction et en production, avec un gabarit commun aux
  couleurs du site (HTML + texte brut).

Décisions de l'utilisateur (2026-11-09) : fiche papier complète ; visiteur limité aux quiz jeux, sans points ni
badges ni certificat (le PRD reste vrai) ; code à 6 chiffres par e-mail ; région et ville de l'encadreur déduites.

## Comportement attendu

### Fiche élève

1. Le formulaire élève garde l'existant (prénom, nom, pseudonyme, identifiant, mot de passe, e-mail facultatif,
   classe, établissement choisi en cascade DRE → IESG → établissement ou proposé, charte, accord du parent).
2. Il ajoute, en étapes courtes pour rester utilisable sur téléphone :
   - **Établissement** : n° d'adhésion dans l'établissement (facultatif), préfecture, commune, canton (texte).
   - **Élève** : sexe, date de naissance, lieu de naissance, contact (téléphone, facultatif).
   - **Parents** : père (nom, profession, contact) et mère (nom, profession, contact), chacun facultatif ;
     **un parent ou tuteur responsable** (nom et contact) obligatoire : il remplace la signature du parent.
   - **Club** : axe(s) choisi(s) parmi les 7 axes actifs (au moins un, trois au plus).
   - **Parcours antérieur** : jusqu'à deux lignes (année scolaire, établissement, IESG), facultatives.
   - **Réseaux sociaux souscrits** : Facebook, TikTok, Instagram, autre (texte) ; facultatif.
   - **Engagement** : case « Je m'engage à mener les activités du Club Santé SOS Docteur TV de mon établissement ».
3. L'année scolaire et la date de la fiche sont posées par le serveur (année scolaire en cours, date d'inscription).
4. Un élève déjà inscrit sans fiche voit dans son espace « Complète ta fiche d'adhésion ». Rien n'est bloqué.
5. L'élève relit et corrige sa fiche depuis son espace (sauf année scolaire et date).
6. **Qui lit la fiche** : l'élève lui-même ; les collaborateurs ayant le droit « fiches élèves : consulter », dans
   leur périmètre (national, ou DRE de l'établissement), sous double authentification, chaque consultation
   journalisée. Ni les encadreurs, ni le président du club, ni aucune page publique. L'élève reste public par son
   seul pseudonyme (RULES).

### Fiche encadreur

7. Le téléphone (WhatsApp) devient obligatoire à l'inscription ; un champ « Discipline / matière ou spécialité »
   (facultatif, 100 caractères) s'ajoute.
8. L'établissement se choisit en cascade DRE → IESG → établissement (déjà le cas). La région et la ville du lycée
   sont affichées, déduites de la DRE et de la localité de l'établissement, jamais saisies.
9. Un encadreur déjà inscrit sans téléphone voit « Ajoute ton téléphone » dans son espace ; il n'est pas bloqué.
10. La file de vérification de l'équipe montre aussi la discipline.

### Compte visiteur

11. L'onglet « Particulier / visiteur » de `/inscription` (aujourd'hui « arrive bientôt ») ouvre le formulaire :
    nom, prénoms, téléphone / WhatsApp, ville, e-mail (obligatoires) ; région (5 régions du Togo ou « Hors du
    Togo »), sexe, statut / profession (facultatifs) ; mot de passe ; case d'accord avec la charte et le
    traitement des données, et « J'ai 18 ans ou plus, ou l'accord de mon parent ou tuteur ».
12. À l'envoi, le compte est créé **non confirmé** et un code à 6 chiffres part par e-mail. La page demande le
    code. Le code est valable 15 minutes ; 5 essais faux l'annulent ; un nouveau code peut être demandé au plus
    une fois par minute et cinq fois par heure.
13. Le bon code confirme l'adresse et ouvre la session. Un visiteur qui se connecte (e-mail + mot de passe) sans
    avoir confirmé est renvoyé vers la saisie du code, avec un nouveau code envoyé.
14. Un visiteur confirmé joue aux quiz du parcours « jeux » sans gagner de points, comme le prévoit le PRD : ni
    points, ni classement, ni badge, ni certificat, ni club. Il voit un espace minimal (son profil, ses parties).
15. Un compte visiteur jamais confirmé est effacé au bout de 7 jours, ce qui libère l'adresse.
16. L'équipe voit les visiteurs dans « Inscrits » (filtre par profil), sans droit nouveau.
17. Les textes de la page visiteur tutoient et ne promettent plus ni badges ni certification.

### E-mails

18. Un module commun envoie des e-mails en HTML et en texte brut, avec un gabarit aux couleurs du site (logo,
    titre bicolore, bouton vert, pied de page AIMES-AFRIQUE / SOS Docteur TV). L'invitation des collaborateurs
    et le code du visiteur l'utilisent.
19. En local ou en préproduction sans SMTP, le code est renvoyé par l'API (`code_de_test`) comme l'est déjà le
    lien d'invitation ; en production sans SMTP, l'inscription visiteur est refusée (503) plutôt que de créer un
    compte inutilisable.
20. Aucune adresse, aucun code et aucun contenu d'e-mail n'est écrit dans les journaux.

## Critères d'acceptation

- [ ] Une inscription élève complète enregistre le compte, le profil et la fiche dans la même transaction ; sans
      sexe, date ou lieu de naissance, responsable (nom + contact), axe ou engagement, elle est refusée (422).
- [ ] Une date de naissance future ou donnant moins de 8 ans ou plus de 30 ans est refusée.
- [ ] Un axe inactif ou inconnu, ou plus de 3 axes, est refusé.
- [ ] Les téléphones de la fiche sont normalisés comme celui de l'encadreur (8 à 15 chiffres, « + » permis).
- [ ] L'élève lit et corrige sa fiche ; un autre élève, un encadreur ou un visiteur reçoit 403 ou 404.
- [ ] Un collaborateur sans le droit « fiches élèves : consulter », hors de son périmètre ou sans double
      authentification ne lit pas la fiche ; une lecture autorisée est journalisée.
- [ ] Aucune route publique ni aucun export existant ne contient un champ de la fiche.
- [ ] Un élève existant sans fiche voit l'invitation à la compléter ; sa fiche complétée la fait disparaître.
- [ ] Une inscription encadreur sans téléphone est refusée ; la discipline est enregistrée et visible dans la file.
- [ ] La région et la ville affichées pour un encadreur viennent de la DRE et de la localité de l'établissement.
- [ ] Une inscription visiteur crée un compte non confirmé et envoie un code ; aucun quiz n'est jouable avant.
- [ ] Le bon code confirme et ouvre la session ; un code expiré, faux 5 fois, ou d'un autre compte est refusé.
- [ ] Le renvoi d'un code respecte 1 par minute et 5 par heure.
- [ ] Un visiteur confirmé termine une partie « jeux » sans aucune ligne dans `mouvement_points`, et ne peut ni
      ouvrir la certification (403) ni demander une affiliation à un club.
- [ ] Les comptes visiteurs non confirmés de plus de 7 jours sont effacés par la purge.
- [ ] Inscriptions fermées (`INSCRIPTIONS_OUVERTES` faux) : le formulaire visiteur est fermé comme les autres.
- [ ] L'e-mail envoyé contient une partie HTML et une partie texte, sans contenu dans les journaux ; en production
      sans SMTP, l'inscription visiteur répond 503 sans créer de compte.

## Cas limites et erreurs

- **Doublons** : e-mail déjà pris (élève, encadreur ou visiteur) → 409 « Cet email est déjà pris. » ; un visiteur
  non confirmé de plus de 7 jours ne bloque plus l'adresse.
- **Codes** : comparaison en temps constant ; seul le dernier code envoyé est valable ; code stocké sous forme
  d'empreinte, jamais en clair.
- **Échec d'envoi SMTP** : le compte n'est pas créé (production) ou le visiteur peut redemander un code.
- **Caractères** : noms éwé et kabiyè acceptés (ɔ, ɛ, ŋ, ɖ, ʋ…), espaces normalisés.
- **Fiche partielle d'un ancien élève** : enregistrable champ par champ ; les champs obligatoires ne le deviennent
  qu'à la première validation complète.
- **Changement d'établissement** : la préfecture, la commune et le canton restent ceux saisis ; l'élève les corrige.
- **Rafales** : la limite d'inscriptions par adresse IP s'applique aussi aux visiteurs.
- **Concurrence** : deux confirmations simultanées du même code n'ouvrent qu'une confirmation.

## Hors périmètre

- Signature manuscrite et cachet de l'établissement : remplacés par les cases cochées et la vérification de
  l'encadreur ; la fiche papier peut rester au club.
- Accès des encadreurs ou du président aux fiches élèves, et leur export : à décider plus tard (ADR si oui).
- Gestion des bourses.
- Commentaires des visiteurs (PRD) : spec ultérieure.
- Badges, certificat, points ou classement pour les visiteurs.
- Changement d'adresse e-mail d'un visiteur, connexion par téléphone.
- Choix du fournisseur SMTP : le plan propose, l'utilisateur fournit les accès (jamais dans le dépôt).

## Questions ouvertes

- Données réelles : la fiche complète (date et lieu de naissance, parents, professions, contacts) doit figurer dans
  la déclaration à l'IPDCP (Q9) avant toute donnée réelle. SECURITY.md sera mis à jour en conséquence. À confirmer
  par le juriste (Q8).
