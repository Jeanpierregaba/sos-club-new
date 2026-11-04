# 018 — Compte encadreur

## Objectif

Roadmap R3, phase 1. Un enseignant ou un accompagnateur crée lui-même son compte encadreur depuis le site.
Son compte reste « en attente » jusqu'à ce qu'un collaborateur vérifie ses informations et l'active. À
l'activation, il reçoit une seule fois les points de bienvenue encadreur (PRD, critère « Un encadreur crée
son compte » ; [CDC encadreur](../../cdc/encadreur.md), § 2 ; Q16, Q22).

Cette spec prépare R4 et R5 : un encadreur actif pourra confirmer le président d'un club (Q19) puis
demander ses rattachements. Elle ne crée ni club ni rattachement.

## Comportement attendu

**Inscription (visiteur)**

1. Sur `/inscription`, le visiteur choisit son profil : « Je suis élève » (le formulaire de la spec 017)
   ou « Je suis encadreur ». Le lien direct `/inscription?profil=encadreur` ouvre le second.
2. Il remplit le formulaire encadreur :
   - prénom et nom : visibles de l'admin, et plus tard de ses élèves et de son club ;
   - e-mail : obligatoire, il sert à la connexion et aux avis ;
   - téléphone : facultatif, pour que l'équipe le joigne pendant la vérification ;
   - identifiant de connexion et mot de passe ;
   - établissement : la même recherche que pour les élèves, avec la même possibilité de proposer un
     établissement absent ;
   - fonction, dans une liste : enseignant, responsable pédagogique ou administratif, infirmier ou agent de
     santé scolaire, accompagnateur ou animateur, autre (à préciser).
3. Il coche deux cases obligatoires : la charte des Clubs Santé, et le consentement au traitement de ses
   données pour la vérification de son compte.
4. Il valide. Il est connecté et arrive sur son espace, « en attente de vérification ».

**Espace de l'encadreur (`/mon-espace`)**

- **En attente** : un message explique que l'équipe vérifie son inscription, avec la date de sa demande.
  Il voit et corrige son profil (téléphone, établissement, fonction) et change son mot de passe.
- **Refusé** : il voit le motif. Il peut corriger son profil et renvoyer sa demande, qui repasse en attente.
- **Actif** : ses points du semestre et son total, ses dernières lignes, son profil et son établissement.
  Un encart annonce que les clubs et les rattachements arrivent bientôt.

**Espace admin**

- **Encadreurs à vérifier** (menu admin) : une file, des plus anciennes demandes aux plus récentes, avec le
  nom, la fonction, l'établissement et sa DRE, l'e-mail, le téléphone et la date de la demande. Un
  compteur apparaît dans le menu et sur le tableau de bord.
- **Activer** : le compte passe « actif » et reçoit les points de bienvenue, dans la même transaction.
- **Refuser** : avec un motif obligatoire, que l'encadreur lit dans son espace.
- **Fiche d'un inscrit encadreur** : fonction, établissement, état de la vérification, qui a décidé et
  quand, et ses points.
- Chaque décision est inscrite au journal d'audit. Si l'envoi d'e-mails est configuré, l'encadreur reçoit
  un e-mail à l'activation ou au refus.

## Critères d'acceptation

- [x] Étant donné les inscriptions ouvertes, quand un visiteur envoie un formulaire encadreur valide, alors
      un compte `encadreur` est créé « en attente », il est connecté, et aucun point n'est crédité.
- [x] Étant donné un e-mail ou un identifiant déjà pris, quand le visiteur s'inscrit, alors l'API répond
      409 avec le champ concerné, et rien n'est créé.
- [x] Étant donné les inscriptions fermées, quand un visiteur s'inscrit comme encadreur, alors l'API
      répond 403. Le même réglage `INSCRIPTIONS_OUVERTES` vaut pour les deux profils.
- [x] Étant donné un encadreur en attente, quand il appelle une route réservée aux encadreurs actifs,
      alors l'API répond 403 (dépendance `encadreur_actif`, que R4 et R5 utiliseront).
- [x] Étant donné un encadreur en attente, quand un collaborateur autorisé l'active, alors son compte
      est actif et une seule ligne `encadreur.bienvenue` est écrite, au montant du barème.
- [x] Étant donné deux activations simultanées du même encadreur, alors une seule réussit et une seule
      ligne de points existe.
- [x] Étant donné un encadreur refusé puis réactivé après correction, alors il n'a toujours qu'une seule
      ligne de bienvenue.
- [x] Étant donné un refus sans motif, alors l'API répond 422.
- [x] Étant donné un collaborateur sans le droit requis, ou hors de la DRE de l'établissement, quand il
      lit la file ou décide, alors l'API répond 403 (ou ne lui montre pas la demande).
- [x] Étant donné un encadreur refusé, quand il renvoie sa demande, alors elle repasse en attente, et le
      motif précédent reste au journal.
- [x] La file, l'activation et le refus apparaissent au journal d'audit avec l'auteur et le motif.
- [x] Le site affiche le choix du profil, le formulaire, les trois états de l'espace et la file admin,
      lisibles sur téléphone.

## Cas limites et erreurs

- **Inscription en double** : même e-mail ou identifiant, refusée (409). Même personne avec deux e-mails :
  l'admin la repère dans la file (même nom, même établissement) et refuse le doublon.
- **Établissement proposé** : l'activation reste possible. L'admin traite la proposition dans le
  référentiel, comme pour un élève.
- **Établissement désactivé ou remplacé** entre la demande et la décision : la fiche suit le remplacement
  (spec 017) ; la file affiche l'établissement actuel.
- **Encadreur suspendu** (statut du compte, spec 015) : la suspension prime, quel que soit l'état de la
  vérification. L'activation d'un compte suspendu est refusée (409).
- **Décision sur une demande déjà traitée** : 409, avec l'état actuel.
- **Pas de semestre en cours** à l'activation : la ligne de bienvenue est écrite sans semestre, comme pour
  un élève (ADR-0004), et compte dans le total historique.
- **Action `encadreur.bienvenue` désactivée** dans le barème : l'activation réussit sans ligne de points.
  La réactiver plus tard ne crédite pas les comptes déjà activés.
- **Limite d'inscriptions** : la même limite par adresse que pour les élèves, tous profils confondus.
- **Comptes encadreurs créés avant cette spec** (ligne de commande, démo) : ils n'ont ni établissement ni
  fonction. La ligne de commande ne crée plus d'encadreur ; la démo crée un encadreur actif avec son profil.

## Hors périmètre

- **Club demandé** : reporté à R5 (rattachements), puisque les clubs n'existent qu'à partir de R4. Le CDC
  le prévoit à l'inscription ; ce sera une demande de rattachement depuis l'espace actif.
- Justificatif téléversé (carte professionnelle, attestation) : pas de stockage de fichiers privés avant
  les rapports d'activités.
- Connexion par téléphone, et vérification de l'e-mail par un lien.
- Changement d'établissement soumis à validation une fois actif : l'établissement est libre tant qu'aucun
  rattachement n'existe ; R5 fixera la règle.
- Tableau de bord complet de l'encadreur (CDC § 3), certification, carte encadreur, classements.

## Questions ouvertes

Aucune. Tranchées le 2026-11-04 :

1. Connexion : identifiant et mot de passe, e-mail obligatoire.
2. Vérification : sur les informations saisies ; l'équipe peut appeler le téléphone indiqué.
3. Activation : au niveau national ou par un collaborateur de la DRE de l'établissement (comme Q18). Le plan
   en fait un module de droits `encadreurs`, car `inscrits` reste national.
4. Points : `encadreur.bienvenue` passe en service à 100 points, montant réglable dans le barème.
