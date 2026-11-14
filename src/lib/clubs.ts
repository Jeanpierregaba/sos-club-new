// Aides d'affichage des clubs (specs 019 et 033) : statuts, axes et rattachement à un établissement.
import type {
  AxePublic,
  CarteEtablissement,
  ClubPublic,
  RegionScolaire,
  StatutClub,
} from "@/lib/api/client";

// Sur la carte, un établissement sans club ne doit plus passer pour un club.
export const LIBELLE_SANS_CLUB = "Aucun club enregistré pour cet établissement";

type Pastille = { libelle: string; classe: string };

// Statuts calculés par l'API (spec 033, ADR-0011).
export const STATUTS_CLUB: Record<StatutClub, Pastille> = {
  en_constitution: { libelle: "En constitution", classe: "bg-sun/30 text-ink" },
  actif: { libelle: "Club actif", classe: "bg-primary/10 text-primary" },
  en_regularisation: { libelle: "En régularisation", classe: "bg-sun/60 text-ink" },
  suspendu: { libelle: "Suspendu", classe: "bg-logo-red/10 text-logo-red" },
};

// Le statut public d'un établissement sur la carte : une régularisation s'y montre « actif ».
export const STATUTS_CARTE: Record<CarteEtablissement["statut"], Pastille> = {
  reference: { libelle: "Référencé", classe: "bg-mist text-muted-foreground" },
  en_constitution: STATUTS_CLUB.en_constitution,
  actif: STATUTS_CLUB.actif,
  suspendu: STATUTS_CLUB.suspendu,
};

// Les seuils d'activation (spec 033) : l'API les renvoie aussi, ces valeurs servent aux textes.
export const SEUIL_ENCADREURS = 3;
export const SEUIL_ELEVES = 21;

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

// Les 5 régions du Togo, du sud au nord (spec 033) : le niveau au-dessus des DRE.
export const REGIONS_SCOLAIRES: { code: RegionScolaire; nom: string }[] = [
  { code: "maritime", nom: "Maritime" },
  { code: "plateaux", nom: "Plateaux" },
  { code: "centrale", nom: "Centrale" },
  { code: "kara", nom: "Kara" },
  { code: "savanes", nom: "Savanes" },
];

export const nomRegion = (code: RegionScolaire) =>
  REGIONS_SCOLAIRES.find((r) => r.code === code)?.nom ?? code;
