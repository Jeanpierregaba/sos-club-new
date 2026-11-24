// Mise en forme des classements (spec 036). L'API calcule les rangs ; le site ne fait que les afficher.

import type { CategorieClassement, PeriodeClassement } from "@/lib/api/client";
import { formatDeLaLangue, ordinal } from "@/lib/langues";
import { m } from "@/paraglide/messages.js";

export const CATEGORIES: { valeur: CategorieClassement; libelle: string }[] = [
  { valeur: "eleves", libelle: "Élèves" },
  { valeur: "encadreurs", libelle: "Encadreurs" },
  { valeur: "clubs", libelle: "Clubs" },
];

export const PERIODES: { valeur: PeriodeClassement; libelle: string }[] = [
  { valeur: "semestre", libelle: "Semestre en cours" },
  { valeur: "historique", libelle: "Total historique" },
];

// Les mêmes listes dans la langue de la page (spec 052) : pour les pages publiques.
const NOMS_CATEGORIES: Record<CategorieClassement, () => string> = {
  eleves: m.classement_eleves,
  encadreurs: m.classement_encadreurs,
  clubs: m.classement_clubs,
};
const NOMS_PERIODES: Record<PeriodeClassement, () => string> = {
  semestre: m.classement_semestre,
  historique: m.classement_historique,
};
export const categoriesTraduites = () =>
  CATEGORIES.map((c) => ({ ...c, libelle: NOMS_CATEGORIES[c.valeur]() }));
export const periodesTraduites = () =>
  PERIODES.map((p) => ({ ...p, libelle: NOMS_PERIODES[p.valeur]() }));

export const estCategorie = (valeur: unknown): valeur is CategorieClassement =>
  valeur === "eleves" || valeur === "encadreurs" || valeur === "clubs";

export const estPeriode = (valeur: unknown): valeur is PeriodeClassement =>
  valeur === "semestre" || valeur === "historique";

/** Les points dans la langue de la page, jamais arrondis : en français, espace des milliers et virgule décimale
 * (« 2,5 », « 1 200 »). */
export function formaterPoints(points: number): string {
  return points
    .toLocaleString(formatDeLaLangue(), { maximumFractionDigits: 1 })
    .replace(/[\u00a0\u202f]/g, " ");
}

/** « 1er », « 2e », « 10e » ; « 1st », « 2nd » ; « 1. », « 2. ». */
export function formaterRang(rang: number): string {
  return ordinal(rang);
}

/** Un rang personnel, ou « Pas encore classé » quand l'API n'en donne pas. */
export function rangOuNonClasse(rang: number | null | undefined): string {
  return rang ? formaterRang(rang) : m.classement_pas_classe();
}

/** Le nombre de pages d'un classement paginé. */
export function nombreDePages(total: number, parPage: number): number {
  return Math.max(1, Math.ceil(total / parPage));
}

type LignePublique =
  | { rang: number; nom: string; club: string | null; dre: string; points: number }
  | {
      rang: number;
      club_id: string;
      nom: string;
      etablissement: string;
      dre: string;
      points: number;
    };

/** Le sous-titre d'une ligne : le club et la DRE d'une personne, l'établissement et la DRE d'un club. */
export function sousTitre(ligne: LignePublique): string {
  if ("etablissement" in ligne) return `${ligne.etablissement} · ${ligne.dre}`;
  return `${ligne.club ?? m.classement_sans_club()} · ${ligne.dre}`;
}

// La règle d'égalité publiée (spec 037) : elle s'affiche avec le palmarès, comme le demande le cahier des charges.
export const regleExAequo = () => m.palmares_regle_ex_aequo();
