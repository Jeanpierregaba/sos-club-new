import { CHAMPION, type JoueurPrime } from "@/lib/genie-imhotep-resultats";

// Éditions du Championnat national Génie Imhotep, de la plus ancienne à la plus récente.
// Chaque édition a sa page dans le Hall of Fame (/genie-imhotep/hall-of-fame/<id>) et dans le Palmarès
// (/genie-imhotep/palmares/<id>). Une édition terminée a ses résultats (genie-imhotep-resultats.ts) ;
// une édition à venir a une date de coup d'envoi, vers laquelle compte le compte à rebours.

export type Edition = {
  id: string;
  numero: number;
  statut: "terminee" | "a-venir";
  // Coup d'envoi, en UTC (ISO 8601). Seulement pour une édition à venir.
  debut?: string;
  // Le champion national, une fois l'édition terminée.
  champion?: string;
  // Les joueurs primés de l'édition (page Palmarès). Vide tant qu'AIMES-AFRIQUE n'a pas transmis la liste.
  joueursPrimes?: JoueurPrime[];
};

export const editions: Edition[] = [
  { id: "2025-2026", numero: 1, statut: "terminee", champion: CHAMPION, joueursPrimes: [] },
  { id: "2026-2027", numero: 2, statut: "a-venir", debut: "2027-03-01T00:00:00Z" },
];

export const trouverEdition = (id: string) => editions.find((e) => e.id === id);

export const ordinal = (n: number) => (n === 1 ? "1re" : `${n}e`);

export const libelleSaison = (id: string) => id.replace("-", " – ");
