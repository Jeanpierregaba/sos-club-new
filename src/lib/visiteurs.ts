import type { Region } from "@/lib/api/client";

// Les régions proposées au visiteur (spec 030).
export const REGIONS: { valeur: Region; libelle: string }[] = [
  { valeur: "maritime", libelle: "Région Maritime" },
  { valeur: "plateaux", libelle: "Région des Plateaux" },
  { valeur: "centrale", libelle: "Région Centrale" },
  { valeur: "kara", libelle: "Région de la Kara" },
  { valeur: "savanes", libelle: "Région des Savanes" },
  { valeur: "hors_togo", libelle: "Hors du Togo" },
];

export const libelleRegion = (region: Region | null) =>
  REGIONS.find((r) => r.valeur === region)?.libelle ?? "Non précisée";
