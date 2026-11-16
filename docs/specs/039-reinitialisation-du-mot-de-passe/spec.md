# 039 — Réinitialisation du mot de passe (Q4)

Sources : PRD Q4 ; spec 017 (réinitialisation par l'admin) ; spec 020 (hors périmètre : « Réinitialisation du mot de
passe d'un élève par un encadreur rattaché, spec à part ») ; spec 030 (code e-mail des visiteurs) ; spec 033 (un
encadreur sur un seul club, « Mon Club Santé ») ; `docs/SECURITY.md` (réinitialisations journalisées, ligne 20) ;
la page de connexion, qui dit déjà « Mot de passe oublié ? Demande à un encadreur de ton club de le réinitialiser ».

Décisions du porteur du projet (2026-11-16) :

- un encadreur ne réinitialise que les **membres confirmés** de son club (affiliation active) ;
- après une réinitialisation, changer le mot de passe provisoire est **conseillé, pas obligatoire** ;
- garde-fous : **10 réinitialisations par encadreur et par jour**, un **motif** court obligatoire, l'action au
  **journal d'audit** et une **notification** à l'élève qui dit qui l'a faite ;
- un **« mot de passe oublié » par e-mail** entre dans cette spec, pour les comptes dont l'adresse est fiable.

## Objectif

Un élève n'a souvent pas d'e-mail (Q4) : quand il oublie son mot de passe, seule l'équipe nationale peut aujourd'hui
le réinitialiser, ce qui ne tient pas à l'échelle du pays. Cette spec donne ce pouvoir à l'encadreur de son club,
encadré et tracé. Elle ajoute aussi un « mot de passe oublié » par e-mail pour les encadreurs et les visiteurs, qui
dépendent aujourd'hui de l'équipe.

## Comportement attendu

### 1. Par l'encadreur, pour un élève de son club

1. Dans « Mon Club Santé », chaque membre confirmé a un bouton **Réinitialiser son mot de passe**.
2. L'encadreur saisit un **motif** (10 à 200 caractères, par exemple « Mot de passe oublié, demandé en classe ») et
   confirme.
3. L'API vérifie, sur la ressource demandée (ADR-0003) :
   - l'encadreur est vérifié, actif et rattaché à un club en service ;
   - l'élève a une affiliation **active** à ce club et un compte actif (pas suspendu ni supprimé) ;
   - l'encadreur n'a pas déjà fait 10 réinitialisations dans les dernières 24 heures.
4. L'API crée un **mot de passe provisoire** (12 caractères sans caractères ambigus, comme la spec 017), coupe toutes
   les sessions de l'élève et renvoie le mot de passe **une seule fois** à l'écran de l'encadreur, avec la consigne
   de le donner à l'élève en main propre. Il n'est écrit nulle part ailleurs : ni au journal, ni dans une
   notification, ni dans un e-mail.
5. L'action est **journalisée** : auteur, élève, club, motif, date, adresse IP.
6. L'élève reçoit une **notification** dans son espace : « Ton mot de passe a été réinitialisé par <prénom nom de
   l'encadreur> le <date> ». Il la lit après s'être connecté avec le mot de passe provisoire.
7. À la connexion avec un mot de passe provisoire, un **bandeau conseille** de le changer, avec un lien vers le
   changement de mot de passe ; il n'est pas bloquant. Le bandeau disparaît dès que l'élève a choisi son propre mot
   de passe.

### 2. Par l'admin (spec 017, ajusté)

La réinitialisation par l'admin reste la même (droit `inscrits:modifier`, motif, journal). Elle marque aussi le mot
de passe comme provisoire (même bandeau) et envoie la même notification à l'élève (« par l'équipe des Clubs
Santé », sans nom de collaborateur).

### 3. « Mot de passe oublié » par e-mail

1. La page de connexion propose **Mot de passe oublié ?** :
   - un élève est invité à demander à un encadreur de son club (le texte actuel) ;
   - un encadreur ou un visiteur saisit son adresse e-mail.
2. Un lien est envoyé seulement à une **adresse fiable** :
   - un **visiteur** dont l'adresse est confirmée par le code de la spec 030 ;
   - un **encadreur activé** par l'équipe : son adresse a servi à son activation.
     Jamais à un élève (son adresse est facultative et non vérifiée), ni à un collaborateur de l'admin (double
     authentification, réinitialisation par le super-administrateur), ni à un compte suspendu.
3. La réponse est **toujours la même**, que le compte existe ou non : « Si cette adresse correspond à un compte, un
   lien vient d'y être envoyé. »
4. Le lien est **à usage unique**, valable **30 minutes** ; il mène à une page où la personne choisit un nouveau mot
   de passe (règles de la spec 001). Un nouveau lien annule le précédent.
5. Une fois le mot de passe changé, toutes les sessions sont coupées, l'action est journalisée, et la personne est
   invitée à se connecter.
6. Garde-fous : 3 demandes par adresse et par heure, et 20 demandes par adresse IP sur 15 minutes ;
   le jeton est stocké sous forme d'empreinte, jamais en clair.

## Critères d'acceptation

### Par l'encadreur

- [x] Étant donné un encadreur vérifié et un membre confirmé de son club, quand il réinitialise avec un motif, alors
      il reçoit un mot de passe provisoire qui ouvre une session de l'élève, les anciennes sessions de l'élève sont
      coupées et l'ancien mot de passe ne marche plus.
- [x] Le mot de passe provisoire n'apparaît ni au journal, ni dans la notification, ni dans une réponse ultérieure.
- [x] Étant donné un élève en attente de confirmation, d'un autre club, suspendu, ou un encadreur, alors la
      réinitialisation est refusée (404 pour un élève hors du club, comme s'il n'existait pas).
- [x] Étant donné un encadreur non vérifié, sans club, ou dont le club n'est pas en service, alors c'est refusé.
- [x] Un élève, un visiteur ou un président ne peut pas réinitialiser un autre compte.
- [x] Un motif de moins de 10 caractères est refusé.
- [x] La 11e réinitialisation d'un encadreur sur 24 heures est refusée (429), même sous requêtes simultanées.
- [x] Chaque réinitialisation est journalisée avec l'encadreur, l'élève, le club et le motif.
- [x] L'élève reçoit une notification qui nomme l'encadreur ; un bandeau lui conseille de changer son mot de passe
      jusqu'à ce qu'il le fasse.

### Par l'admin

- [x] Une réinitialisation par l'admin marque le mot de passe comme provisoire et notifie l'élève, sans nommer le
      collaborateur.

### Par e-mail

- [x] Étant donné un encadreur activé ou un visiteur confirmé, quand il demande un lien, alors il reçoit un e-mail
      avec un lien valable 30 minutes.
- [x] Étant donné une adresse inconnue, d'un élève, d'un collaborateur, d'un compte suspendu ou d'un visiteur non
      confirmé, alors aucun e-mail n'est envoyé et la réponse est la même que pour un compte réel.
- [x] Un lien utilisé, expiré ou remplacé par un plus récent est refusé.
- [x] Après le changement, les sessions du compte sont coupées et l'action est journalisée.
- [x] La 4e demande pour la même adresse dans l'heure n'envoie rien.
- [x] Le jeton n'est stocké qu'en empreinte.

## Cas limites et erreurs

- **Encadreur qui réinitialise puis perd son rattachement** : les réinitialisations passées restent au journal ; il
  n'en fait plus d'autres.
- **Deux encadreurs du club réinitialisent le même élève en même temps** : chacune est valable et journalisée ; seul
  le dernier mot de passe marche. Les deux encadreurs voient un mot de passe : l'élève est invité à le changer.
- **Élève qui change son mot de passe** : le bandeau disparaît ; une nouvelle réinitialisation le fait revenir.
- **Élève qui n'a pas pu se connecter** : rien ne change tant qu'il n'utilise pas le provisoire ; l'encadreur peut
  réinitialiser de nouveau (dans le plafond).
- **Adresse e-mail en majuscules ou avec des espaces** : normalisée avant la recherche.
- **SMTP indisponible** : la réponse reste la même ; l'échec est consigné dans les logs, sans l'adresse en clair.
- **Lien ouvert deux fois** : la page de choix fonctionne tant que le mot de passe n'a pas été changé ; le second
  envoi du formulaire est refusé.
- **Encadreur suspendu après la demande de lien** : le lien est refusé au moment du changement.

## Hors périmètre

- La réinitialisation par le **président** du club : c'est un élève.
- Le changement obligatoire du mot de passe provisoire (décision du 2026-11-16 : conseillé seulement).
- La récupération par SMS ou WhatsApp.
- Le « mot de passe oublié » des collaborateurs de l'admin : le super-administrateur le gère (spec 015).
- L'envoi du mot de passe provisoire à l'élève par l'application : l'encadreur le lui donne en main propre.

## Questions ouvertes

Aucune : les quatre questions ont été tranchées le 2026-11-16.
