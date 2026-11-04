import type { AdminMoi, CollaborateurResume, Droit } from "@/lib/api/client";

export const cleDroit = (d: Droit) => `${d.module}:${d.action}`;

// Affichage seulement : l'API vérifie chaque droit de son côté (ADR-0008).
export function peut(admin: AdminMoi, module: string, action: Droit["action"]): boolean {
  return admin.super_admin || admin.droits.some((d) => d.module === module && d.action === action);
}

export const peutVoirInscrits = (admin: AdminMoi) =>
  peut(admin, "inscrits", "consulter") && admin.perimetre_dre === null;

export const peutExporter = (admin: AdminMoi) =>
  peut(admin, "statistiques", "exporter") ||
  (peut(admin, "inscrits", "exporter") && admin.perimetre_dre === null);

export const STATUTS_COLLABORATEUR: Record<
  CollaborateurResume["statut"],
  { libelle: string; classe: string }
> = {
  invitation_envoyee: { libelle: "Invitation envoyée", classe: "bg-sky/15 text-sky" },
  invitation_expiree: {
    libelle: "Invitation expirée ou annulée",
    classe: "bg-tangerine/15 text-tangerine",
  },
  actif: {
    libelle: "Actif",
    classe:
      "bg-[color-mix(in_oklch,var(--primary)_14%,white)] text-[color-mix(in_oklch,var(--primary)_70%,black)]",
  },
  suspendu: { libelle: "Suspendu", classe: "bg-sun/30 text-ink" },
  revoque: { libelle: "Révoqué", classe: "bg-logo-red/10 text-logo-red" },
};

export const STATUTS_COMPTE = {
  actif: STATUTS_COLLABORATEUR.actif,
  suspendu: STATUTS_COLLABORATEUR.suspendu,
  revoque: STATUTS_COLLABORATEUR.revoque,
} as const;

export const PROFILS = { eleve: "Élève", encadreur: "Encadreur", admin: "Collaborateur" } as const;

// Libellés des actions du journal d'audit.
export const ACTIONS_JOURNAL: Record<string, string> = {
  connexion: "Connexion",
  echec_connexion: "Échec de connexion",
  echec_code_double_auth: "Code de double authentification faux",
  acces_refuse: "Accès refusé",
  fin_acces_atteinte: "Fin d'accès atteinte",
  collaborateur_invite: "Collaborateur invité",
  invitation_renvoyee: "Invitation renvoyée",
  invitation_acceptee: "Invitation acceptée",
  invitation_annulee: "Invitation annulée",
  droits_modifies: "Droits modifiés",
  droits_revus: "Droits revus",
  collaborateur_suspendu: "Collaborateur suspendu",
  collaborateur_reactive: "Collaborateur réactivé",
  collaborateur_revoque: "Collaborateur révoqué",
  double_auth_activee: "Double authentification activée",
  double_auth_reinitialisee: "Double authentification réinitialisée",
  referentiel_cree: "Référentiel : élément créé",
  referentiel_modifie: "Référentiel : élément modifié",
  referentiel_desactive: "Référentiel : élément désactivé",
  referentiel_reactive: "Référentiel : élément réactivé",
  codes_secours_regeneres: "Codes de secours régénérés",
  inscrit_suspendu: "Inscrit suspendu",
  inscrit_reactive: "Inscrit réactivé",
  inscription_eleve: "Inscription d'un élève",
  profil_eleve_modifie: "Profil d'élève modifié",
  pseudonyme_impose: "Pseudonyme imposé",
  mot_de_passe_change: "Mot de passe changé",
  mot_de_passe_reinitialise: "Mot de passe réinitialisé",
  semestre_cree: "Semestre créé",
  semestre_modifie: "Semestre modifié",
  bareme_modifie: "Barème modifié",
  etablissement_remplace: "Établissement proposé remplacé",
  export_demande: "Export demandé",
  export_telecharge: "Export téléchargé",
  super_admin_cree_en_ligne_de_commande: "Super-administrateur créé",
};

const formatDate = new Intl.DateTimeFormat("fr-FR", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});
const formatDateHeure = new Intl.DateTimeFormat("fr-FR", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "UTC",
});

// En UTC, l'heure du Togo : le rendu serveur et le navigateur affichent le même texte.
export const dateCourte = (iso: string | null | undefined) =>
  iso ? formatDate.format(new Date(iso)) : "—";
export const dateHeure = (iso: string | null | undefined) =>
  iso ? formatDateHeure.format(new Date(iso)) : "—";
