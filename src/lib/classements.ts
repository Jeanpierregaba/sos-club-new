// Mise en forme des classements (spec 036). L'API calcule les rangs ; le site ne fait que les afficher.

import type { CategorieClassement, PeriodeClassement } from "@/lib/api/client";

export const CATEGORIES: { valeur: CategorieClassement; libelle: string }[] = [
  { valeur: "eleves", libelle: "Élèves" },
  { valeur: "encadreurs", libelle: "Encadreurs" },
  { valeur: "clubs", libelle: "Clubs" },
];

export const PERIODES: { valeur: PeriodeClassement; libelle: string }[] = [
  { valeur: "semestre", libelle: "Semestre en cours" },
  { valeur: "historique", libelle: "Total historique" },
];

export const estCategorie = (valeur: unknown): valeur is CategorieClassement =>
  valeur === "eleves" || valeur === "encadreurs" || valeur === "clubs";

export const estPeriode = (valeur: unknown): valeur is PeriodeClassement =>
  valeur === "semestre" || valeur === "historique";

/** Les points en français : espace des milliers, virgule décimale, jamais arrondis (« 2,5 », « 1 200 »). */
export function formaterPoints(points: number): string {
  return points
    .toLocaleString("fr-FR", { maximumFractionDigits: 1 })
    .replace(/[\u00a0\u202f]/g, " ");
}

/** « 1er », « 2e », « 10e ». */
export function formaterRang(rang: number): string {
  return rang === 1 ? "1er" : `${rang}e`;
}

/** Un rang personnel, ou « Pas encore classé » quand l'API n'en donne pas. */
export function rangOuNonClasse(rang: number | null | undefined): string {
  return rang ? formaterRang(rang) : "Pas encore classé";
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
  return `${ligne.club ?? "Sans club"} · ${ligne.dre}`;
}
