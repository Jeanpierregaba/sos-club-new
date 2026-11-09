# 028 — Tâches

- [x] 1. Tests du contrôle des PDF (`test_pdf.py`, PDF construits dans les tests : sain, JavaScript, action de
      lancement, fichier joint, chiffré, tronqué, pas un PDF), puis `pypdf`, `fichiers/pdf.py`, clés `.pdf` et
      lecture en flux du stockage, limites de taille, Caddy à 25MB.
- [x] 2. Modèle `Ressource`, migration `bibliotheque`, module `bibliotheque` au catalogue.
- [x] 3. Tests de la gestion (`test_bibliotheque_gestion.py`) : droits, 2FA, deux personnes, validateur, états,
      dépôt et remplacement des fichiers, suppression, journal, notifications, courses ; puis `gestion.py` et
      `router_gestion.py`.
- [x] 4. Tests de la bibliothèque publique (`test_bibliotheque_public.py`) : liste, filtres, « À la Une »,
      fichier et couverture servis ou 404, en-têtes, compteur ; puis `public.py` et `router.py`.
- [x] 5. `seed_dev` : ressources « Contenu de test » ; types de l'API régénérés.
- [ ] 6. Site, public : client, `/bibliotheque` sur les vraies données, carrousel, filtres, état vide.
- [ ] 7. Site, admin : liste, fiche, dépôt des fichiers, décisions ; entrée « Bibliothèque » du menu.
- [ ] 8. Docs : ADR-0010, ARCHITECTURE, SECURITY, TASKS.
- [ ] Vérifier tous les critères d'acceptation de spec.md
- [ ] Relecture par le sous-agent reviewer
