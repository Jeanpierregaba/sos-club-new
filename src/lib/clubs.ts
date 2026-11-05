// Aides d'affichage des clubs (spec 019) : états, axes et rattachement à un établissement.
import type { AxePublic, ClubPublic, EtatClub } from "@/lib/api/client";

// Sur la carte, un établissement sans club ne doit plus passer pour un club.
export const LIBELLE_SANS_CLUB = "Aucun club enregistré pour cet établissement";

export const ETATS_CLUB: Record<EtatClub, { libelle: string; classe: string }> = {
  en_attente: { libelle: "En attente de vérification", classe: "bg-sun/30 text-ink" },
  actif: { libelle: "Club actif", classe: "bg-primary/10 text-primary" },
  refuse: { libelle: "Demande refusée", classe: "bg-logo-red/10 text-logo-red" },
};

// Un seul club actif par établissement : l'index suffit à savoir si un établissement en a un.
export function clubsParEtablissement(clubs: ClubPublic[]): Map<string, ClubPublic> {
  return new Map(clubs.map((club) => [club.etablissement.id, club]));
}

export function libellesDesAxes(axes: AxePublic[]): Map<string, string> {
  return new Map(axes.map((axe) => [axe.code, axe.libelle]));
}

// « sante-environnement » devient son libellé du référentiel ; un code inconnu reste lisible tel quel.
export function libelleAxes(codes: string[], libelles: Map<string, string>): string {
  return codes.map((code) => libelles.get(code) ?? code).join(" · ");
}
