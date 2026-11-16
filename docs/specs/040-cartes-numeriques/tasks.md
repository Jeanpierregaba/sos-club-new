# 040 — Tâches

Ordonnées. Chaque tâche est petite, testable et committable seule. Les parties critiques (droits, données publiques,
unicité) sont écrites en TDD : les tests précèdent le code.

## Socle

- [x] 1. Documents :
  - `TASKS.md` : spec 040 en cours, spec, plan et tâches validés ;
  - `docs/SECURITY.md` : code du QR secret, exclu des exports et du journal ; page de vérification publique ;
  - `docs/DESIGN.md` : parcours « Ma carte » et page de vérification ;
  - `docs/PRD.md` : R15 traité par la spec 040.
- [x] 2. Migration et modèle :
  - table `carte` (numéro et code uniques, `utilisateur_id` unique en `SET NULL`, suspension avec CHECK) ;
  - séquence `carte_numero_seq` ;
  - délivrance aux élèves puis aux encadreurs actifs existants, code en SQL natif ;
  - test d'aller-retour de la migration et de la délivrance (encadreur en attente : aucune carte).

## Délivrance et état

- [x] 3. Tests puis code de `cartes.service.delivrer` et de son branchement :
  - une inscription d'élève crée une carte « Non affilié » ;
  - l'activation d'un encadreur crée la sienne, et le seed commun suit les mêmes règles ;
  - idempotente : un second appel ne crée rien ;
  - unicité du numéro et du code sous 20 délivrances simultanées ;
  - format `CS-M-` et `CS-E-`, code de 32 caractères.
- [x] 4. Tests puis code de `etat_de` :
  - validité, cause, club, rôle et établissement selon le tableau du plan ;
  - affiliation confirmée, puis retirée ;
  - présidence et passation ;
  - compte suspendu, puis réactivé ;
  - encadreur sans rattachement, rattaché, puis retiré ;
  - suspension par l'équipe qui tient après la réactivation du compte ;
  - compte supprimé (`utilisateur_id` nul).

## Espace

- [x] 5. Tests puis code de `GET /api/cartes/moi` :
  - le titulaire ne voit que sa carte ;
  - 404 pour un visiteur, un collaborateur ou un encadreur pas encore vérifié ;
  - `no-store`.
- [x] 6. Rendu PDF et PNG (`cartes/rendu.py`), après vérification de l'API de segno avec Context7 :
  - mise en page commune au format carte, polices Noto Sans, coupure des noms longs ;
  - routes `moi.pdf` et `moi.png`, 409 si la carte n'est pas valide ;
  - tests : types MIME, `no-store`, le PDF contient le numéro, le prénom et l'adresse de vérification, taille du PNG ;
  - nom avec lettres éwé.

## Vérification publique

- [x] 7. Tests puis code de `GET /api/cartes/verification/{code}` :
  - clés exactes de la réponse, sans nom, pseudonyme ni établissement ;
  - carte non valide sans motif ;
  - code inconnu, mal formé, ou numéro à la place du code : 404 ;
  - `no-store` et `X-Robots-Tag: noindex` ;
  - limite par adresse IP (429), avec une clé non déclenchable par une saisie de connexion.

## Admin

- [x] 8. Tests puis code de la carte dans la fiche « Inscrits » et des routes `carte/suspendre` et `carte/reactiver` :
  - `InscritDetail.carte` avec l'historique tiré du journal ;
  - droit `inscrits:modifier` et double authentification ;
  - motif de 10 à 200 caractères ;
  - 409 si déjà suspendue, ou si elle ne l'est pas ;
  - journal, et notification au titulaire sans nom de collaborateur ;
  - le code n'apparaît ni au journal, ni dans les exports.

## Site

- [ ] 9. Types de l'API régénérés et fonctions du client. Page « Ma carte » (`/ma-carte`) avec `ApercuCarte` :
  - aperçu, statut, marche à suivre si elle n'est pas valide ;
  - téléchargements PDF et image, avertissement sur le nom ;
  - encadreur sans rattachement ;
  - entrée de navigation, numéro et lien sur la `CarteMembre` du tableau de bord, raccourci de l'`EspaceEncadreur` ;
  - tests des composants.
- [ ] 10. Page publique `/carte/$code` (SSR, `noindex`) : valide, non valide, inconnue ; tests.
- [ ] 11. Bloc carte de la fiche admin (`CarteInscrit`) avec `DialogueMotif` pour suspendre et réactiver, libellés
      du journal dans `src/lib/admin.ts` ; tests.

## Fin

- [ ] 12. Lint, typecheck, tests backend et site. Vérification dans le navigateur :
  - page publique ;
  - PDF imprimé au format carte, et PNG à la taille d'un téléphone, avec capture jointe ;
  - mise à jour de `TASKS.md`.
- [ ] Vérifier tous les critères d'acceptation de `spec.md`.
- [ ] Relecture par le sous-agent `reviewer`.
