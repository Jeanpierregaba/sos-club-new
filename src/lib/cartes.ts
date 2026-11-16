import type { MaCarte } from "@/lib/api/client";

// Libellés des cartes numériques (spec 040), partagés par l'espace, la page publique et l'admin.

export const ROLES_CARTE: Record<MaCarte["role"], string> = {
  membre: "Membre",
  president: "Président du club",
  encadreur: "Encadreur",
};

export const TYPES_CARTE: Record<MaCarte["type"], string> = {
  membre: "Carte membre",
  encadreur: "Carte encadreur",
};

type Cause = NonNullable<MaCarte["cause"]>;

// Ce que voit le titulaire : la marche à suivre, jamais le détail d'un motif de fraude.
export const CAUSES_TITULAIRE: Record<Cause, string> = {
  compte_supprime: "Ce compte n'existe plus.",
  compte_suspendu: "Ton compte est suspendu : contacte l'équipe nationale des Clubs Santé.",
  suspendue_par_l_equipe:
    "Ta carte a été suspendue par l'équipe nationale : contacte-la pour en savoir plus.",
  non_verifie: "Ta carte sera valide quand l'équipe aura vérifié ton compte.",
  sans_rattachement:
    "Ta carte sera valide dès que tu seras rattaché à un Club Santé : rapproche-toi de ton établissement.",
};

// Ce que voit l'équipe dans la fiche d'un inscrit.
export const CAUSES_ADMIN: Record<Cause, string> = {
  compte_supprime: "Compte supprimé",
  compte_suspendu: "Compte suspendu",
  suspendue_par_l_equipe: "Suspendue par l'équipe",
  non_verifie: "Encadreur non vérifié",
  sans_rattachement: "Encadreur sans rattachement",
};
