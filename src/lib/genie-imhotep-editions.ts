// Éditions du Championnat national Génie Imhotep, de la plus ancienne à la plus récente.
// Une édition terminée a ses résultats (genie-imhotep-resultats.ts) ; une édition à venir a une date de
// coup d'envoi, vers laquelle compte le compte à rebours du Hall of Fame.
// Pour ajouter une saison : une ligne ici ; ses résultats rejoindront le Hall of Fame et le Palmarès.

export type Edition = {
  id: string;
  numero: number;
  statut: "terminee" | "a-venir";
  // Coup d'envoi, en UTC (ISO 8601). Seulement pour une édition à venir.
  debut?: string;
};

export const editions: Edition[] = [
  { id: "2025-2026", numero: 1, statut: "terminee" },
  // DATE PROVISOIRE (2026-11-05) : à remplacer par la date officielle du coup d'envoi.
  { id: "2026-2027", numero: 2, statut: "a-venir", debut: "2027-02-01T08:00:00Z" },
];

// L'édition affichée par défaut : la dernière terminée.
export const editionParDefaut = editions.filter((e) => e.statut === "terminee").at(-1)!;

export const editionDe = (id: string | undefined) =>
  editions.find((e) => e.id === id) ?? editionParDefaut;

export const ordinal = (n: number) => (n === 1 ? "1re" : `${n}e`);
