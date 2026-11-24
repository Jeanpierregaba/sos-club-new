// Aides d'affichage des clubs (specs 019 et 033) : statuts, axes et rattachement à un établissement.
import type {
  AxePublic,
  CarteEtablissement,
  ClubPublic,
  RegionScolaire,
  StatutClub,
} from "@/lib/api/client";
import { m } from "@/paraglide/messages.js";

// Sur la carte, un établissement sans club ne doit plus passer pour un club.
export const libelleSansClub = () => m.clubs_sans_club();

type Pastille = { readonly libelle: string; classe: string };

// Le libellé est lu à l'affichage, dans la langue de la page (spec 052).
const pastille = (libelle: () => string, classe: string): Pastille => ({
  get libelle() {
    return libelle();
  },
  classe,
});

// Statuts calculés par l'API (spec 033, ADR-0011).
export const STATUTS_CLUB: Record<StatutClub, Pastille> = {
  en_constitution: pastille(m.clubs_statut_en_constitution, "bg-sun/30 text-ink"),
  actif: pastille(m.clubs_statut_actif, "bg-primary/10 text-primary"),
  en_regularisation: pastille(m.clubs_statut_en_regularisation, "bg-sun/60 text-ink"),
  suspendu: pastille(m.clubs_statut_suspendu, "bg-logo-red/10 text-logo-red"),
};

// Le statut public d'un établissement sur la carte : une régularisation s'y montre « actif ».
export const STATUTS_CARTE: Record<CarteEtablissement["statut"], Pastille> = {
  reference: pastille(m.clubs_statut_reference, "bg-mist text-muted-foreground"),
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
